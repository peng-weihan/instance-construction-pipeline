"""Build a public-only offline cloud context, then exercise exact pilot judging."""
from pathlib import Path
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import traceback
import uuid

from build_packages import ROOT, SOURCE, dump, inventory


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def copy_from(cid, remote, dest, optional=False):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(['docker', 'cp', '-L', cid + ':' + remote, str(dest)], capture_output=True)
    if p.returncode and not optional:
        raise RuntimeError('missing public runtime asset: ' + remote)
    return p.returncode == 0


def make_snapshot(out, name, image, workdir, solution=None):
    snap = out / 'controls' / name / 'snapshot'
    target = snap / (workdir + '/submission').lstrip('/')
    target.parent.mkdir(parents=True)
    cmd = ['docker', 'create', '--network', 'none', '--user', '0:0', '--entrypoint', '/bin/sh']
    if solution:
        cmd += ['--mount', f'type=bind,source={solution},target=/solution,readonly']
    cmd += [image, '-c', '/bin/sh /solution/solve.sh' if solution else 'true']
    cid = subprocess.check_output(cmd, text=True).strip()
    try:
        if solution:
            with (out / 'controls' / name / 'solution.log').open('wb') as f:
                run(['docker', 'start', '-a', cid], stdout=f, stderr=subprocess.STDOUT)
            code = subprocess.check_output(['docker', 'inspect', cid, '--format', '{{.State.ExitCode}}'], text=True).strip()
            assert code == '0', 'reference entry failed'
        copy_from(cid, workdir + '/submission', target)
    finally:
        subprocess.run(['docker', 'rm', '-f', cid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return snap


def prepare(key):
    out = ROOT / key
    status = json.loads((out / 'prepare-status.json').read_text())
    if status['phase'] != 'images_built':
        raise RuntimeError('images not ready')
    status.update(phase='preparing_cloud_context')
    dump(out / 'prepare-status.json', status)
    try:
        import tomllib
        source = out / 'source-task'
        cfg = tomllib.loads((source / 'task.toml').read_text())
        work = cfg['environment']['workdir']
        images = json.loads((out / 'images.json').read_text())
        task = out / 'task'
        shutil.copytree(source, task, ignore=shutil.ignore_patterns('environment', 'verifier'))
        context = task / 'environment'
        context.mkdir()
        assets = out / 'public-runtime'
        assets.mkdir()
        cid = subprocess.check_output(['docker', 'create', images['agent']['image_id']], text=True).strip()
        try:
            copy_from(cid, work, assets / work.lstrip('/'))
            # Runtime/library installation paths are exactly those of the authored image.
            for path in ['/usr/local/bin/python3.12', '/usr/local/lib/python3.12',
                         '/usr/local/lib/libpython3.12.so.1.0']:
                copy_from(cid, path, assets / path.lstrip('/'))
            has_venv = copy_from(cid, '/opt/venv', assets / 'opt/venv', optional=True)
        finally:
            subprocess.run(['docker', 'rm', cid], check=True, stdout=subprocess.DEVNULL)
        # Fail closed on accidental inclusion of an author answer or account file.
        forbidden = {'auth.json', 'static-egress.json', 'connection.json', 'AUTHOR_RESULT.json',
                     'reference.patch', 'restore.patch', 'reference.tar.gz'}
        assert not any(p.name in forbidden for p in assets.rglob('*'))
        archive = context / 'public-runtime.tar.gz'
        with tarfile.open(archive, 'w:gz', compresslevel=1) as tar:
            for p in assets.iterdir():
                tar.add(p, arcname=p.name)
        shutil.copyfile(ROOT.parent / 'remaining-three-001/science-pilot/task/environment/aliyun.json',
                        context / 'aliyun.json')
        cloud = json.loads((context / 'aliyun.json').read_text())
        bootstrap = '''set -eu
CTX=/opt/tbsci-bootstrap
tar -xzf "$CTX/public-runtime.tar.gz" -C /
rm "$CTX/public-runtime.tar.gz"
ln -sf python3.12 /usr/local/bin/python3
ln -sf python3.12 /usr/local/bin/python
ln -sf libpython3.12.so.1.0 /usr/local/lib/libpython3.12.so
/sbin/ldconfig
mkdir -p /home/workspace
chown -R agent:agent WORKDIR
chmod 755 /home/workspace WORKDIR
ln -sf /opt/codex-static/codex-path/rg /usr/local/bin/rg
'''.replace('WORKDIR', work)
        # Each terminal inherits the interpreter selected by the author image.
        if has_venv:
            bootstrap += 'printf \'export PATH=/opt/venv/bin:$PATH\\n\' >> /home/agent/.bashrc\n'
        if key.startswith('04_'):
            bootstrap += 'chown -R agent:agent /opt/venv\n'
        if key.startswith('14_'):
            bootstrap += 'command -v cc\ncc --version\ncommand -v make\ncommand -v patch\n'
        bootstrap += f'cd {work}\n/usr/local/bin/python --version\n'
        (context / 'bootstrap.sh').write_text(bootstrap)
        # Keep the unchanged author image definition as provenance, not as a cloud builder.
        (context / 'Dockerfile').write_text('FROM ' + images['agent']['image_id'] + '\n')
        profile = {'workdir': work, 'submission_root': work + '/submission',
                   'artifacts': [work + '/submission'], 'selection': 'valid_then_score',
                   'score_direction': 'maximize', 'cooldown_sec': 120, 'grading_workers': 1,
                   'verifier_timeout_sec': cfg['verifier']['timeout_sec'],
                   'judge_memory_mb': cfg['verifier']['environment']['memory_mb']}
        dump(task / 'pipeline-profile.json', profile)
        framework = ROOT / 'framework'
        sys.path[:0] = [str(framework), str(framework / 'sdk')]
        from harbor.models.task.config import TaskConfig
        t = TaskConfig.model_validate_toml((source / 'task.toml').read_text())
        t.environment.cpus = cloud['cpus']
        t.environment.memory_mb = cloud['memory_mb']
        t.environment.storage_mb = max(t.environment.storage_mb or 0, 15360)
        t.agent.user = 'agent'
        t.agent.timeout_sec = 28800
        (task / 'task.toml').write_text(t.model_dump_toml())
        instruction = (source / 'instruction.md').read_text()
        instruction += ('\n\n运行说明：工作目录为 ' + work + '。仅 submission/ 文件参与评分。'
            '使用 python 命令；Python依赖已离线安装。每600秒自动提交快照，也可执行 sforge-submit 主动请求反馈。'
            '本次学习预算为完整6小时，取所有有效提交最高分；完成一个阶段后继续检查边界和改进。'
            '禁止访问账号凭据、网络设置或评分器私有文件。\n')
        if has_venv:
            instruction += '任务 Python 为 /opt/venv/bin/python；终端需要时执行 export PATH=/opt/venv/bin:$PATH。\n'
        (task / 'instruction.md').write_text(instruction)
        dump(out / 'cloud-preparation.json', {'public_runtime_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'public_runtime_bytes': archive.stat().st_size, 'workdir': work,
            'original_source_task_unchanged': inventory(source) == json.loads((out / 'source-freeze.json').read_text())['file_hashes'],
            'cloud_resources': cloud, 'author_score_unchanged': True, 'formal_acceptance': False})
        status.update(phase='running_score_controls')
        dump(out / 'prepare-status.json', status)
        controls = out / 'controls'
        controls.mkdir(exist_ok=True)
        starter = make_snapshot(out, 'starter', images['agent']['image_id'], work)
        reference = make_snapshot(out, 'reference', images['agent']['image_id'], work, source / 'solution')
        empty = controls / 'empty/snapshot'
        (empty / profile['submission_root'].lstrip('/')).mkdir(parents=True)
        partial = controls / 'partial/snapshot'
        submission = partial / profile['submission_root'].lstrip('/')
        shutil.copytree(reference / profile['submission_root'].lstrip('/'), submission)
        if key.startswith('01_'):
            shutil.rmtree(submission)
            shutil.copytree(SOURCE / key / 'controls/no_auth_override', submission)
        elif key.startswith('02_'):
            shutil.rmtree(submission)
            shutil.copytree(SOURCE / key / 'controls/unstable_pending_key', submission)
        elif key.startswith('04_'):
            shutil.rmtree(submission)
            shutil.copytree(SOURCE / key / 'controls/no_item_cache', submission)
        elif key.startswith('09_'):
            shutil.rmtree(submission)
            shutil.copytree(source / 'verifier/private/controls/no_watch', submission)
        elif key.startswith('14_'):
            shutil.rmtree(submission)
            shutil.copytree(starter / profile['submission_root'].lstrip('/'), submission)
            with (source / 'verifier/private/controls/edit_only.patch').open('rb') as f:
                run(['patch', '-p1'], cwd=submission, stdin=f, stdout=subprocess.DEVNULL)
        from edgebench_harbor.package_scorer import DockerScorer
        scorer = DockerScorer(task, images['verifier']['image_id'], profile['verifier_timeout_sec'])

        async def grade_all():
            results = {}
            dump(out / 'scorer-controls.json', {'passed': False, 'status': 'running', 'results': results})
            for name, snapshot in [('reference', reference), ('starter', starter), ('empty', empty), ('partial', partial)]:
                report, seconds = await scorer.grade(snapshot, controls / name / 'grading')
                results[name] = {'score': report['score'], 'valid': report['valid'], 'seconds': seconds,
                    'failed_checks': report['failed_checks'], 'candidate_hashes': inventory(snapshot)}
                dump(out / 'scorer-controls.json', {'passed': False, 'status': 'running', 'results': results})
                print(key, name, report['score'], seconds, flush=True)
            assert results['reference']['score'] == 1.0, 'reference failed to reach declared upper endpoint'
            assert results['empty']['score'] == 0.0, 'empty unexpectedly scores'
            assert 0 < results['partial']['score'] < 1, 'actual partial control not partial'
            dump(out / 'scorer-controls.json', {'passed': True, 'status': 'completed',
                'results': results, 'image_id': images['verifier']['image_id'],
                'task_hashes': inventory(task), 'formal_native_harbor_controls': False,
                'score_entry': 'unmodified authored /tests/test.sh; exact periodic scorer',
                'model_runs': 0, 'formal_acceptance': False})

        asyncio.run(grade_all())
        status.update(phase='ready_for_cloud_admission')
        dump(out / 'prepare-status.json', status)
    except Exception as exc:
        status.update(phase='preparation_failed', error=repr(exc), traceback=traceback.format_exc())
        dump(out / 'prepare-status.json', status)
        raise


if __name__ == '__main__':
    prepare(sys.argv[1])
