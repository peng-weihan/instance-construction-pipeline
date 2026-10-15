"""Freeze a startup-only repair, retaining original scoring measurements verbatim."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

OLD = Path('/ws/users/raymone/edgebench/swe-rollouts-003-20261015-r2')
ROOT = OLD.parent / 'swe-rollouts-003-20261015-r4'
AUDIT = OLD.parent / 'remaining-three-001/science-pilot/task/environment/native-audit'
KEYS = ['02_restler_recovery', '04_pytest_fixtures', '09_valkey_transactions']

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def inventory(root):
    assert not any(p.is_symlink() for p in root.rglob('*'))
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}

def dump(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n')

def prepare():
    ROOT.mkdir(exist_ok=False)
    (ROOT/'scripts').mkdir()
    (ROOT/'activity').mkdir(mode=0o700)
    subprocess.run(['cp','-a','--reflink=auto',str(OLD/'framework'),str(ROOT/'framework')],check=True)
    f=ROOT/'framework'
    audit_hashes=json.loads((f/'native-audit-tools.json').read_text())['files_sha256']
    assert inventory(AUDIT)==audit_hashes
    for name in ['account_model_slots.py','static_native.py']:
        p=f/'edgebench_harbor'/name
        p.write_text(p.read_text().replace(str(OLD),str(ROOT)))
    p=f/'edgebench_harbor/unleased_official_cloud_environment.py'
    t=p.read_text()
    anchor='        try:\n'
    assert t.count(anchor)==1
    t=t.replace(anchor,anchor+
        '            from .native_audit_tools import verify_installed_tools\n'
        '            await verify_installed_tools(self)\n'
        '            probe = await self.exec("LD_LIBRARY_PATH=/opt/edgebench-native-audit/lib /opt/edgebench-native-audit/bin/strace -f -e trace=connect -o /tmp/edgebench-native-preflight.trace /bin/true", user="agent", cwd="/", timeout_sec=30)\n'
        '            if probe.return_code: raise RuntimeError("Native audit execution preflight failed before any model entry")\n'
        '            self.evidence["native_audit_exec_preflight"] = {"user": "agent", "exit_code": probe.return_code}\n')
    p.write_text(t)
    for name in ['build_packages.py','launch_run.py','roll_worker.py','dispatch.py']:
        t=(OLD/'scripts'/name).read_text().replace(str(OLD),str(ROOT))
        if name=='launch_run.py':
            anchor="    assert inventory(task) == controls['task_hashes']"
            assert anchor in t
            t=t.replace(anchor,
                "    reuse = json.loads((PILOT / 'startup-repair-attestation.json').read_text())\n"
                "    assert inventory(task) == reuse['current_task_hashes']\n"
                "    assert controls['task_hashes'] == reuse['control_task_hashes']\n"
                "    assert native['source_task_hashes'] == reuse['control_task_hashes']\n"
                "    changed = {k for k in set(reuse['current_task_hashes']) | set(reuse['control_task_hashes']) if reuse['current_task_hashes'].get(k) != reuse['control_task_hashes'].get(k)}\n"
                "    assert changed == set(reuse['changed_task_files'])\n"
                "    assert all(k == 'environment/bootstrap.sh' or k.startswith('environment/native-audit/') for k in changed)\n"
                "    assert inventory(Path(reuse['previous_task'])) == reuse['control_task_hashes']")
        (ROOT/'scripts'/name).write_text(t)
    for key in KEYS:
        old,new=OLD/key,ROOT/key
        new.mkdir()
        subprocess.run(['cp','-a','--reflink=auto',str(old/'task'),str(new/'task')],check=True)
        before=inventory(new/'task')
        for name in ['images.json','scorer-controls.json']:
            shutil.copy2(old/name,new/name)
        (new/'native-controls').mkdir()
        shutil.copy2(old/'native-controls/report.json',new/'native-controls/report.json')
        assert before==json.loads((new/'scorer-controls.json').read_text())['task_hashes']
        shutil.copytree(AUDIT,new/'task/environment/native-audit')
        p=new/'task/environment/bootstrap.sh'
        p.write_text(p.read_text()+'\nmkdir -p /opt/edgebench-native-audit\ncp -a "$CTX/native-audit/." /opt/edgebench-native-audit/\nchmod -R a+rX,go-w /opt/edgebench-native-audit\nchmod 755 /opt/edgebench-native-audit/bin/*\n')
        after=inventory(new/'task')
        diff={k for k in set(before)|set(after) if before.get(k)!=after.get(k)}
        assert all(k=='environment/bootstrap.sh' or k.startswith('environment/native-audit/') for k in diff)
        dump(new/'startup-repair-attestation.json',{'previous_task':str(old/'task'),
            'control_task_hashes':before,'current_task_hashes':after,'changed_task_files':sorted(diff),
            'old_measurements_preserved':True,'scoring_and_student_starting_files_unchanged':True,
            'repair':'Install hash-locked public strace closure; enforce actual agent-user tracer probe before model entry'})
    files={k:v for k,v in inventory(f).items() if '__pycache__' not in Path(k).parts and k!='framework-version.json'}
    dump(f/'framework-version.json',{'status':'frozen','kind':'six_hour_engineering_pilot',
        'formal_acceptance':False,'runtime_file_hashes':files,
        'runtime_tree_sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),
        'source':str(OLD/'framework'),'repair':'Fail-closed public native-audit dependency validation before all cloud model entries'})
    print(json.dumps({'prepared':str(ROOT),'tasks':KEYS}))

if __name__=='__main__':
    prepare()
