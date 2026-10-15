"""Freeze and exercise five authored tasks; no teacher starts without actual controls."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shutil
import subprocess
import sys

BASE=Path('/ws/users/raymone/edgebench')
ROOT=BASE/'swe-rollouts-005-20261015-r5'
SOURCE=BASE/'swe-authoring-006-20261015-r2/jobs'
OLD=BASE/'swe-rollouts-005-20261015-r1'
FIXED=BASE/'swe-rollouts-003-20261015-r4'
KEYS=['18_polars_streaming','19_ruff_project_analysis','20_libcst_project_migration','21_coverage_context_merge','22_sphinx_incremental_build']
AUDIT=BASE/'remaining-three-001/science-pilot/task/environment/native-audit'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def setup():
    ROOT.mkdir(exist_ok=False)
    (ROOT/'scripts').mkdir();(ROOT/'activity').mkdir(mode=0o700)
    # One immutable upstream notebook fixture is a relative in-repository link.
    # Materialize it only in the owned input copy; retain its original link target.
    ruff_source=SOURCE/'19_ruff_project_analysis/task'
    ruff_copy=ROOT/'preparation-inputs/19_ruff_project_analysis/task'
    ruff_copy.parent.mkdir(parents=True)
    subprocess.run(['cp','-a','--reflink=auto',str(ruff_source),str(ruff_copy)],check=True)
    links=[]
    for path in ruff_copy.rglob('*'):
        if not path.is_symlink():continue
        target=path.resolve(strict=True)
        assert target.is_file() and target.is_relative_to(ruff_copy/'environment/submission')
        data=target.read_bytes()
        links.append({'path':str(path.relative_to(ruff_copy)),'original_link':os.readlink(path),
                      'resolved_content_sha256':hashlib.sha256(data).hexdigest()})
        path.unlink();path.write_bytes(data);shutil.copymode(target,path)
    assert len(links)==1
    (ruff_copy.parent/'materialization.json').write_text(json.dumps({'original_task':str(ruff_source),
        'changes':links,'originals_modified':False},indent=2)+'\n')
    subprocess.run(['cp','-a','--reflink=auto',str(FIXED/'framework'),str(ROOT/'framework')],check=True)
    f=ROOT/'framework'
    for name in ['account_model_slots.py','static_native.py']:
        p=f/'edgebench_harbor'/name;p.write_text(p.read_text().replace(str(FIXED),str(ROOT)))
    p=f/'edgebench_harbor/unleased_official_cloud_environment.py'
    t=p.read_text().replace('from pathlib import Path','from pathlib import Path\nimport json')
    t=t.replace("        persistent=dict(kwargs.pop('persistent_env',None) or {})", "        persistent=dict(kwargs.pop('persistent_env',None) or {})\n        task_env_file=Path(cloud_context)/'runtime-env.json'\n        if task_env_file.exists():\n            task_env=json.loads(task_env_file.read_text())\n            allowed={'PYTHONPATH','POLARS_MAX_THREADS','CARGO_HOME','CARGO_NET_OFFLINE','CARGO_TARGET_DIR','CARGO_BUILD_JOBS','COVERAGE_CORE','PYTHONDONTWRITEBYTECODE','PYTHONHASHSEED','PIP_NO_INDEX','PIP_DISABLE_PIP_VERSION_CHECK'}\n            if not set(task_env)<=allowed: raise ValueError('Unexpected task runtime environment key')\n            persistent.update(task_env)")
    t=t.replace(':/opt/venv/bin:/opt/venv/bin:',':/opt/rust/bin:/opt/venv/bin:')
    p.write_text(t)
    p=f/'edgebench_harbor/package_scorer.py'
    t=p.read_text();assert "'--cpus', '2'" in t
    p.write_text(t.replace("'--cpus', '2'", "'--cpus', str(self.profile.get('judge_cpus', 2))"))
    for name in ['build_packages.py','prepare_cloud_and_controls.py','run_native_controls.py','launch_run.py','roll_worker.py','dispatch.py']:
        t=(OLD/'scripts'/name).read_text().replace(str(OLD),str(ROOT))
        if name=='build_packages.py':
            t=t.replace("SOURCE = ROOT.parent / 'swe-authoring-016-20261015-r1/jobs'",'SOURCE = Path('+repr(str(SOURCE))+')')
            t=t.replace("        source = SOURCE / key / 'task'", "        source = SOURCE / key / 'task'\n        if key == '19_ruff_project_analysis': source = ROOT / 'preparation-inputs' / key / 'task'")
            a=t.index('TASKS = ');b=t.index('\n\n',a);t=t[:a]+'TASKS = '+repr(KEYS)+t[b:]
            t=t.replace('edge-raymone-swe-roll-r1-','edge-raymone-swe-roll-r5-').replace('timeout=1800','timeout=3600')
        if name=='prepare_cloud_and_controls.py':
            t=t.replace("            has_venv = copy_from(cid, '/opt/venv', assets / 'opt/venv', optional=True)", "            has_venv = copy_from(cid, '/opt/venv', assets / 'opt/venv', optional=True)\n            if key.startswith('19_'):\n                for path in ['/opt/rust', '/opt/cargo', '/opt/vendor']:\n                    copy_from(cid, path, assets / path.lstrip('/'))")
            t=t.replace("        # Fail closed on accidental inclusion", "        image_info = json.loads(subprocess.check_output(['docker','image','inspect',images['agent']['image_id']],text=True))[0]\n        allowed_env={'PYTHONPATH','POLARS_MAX_THREADS','CARGO_HOME','CARGO_NET_OFFLINE','CARGO_TARGET_DIR','CARGO_BUILD_JOBS','COVERAGE_CORE','PYTHONDONTWRITEBYTECODE','PYTHONHASHSEED','PIP_NO_INDEX','PIP_DISABLE_PIP_VERSION_CHECK'}\n        runtime_env={k:v for item in image_info['Config'].get('Env',[]) for k,v in [item.split('=',1)] if k in allowed_env}\n        runtime_env['PYTHONDONTWRITEBYTECODE']='1'\n        if key.startswith('19_'): runtime_env['CARGO_BUILD_JOBS']='4'\n        dump(context/'runtime-env.json',runtime_env)\n        shutil.copytree(Path("+repr(str(AUDIT))+"),context/'native-audit')\n        # Fail closed on accidental inclusion")
            audit_bootstrap = """
mkdir -p /opt/edgebench-native-audit
cp -a "$CTX/native-audit/." /opt/edgebench-native-audit/
chmod -R a+rX,go-w /opt/edgebench-native-audit
chmod 755 /opt/edgebench-native-audit/bin/*
"""
            polars_bootstrap = """
rm -rf WORK/upstream/py-polars/src/polars/streaming
ln -s WORK/submission/polars/streaming WORK/upstream/py-polars/src/polars/streaming
PYTHONPATH=WORK/upstream/py-polars/src POLARS_MAX_THREADS=4 /usr/local/bin/python -c 'import polars; print(polars.__version__)'
"""
            rust_bootstrap = """
chmod -R a+rX /opt/rust /opt/cargo /opt/vendor
mkdir -p WORK/target
chown -R agent:agent WORK/target /opt/cargo
command -v cc
/opt/rust/bin/rustc --version
cat > /tmp/edgebench-rust-probe.rs <<'RS'
fn main() {}
RS
/opt/rust/bin/rustc /tmp/edgebench-rust-probe.rs -o /tmp/edgebench-rust-probe
/tmp/edgebench-rust-probe
"""
            extra = '        bootstrap += ' + repr(audit_bootstrap) + '\n'
            extra += "        if key.startswith('18_'): bootstrap += " + repr(polars_bootstrap) + ".replace('WORK',work)\n"
            extra += "        if key.startswith('19_'): bootstrap += " + repr(rust_bootstrap) + ".replace('WORK',work)\n"
            t=t.replace("        (context / 'bootstrap.sh').write_text(bootstrap)", extra + "        (context / 'bootstrap.sh').write_text(bootstrap)")
            t=t.replace("'judge_memory_mb': cfg['verifier']['environment']['memory_mb']", "'judge_memory_mb': cfg['verifier']['environment']['memory_mb'], 'judge_cpus': cfg['verifier']['environment']['cpus'], 'judge_writable_root': True")
            t=t.replace('from harbor.models.task.config import TaskConfig','from harbor.models.task.config import TaskConfig, ArtifactConfig')
            t=t.replace("        t.agent.user = 'agent'", "        t.artifacts = [ArtifactConfig(source=work + '/submission')]\n        t.agent.user = 'agent'")
            marker="        if key.startswith('01_'):\n            shutil.rmtree(submission)"
            assert marker in t
            insert="""        if key.startswith('18_'):
            shutil.rmtree(submission)
            shutil.copytree(source / 'controls/mean_of_means', submission)
        elif key.startswith('19_'):
            shutil.copytree(source / 'authoring/controls/library-only', submission, dirs_exist_ok=True)
        elif key.startswith('20_'):
            shutil.rmtree(submission)
            shutil.copytree(SOURCE / key / 'controls/no_safety', submission)
        elif key.startswith('21_') or key.startswith('22_'):
            name = 'volatile-ledger.patch' if key.startswith('21_') else 'files-only.patch'
            with (source / 'authoring/controls' / name).open('rb') as patch_input:
                run(['patch', '-p1'], cwd=submission, stdin=patch_input, stdout=subprocess.DEVNULL)
        elif key.startswith('01_'):
            shutil.rmtree(submission)"""
            t=t.replace(marker,insert)
            # A root-private ephemeral judge filesystem is required by these graders.
            # Its numeric scoring source and constants remain the authored image bytes.
        compile(t,name,'exec')
        (ROOT/'scripts'/name).write_text(t)
    files={p.relative_to(f).as_posix():sha(p) for p in f.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
    (f/'framework-version.json').write_text(json.dumps({'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,'runtime_file_hashes':files,'runtime_tree_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),'source':str(FIXED/'framework'),'changes':['read allowlisted task runtime environment','use task-declared judge CPU count','rebase owned reservation/activity paths'],'native_audit_preflight_required':True},indent=2)+'\n')
    (ROOT/'PREPARATION.json').write_text(json.dumps({'tasks':KEYS,'model':'gpt-6.1-sol','budget_sec':21600,'interval_sec':600,'difficulty_early_stop':False,'score_formula_changed':False,'teacher_runs_started':0,'artifact_envelope':'whole submission directory; authored grader still selects candidate source','status':'preparing_each_task_independently'},indent=2)+'\n')

def one(key):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    with (ROOT/(key+'-preparation.log')).open('wb') as log:
        commands=[['-c',"from build_packages import build; build("+repr(key)+")"],
            [str(ROOT/'scripts/prepare_cloud_and_controls.py'),key],
            [str(ROOT/'scripts/run_native_controls.py'),key]]
        for command in commands:
            p=subprocess.run([sys.executable,*command],cwd=ROOT/'scripts',env=env,stdout=log,stderr=subprocess.STDOUT)
            if p.returncode:
                print(json.dumps({'task':key,'phase':'preparation_failed','failed_stage':command[0]}),flush=True)
                return
    print(json.dumps({'task':key,'phase':'ready_for_cloud_admission'}),flush=True)

if __name__=='__main__':
    setup()
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,KEYS))
