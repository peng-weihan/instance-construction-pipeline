"""Freeze four authored candidates and prepare real, separately judged pilots."""
from pathlib import Path
import asyncio
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
import traceback

BASE = Path('/ws/users/raymone/edgebench')
ROOT = BASE / 'swe-new-rollouts-004-20261015-r1'
SOURCE = BASE / 'swe-route-authoring-010-20261015-r4/jobs'
OLD = BASE / 'swe-rollouts-005-20261015-r5'
TASKS = ['33_sqlglot_system_reconstruction', '35_click_multimodule_reconstruction',
         '36_yq_rust_behavioral_port', '37_jinja_template_engine']


def dump(path, obj):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def inventory(root):
    result = {}
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink():
            raise ValueError('Unreviewed task symlink: ' + str(p))
        if p.is_file():
            result[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def cp(source, dest):
    subprocess.run(['cp', '-a', '--reflink=auto', str(source), str(dest)], check=True)


def docker_copy(cid, remote, dest, optional=False):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(['docker', 'cp', '-L', cid + ':' + remote, str(dest)], capture_output=True)
    if proc.returncode and not optional:
        raise RuntimeError('Public runtime file missing: ' + remote)
    return proc.returncode == 0


def deploy():
    ROOT.mkdir(exist_ok=False)
    (ROOT / 'scripts').mkdir()
    (ROOT / 'activity').mkdir()
    cp(OLD / 'framework', ROOT / 'framework')
    f = ROOT / 'framework'
    # The authored Jinja entry is Bash; yq supplies its trusted Python in /usr/bin.
    # These are entry selection options only, never edits to any task grader.
    changes = {
        'edgebench_harbor/account_model_slots.py': [
            ("ROOT = Path('/ws/users/raymone/edgebench/swe-rollouts-005-20261015-r5')",
             "ROOT = Path(__file__).resolve().parents[2]")],
        'edgebench_harbor/package_scorer.py': [
            ("'--entrypoint', '/bin/sh', self.image, '/tests/test.sh'",
             "'--entrypoint', self.profile.get('judge_shell', '/bin/sh'), self.image, '/tests/test.sh'")],
        'edgebench_harbor/native_controls_runtime.py': [
            ("'/usr/local/bin/python3 -I -c ' + shlex.quote(code)",
             "shlex.quote(profile.get('native_control_python', '/usr/local/bin/python3')) + ' -I -c ' + shlex.quote(code)"),
            ("self.environment.exec('/bin/sh /tests/test.sh'",
             "self.environment.exec(shlex.quote(profile.get('judge_shell', '/bin/sh')) + ' /tests/test.sh'")],
        'edgebench_harbor/unleased_official_cloud_environment.py': [
            ("'PIP_NO_INDEX','PIP_DISABLE_PIP_VERSION_CHECK'}",
             "'PIP_NO_INDEX','PIP_DISABLE_PIP_VERSION_CHECK','PATH','RUSTUP_HOME','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS'}"),
            ("PATH='/opt/codex-static/bin:/opt/codex-static/codex-path:/opt/rust/bin:/opt/venv/bin:/usr/local/bin:/usr/bin:/bin'",
             "PATH='/opt/codex-static/bin:/opt/codex-static/codex-path:' + persistent.get('PATH','/opt/rust/bin:/opt/venv/bin:/usr/local/bin:/usr/bin:/bin')")],
    }
    patch_record = []
    for rel, replacements in changes.items():
        p = f / rel
        before = p.read_text()
        after = before
        for a, b in replacements:
            assert after.count(a) == 1, (rel, a)
            after = after.replace(a, b)
        compile(after, str(p), 'exec')
        p.write_text(after)
        patch_record.append({'file': rel, 'before': hashlib.sha256(before.encode()).hexdigest(),
                             'after': hashlib.sha256(after.encode()).hexdigest()})
    previous = json.loads((f / 'framework-version.json').read_text())
    hashes = {p.relative_to(f).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in f.rglob('*') if p.is_file() and '__pycache__' not in p.parts
              and p.name != 'framework-version.json'}
    previous.update(runtime_file_hashes=hashes,
                    runtime_tree_sha256=hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                    derived_from=str(OLD / 'framework'), new_entry_options=patch_record,
                    evidence_scope='Controls and actual cloud admission required anew for each task')
    dump(f / 'framework-version.json', previous)
    shutil.copyfile(__file__, ROOT / 'scripts/build_packages.py')
    for n in ['launch_run.py', 'roll_worker.py', 'run_native_controls.py']:
        shutil.copyfile(OLD / 'scripts' / n, ROOT / 'scripts' / n)
    # Require the actual partial control too, before inference.
    for n in ['launch_run.py', 'roll_worker.py']:
        p = ROOT / 'scripts' / n
        s = p.read_text().replace("['oracle', 'nop']", "['oracle', 'nop', 'partial']")
        p.write_text(s)
    dump(ROOT / 'PREPARATION.json', {
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source': str(SOURCE), 'tasks': TASKS, 'model': 'gpt-6.1-sol',
        'budget_seconds': 21600, 'interval_seconds': 600,
        'user_authorized_full_score_stop': True, 'difficulty_other_early_stop': False,
        'author_sources_and_old_rollouts_preserved': True,
        'purpose': 'One exploratory difficulty rollout per new-material candidate, not final acceptance'})
    for key in TASKS:
        (ROOT / key).mkdir()
        with (ROOT / key / 'preparation.log').open('xb') as log:
            p = subprocess.Popen([sys.executable, '-u', str(ROOT / 'scripts/build_packages.py'), key],
                                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                 start_new_session=True)
        dump(ROOT / key / 'preparation-launch.json', {
            'pid': p.pid, 'start_ticks': Path('/proc', str(p.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]})
    print(json.dumps({'root': str(ROOT), 'preparation_workers_started': len(TASKS)}), flush=True)


def prepare(key):
    assert key in TASKS
    out = ROOT / key
    state = {'task': key, 'phase': 'freezing', 'model_requests': 0}
    save = lambda: dump(out / 'prepare-status.json', state)
    save()
    try:
        source = SOURCE / key / 'task'
        hashes = inventory(source)
        cp(source, out / 'source-task')
        assert hashes == inventory(source) == inventory(out / 'source-task')
        dump(out / 'source-freeze.json', {'source': str(source), 'file_hashes': hashes, 'source_preserved': True})
        source = out / 'source-task'
        cfg = tomllib.loads((source / 'task.toml').read_text())
        work = cfg['environment']['workdir']
        images = {}
        for side, section in [('agent', cfg['environment']), ('verifier', cfg['verifier']['environment'])]:
            record = json.loads(subprocess.check_output(['docker', 'image', 'inspect', section['docker_image']], text=True))[0]
            images[side] = {'image_id': record['Id'], 'authored_reference': section['docker_image'],
                            'image_config': {k: record['Config'].get(k) for k in ['Env', 'WorkingDir', 'User']}}
        dump(out / 'images.json', images)
        state.update(phase='preparing_public_cloud_context'); save()
        task = out / 'task'
        shutil.copytree(source, task, ignore=shutil.ignore_patterns('environment', 'verifier'))
        context = task / 'environment'; context.mkdir()
        assets = out / 'public-runtime'; assets.mkdir()
        cid = subprocess.check_output(['docker', 'create', '--network', 'none', images['agent']['image_id']], text=True).strip()
        try:
            docker_copy(cid, work, assets / work.lstrip('/'))
            if key.startswith('36_'):
                for path in ['/usr/local/cargo', '/usr/local/rustup', '/opt/deps', '/opt/python',
                             '/usr/bin/python3.11', '/usr/lib/python3.11', '/usr/bin/jq']:
                    docker_copy(cid, path, assets / path.lstrip('/'))
                # Keep additional distribution libraries isolated from the cloud's libc.
                for pattern in ['libjq.so.1', 'libonig.so.5', 'libssl.so.3', 'libcrypto.so.3',
                                'libffi.so.8', 'libexpat.so.1', 'libz.so.1', 'libcrypt.so.1']:
                    docker_copy(cid, '/usr/lib/x86_64-linux-gnu/' + pattern,
                                assets / 'opt/edgebench-yq-libs' / pattern)
            else:
                for path in ['/usr/local/bin/python3.12', '/usr/local/lib/python3.12',
                             '/usr/local/lib/libpython3.12.so.1.0']:
                    docker_copy(cid, path, assets / path.lstrip('/'))
                if key.startswith('35_'):
                    docker_copy(cid, '/opt/dev', assets / 'opt/dev')
        finally:
            subprocess.run(['docker', 'rm', '-f', cid], check=True, stdout=subprocess.DEVNULL)
        forbidden = {'auth.json', 'static-egress.json', 'connection.json', 'AUTHOR_RESULT.json',
                     'reference.patch', 'restore.patch', 'reference.tar.gz'}
        bad = [str(p.relative_to(assets)) for p in assets.rglob('*') if p.name in forbidden]
        assert not bad, bad
        env = {k: v for item in images['agent']['image_config'].get('Env', [])
               for k, v in [item.split('=', 1)] if k in {
                   'PATH', 'PYTHONPATH', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS',
                   'CARGO_HOME', 'RUSTUP_HOME', 'CARGO_NET_OFFLINE', 'CARGO_BUILD_JOBS'}}
        env.update(PYTHONDONTWRITEBYTECODE='1', PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1')
        # SDK utilities remain available; task-specific interpreters retain image precedence.
        env['PATH'] = env.get('PATH', '/usr/local/bin:/usr/bin:/bin') + ':/opt/codex-static/codex-path'
        dump(context / 'runtime-env.json', env)
        audit_source = BASE / 'remaining-three-001/science-pilot/task/environment/native-audit'
        shutil.copytree(audit_source, context / 'native-audit')
        archive = context / 'public-runtime.tar.gz'
        with tarfile.open(archive, 'w:gz', compresslevel=1, dereference=False) as tar:
            for p in assets.iterdir(): tar.add(p, arcname=p.name)
        cloud = json.loads((BASE / 'remaining-three-001/science-pilot/task/environment/aliyun.json').read_text())
        dump(context / 'aliyun.json', cloud)
        bootstrap = '''set -eu
CTX=/opt/tbsci-bootstrap
tar -xzf "$CTX/public-runtime.tar.gz" -C /
rm "$CTX/public-runtime.tar.gz"
mkdir -p /home/workspace
chown -R agent:agent WORKDIR
chmod 755 /home/workspace WORKDIR
ln -sf /opt/codex-static/codex-path/rg /usr/local/bin/rg
mkdir -p /opt/edgebench-native-audit
cp -a "$CTX/native-audit/." /opt/edgebench-native-audit/
chmod -R a+rX,go-w /opt/edgebench-native-audit
chmod 755 /opt/edgebench-native-audit/bin/*
'''.replace('WORKDIR', work)
        if key.startswith('36_'):
            bootstrap += '''ln -sf /usr/bin/python3.11 /opt/python/bin/python3
ln -sf python3 /opt/python/bin/python
ln -sf /usr/bin/python3.11 /usr/local/bin/python3
ln -sf /usr/bin/python3.11 /usr/local/bin/python
cat > /usr/local/bin/jq <<'JQ'
#!/bin/sh
LD_LIBRARY_PATH=/opt/edgebench-yq-libs exec /usr/bin/jq "$@"
JQ
chmod 755 /usr/local/bin/jq
chown -R agent:agent /usr/local/cargo
export RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo CARGO_NET_OFFLINE=true CARGO_BUILD_JOBS=2
export PATH=/opt/python/bin:/usr/local/cargo/bin:/usr/local/bin:/usr/bin:/bin
python3 --version
python3 -c 'import yaml,ruamel.yaml'
cargo --version
rustc --version
jq --version
cd WORKDIR/submission
su -s /bin/sh agent -c 'RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo CARGO_NET_OFFLINE=true CARGO_BUILD_JOBS=2 /usr/local/cargo/bin/cargo check --offline --locked -j2'
rm -rf WORKDIR/submission/target
'''.replace('WORKDIR', work)
        else:
            bootstrap += '''ln -sf python3.12 /usr/local/bin/python3
ln -sf python3.12 /usr/local/bin/python
ln -sf libpython3.12.so.1.0 /usr/local/lib/libpython3.12.so
/sbin/ldconfig
/usr/local/bin/python3 --version
'''
            if key.startswith('33_'):
                bootstrap += "/usr/local/bin/python3 -c 'import sqlparse,pglast,duckdb,lark; import importlib.util; assert importlib.util.find_spec(\"sqlglot\") is None'\n"
            elif key.startswith('35_'):
                bootstrap += "/opt/dev/bin/python3 -c 'import pytest,typing_extensions'\n"
            elif key.startswith('37_'):
                bootstrap += "/usr/local/bin/python3 -c 'import importlib.util; assert importlib.util.find_spec(\"jinja2\") is None; import minijinja'\n"
        (context / 'bootstrap.sh').write_text(bootstrap)
        (context / 'Dockerfile').write_text('FROM ' + images['agent']['image_id'] + '\n')
        profile = {'workdir': work, 'submission_root': work + '/submission', 'artifacts': [work + '/submission'],
                   'selection': 'valid_then_score', 'score_direction': 'maximize', 'cooldown_sec': 120,
                   'grading_workers': 1, 'verifier_timeout_sec': cfg['verifier']['timeout_sec'],
                   'judge_memory_mb': cfg['verifier']['environment']['memory_mb'],
                   'judge_cpus': cfg['verifier']['environment']['cpus'], 'judge_writable_root': True,
                   'judge_shell': '/bin/bash' if key.startswith('37_') else '/bin/sh',
                   'native_control_python': '/usr/bin/python3' if key.startswith('36_') else '/usr/local/bin/python3'}
        dump(task / 'pipeline-profile.json', profile)
        f = ROOT / 'framework'
        sys.path[:0] = [str(f), str(f / 'sdk')]
        from harbor.models.task.config import TaskConfig, ArtifactConfig
        t = TaskConfig.model_validate_toml((source / 'task.toml').read_text())
        t.environment.cpus = cloud['cpus']; t.environment.memory_mb = cloud['memory_mb']
        t.environment.storage_mb = max(t.environment.storage_mb or 0, 15360)
        t.artifacts = [ArtifactConfig(source=work + '/submission')]
        t.agent.user = 'agent'; t.agent.timeout_sec = 28800
        (task / 'task.toml').write_text(t.model_dump_toml())
        extra = ('\n\n运行说明：工作目录为 ' + work + '，仅 submission/ 文件参与评分。'
                 '公开依赖已离线安装；每600秒自动提交快照，也可执行 sforge-submit 请求评分反馈。'
                 '本次学习预算最多6小时，最终取有效提交的最高分。继续完成尚未实现的能力与边界行为。'
                 '禁止访问账号凭据、网络设置或评分器私有文件。\n')
        if key.startswith('35_'): extra += '任务 Python 为 /opt/dev/bin/python；可执行 export PATH=/opt/dev/bin:$PATH。\n'
        if key.startswith('36_'): extra += 'Rust 使用 /usr/local/cargo/bin；CARGO_HOME=/usr/local/cargo，RUSTUP_HOME=/usr/local/rustup。Python 为 /opt/python/bin/python。\n'
        (task / 'instruction.md').write_text((source / 'instruction.md').read_text() + extra)
        dump(out / 'cloud-preparation.json', {
            'public_runtime_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'public_runtime_bytes': archive.stat().st_size, 'workdir': work, 'cloud_resources': cloud,
            'author_score_unchanged': True, 'author_private_material_not_uploaded': True,
            'source_task_hashes': hashes, 'formal_acceptance': False})
        controls = out / 'controls'; controls.mkdir()
        starter = controls / 'starter/snapshot'
        target = starter / profile['submission_root'].lstrip('/')
        target.parent.mkdir(parents=True)
        shutil.copytree(assets / profile['submission_root'].lstrip('/'), target)
        reference = controls / 'reference/snapshot'
        target = reference / profile['submission_root'].lstrip('/')
        shutil.copytree(starter / profile['submission_root'].lstrip('/'), target)
        refname = 'gold' if key.startswith('35_') else 'reference' if key.startswith('36_') else 'oracle'
        shutil.copytree(source / 'solution' / refname, target, dirs_exist_ok=True)
        empty = controls / 'empty/snapshot'
        (empty / profile['submission_root'].lstrip('/')).mkdir(parents=True)
        partial_sources = {
            TASKS[0]: SOURCE / TASKS[0] / 'authoring/controls/partial_frontend',
            TASKS[1]: SOURCE / TASKS[1] / 'controls/partial-input/submission',
            TASKS[2]: SOURCE / TASKS[2] / 'work/partials/no-presentation',
            TASKS[3]: SOURCE / TASKS[3] / 'controls/minijinja',
        }
        partial = controls / 'partial/snapshot'
        shutil.copytree(partial_sources[key], partial / profile['submission_root'].lstrip('/'),
                        ignore=shutil.ignore_patterns('target', '__pycache__'))
        state.update(phase='running_periodic_score_controls'); save()
        from edgebench_harbor.package_scorer import DockerScorer
        scorer = DockerScorer(task, images['verifier']['image_id'], profile['verifier_timeout_sec'])

        async def grade_all():
            results = {}
            for name, snap in [('reference', reference), ('starter', starter), ('empty', empty), ('partial', partial)]:
                report, seconds = await scorer.grade(snap, controls / name / 'grading')
                results[name] = {'score': report['score'], 'valid': report['valid'], 'seconds': seconds,
                                 'failed_checks': report['failed_checks'], 'candidate_hashes': inventory(snap)}
                dump(out / 'scorer-controls.json', {'passed': False, 'status': 'running', 'results': results})
                print(key, name, report['score'], seconds, flush=True)
            assert results['reference']['score'] == 1.0
            assert results['empty']['score'] == 0.0
            assert 0 < results['partial']['score'] < 1
            dump(out / 'scorer-controls.json', {'passed': True, 'status': 'completed', 'results': results,
                'image_id': images['verifier']['image_id'], 'task_hashes': inventory(task),
                'score_entry': 'Unchanged authored /tests/test.sh in immutable private judge',
                'model_requests': 0, 'formal_acceptance': False})
        asyncio.run(grade_all())
        state.update(phase='running_native_controls'); save()
        with (out / 'native-controls-console.log').open('wb') as log:
            subprocess.run([sys.executable, '-u', str(ROOT / 'scripts/run_native_controls.py'), key],
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=7200)
        state.update(phase='ready_for_cloud_admission'); save()
    except Exception as exc:
        state.update(phase='preparation_failed', error=repr(exc), traceback=traceback.format_exc()); save()
        raise


if __name__ == '__main__':
    deploy() if sys.argv[1:] == ['--deploy'] else prepare(sys.argv[1])
