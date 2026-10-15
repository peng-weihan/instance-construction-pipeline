"""Complete original OpenAPI/HTTPX pilots with repaired cloud startup dependencies."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shutil
import subprocess
import sys

BASE=Path('/ws/users/raymone/edgebench')
ROOT=BASE/'swe-rollouts-002-20261015-r6'
OLD=BASE/'swe-rollouts-002-20261015-r3'
FIXED=BASE/'swe-rollouts-003-20261015-r4'
KEYS=['01_openapi_streaming','03_httpx_transport']
AUDIT=BASE/'remaining-three-001/science-pilot/task/environment/native-audit'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def inventory(root):
    assert not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}

def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def main():
    ROOT.mkdir(exist_ok=False);(ROOT/'scripts').mkdir();(ROOT/'activity').mkdir(mode=0o700)
    subprocess.run(['cp','-a','--reflink=auto',str(FIXED/'framework'),str(ROOT/'framework')],check=True)
    f=ROOT/'framework'
    for name in ['account_model_slots.py','static_native.py']:
        p=f/'edgebench_harbor'/name;p.write_text(p.read_text().replace(str(FIXED),str(ROOT)))
    for name in ['build_packages.py','launch_run.py','roll_worker.py']:
        t=(FIXED/'scripts'/name).read_text().replace(str(FIXED),str(ROOT))
        if name=='build_packages.py':
            a=t.index('TASKS = ');b=t.index('\n\n',a);t=t[:a]+'TASKS = '+repr(KEYS)+t[b:]
        if name=='launch_run.py':
            t=t.replace("assert native['source_task_hashes'] == reuse['control_task_hashes']", "assert native['source_task_hashes'] == reuse['current_task_hashes']")
            t=t.replace("k == 'environment/bootstrap.sh' or k.startswith('environment/native-audit/')", "k in ('environment/bootstrap.sh', 'task.toml') or k.startswith('environment/native-audit/')")
        (ROOT/'scripts'/name).write_text(t)
    (ROOT/'scripts/run_native_controls.py').write_text((BASE/'swe-rollouts-005-20261015-r1/scripts/run_native_controls.py').read_text())
    sys.path[:0]=[str(f),str(f/'sdk')]
    from harbor.models.task.config import TaskConfig,ArtifactConfig
    assert inventory(AUDIT)==json.loads((f/'native-audit-tools.json').read_text())['files_sha256']
    for key in KEYS:
        old,new=OLD/key,ROOT/key;new.mkdir()
        for name in ['task','controls']:
            subprocess.run(['cp','-a','--reflink=auto',str(old/name),str(new/name)],check=True)
        for name in ['images.json','scorer-controls.json']:shutil.copy2(old/name,new/name)
        controls=json.loads((new/'scorer-controls.json').read_text());before=inventory(new/'task')
        assert controls['passed'] and controls['task_hashes']==before
        shutil.copytree(AUDIT,new/'task/environment/native-audit')
        p=new/'task/environment/bootstrap.sh'
        p.write_text(p.read_text()+'\nmkdir -p /opt/edgebench-native-audit\ncp -a "$CTX/native-audit/." /opt/edgebench-native-audit/\nchmod -R a+rX,go-w /opt/edgebench-native-audit\nchmod 755 /opt/edgebench-native-audit/bin/*\n')
        p=new/'task/task.toml';cfg=TaskConfig.model_validate_toml(p.read_text())
        cfg.artifacts=[ArtifactConfig(source=cfg.environment.workdir+'/submission')]
        p.write_text(cfg.model_dump_toml())
        after=inventory(new/'task');diff={k for k in set(before)|set(after) if before.get(k)!=after.get(k)}
        assert all(k in ('task.toml','environment/bootstrap.sh') or k.startswith('environment/native-audit/') for k in diff)
        dump(new/'startup-repair-attestation.json',{'previous_task':str(old/'task'),'control_task_hashes':before,
            'current_task_hashes':after,'changed_task_files':sorted(diff),'old_measurements_preserved':True,
            'scoring_and_student_starting_files_unchanged':True,'native_controls':'new native controls required on this exact task metadata',
            'repair':'Install public native-audit closure and declare full submission snapshot envelope; scorer selects same source'})
    files={k:v for k,v in inventory(f).items() if '__pycache__' not in Path(k).parts and k!='framework-version.json'}
    dump(f/'framework-version.json',{'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,
        'runtime_file_hashes':files,'runtime_tree_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),
        'source':str(FIXED/'framework'),'changes':['rebase own account/activity paths']})
    def control(key):
        with (ROOT/key/'native-preparation.log').open('xb') as log:
            p=subprocess.run([sys.executable,str(ROOT/'scripts/run_native_controls.py'),key],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        print(json.dumps({'task':key,'native_controls_exit':p.returncode}),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(control,KEYS))

if __name__=='__main__':main()
