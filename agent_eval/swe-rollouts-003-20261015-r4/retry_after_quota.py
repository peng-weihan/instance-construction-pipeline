"""Retry only a pre-model quota failure, using unchanged successful admission."""
from pathlib import Path
import datetime
import fcntl
import json
import os
import subprocess
import sys
import uuid

ROOT=Path('/ws/users/raymone/edgebench/swe-rollouts-003-20261015-r4')
KEY='04_pytest_fixtures'
ACCOUNT='raymone/1'
RUN=sys.argv[1] if len(sys.argv)>1 else 'run-6h-003'
assert RUN.startswith('run-6h-') and RUN.removeprefix('run-6h-').isdigit()
OUT=ROOT/KEY/RUN

def dump(p,d):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)

def main():
    old=sorted(p for p in (ROOT/KEY).glob('run-6h-*') if p.is_dir())[-1]
    results=list((old/'jobs/trial').glob('*/result.json'))
    assert len(results)==1
    err=json.loads(results[0].read_text()).get('exception_info') or {}
    assert err.get('exception_type')=='RateLimitException'
    assert 'Account resource quota exceeded' in err.get('exception_message','')
    assert not (old/'evaluation/events.jsonl').exists()
    admission=json.loads((ROOT/KEY/'admission/report.json').read_text())
    assert admission['passed'] and admission['selected_native_identity']['account']==ACCOUNT
    assert not OUT.exists()
    audit=ROOT.parent/'swe-authoring-016-20261015-r1/authoring/review_raymone123_actual_unused_accounts_r1.py'
    r=subprocess.run([sys.executable,str(audit)],capture_output=True,text=True,check=True,timeout=150)
    receipt=Path(json.loads(r.stdout.splitlines()[-1])['report'])
    report=json.loads(receipt.read_text())
    row=next(x for x in report['accounts'] if x['account']==ACCOUNT)
    assert not row['unknown_hosts'] and not row['SDK_observation_errors']
    count=sum(x['comm']=='codex' for x in row['actual_selected_codex_processes'])+len(row['active_SDK_learners'])+len(row['Docker_bindings'])
    assert count<10
    token=uuid.uuid4().hex
    entry={'task':KEY,'account':ACCOUNT,'worker_pid':os.getpid(),'worker_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
        'lease':token,'model_slots':1,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run':RUN}
    with (ROOT/'model-reservations.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads((ROOT/'model-reservations.json').read_text())
        assert state['outside_counts'][ACCOUNT]+sum(x['account']==ACCOUNT for x in state['leases'].values())+1<=10
        state['leases'][token]=entry;dump(ROOT/'model-reservations.json',state)
    status=ROOT/KEY/(RUN+'-retry-status.json')
    dump(status,{**entry,'phase':'launching','fresh_actual_account_receipt':str(receipt),'previous_quota_failure_preserved':True})
    launcher=ROOT/'scripts'/('launch_'+RUN+'.py')
    assert not launcher.exists()
    launcher.write_text((ROOT/'scripts/launch_run.py').read_text().replace("'run-6h-001'",repr(RUN)))
    env={**os.environ,'EDGEBENCH_SELECTED_ACCOUNT':ACCOUNT,'EDGEBENCH_SLOT_TOKEN':token,'PYTHONDONTWRITEBYTECODE':'1'}
    try:
        with (ROOT/KEY/(RUN+'-retry-launch.log')).open('xb') as log:
            result=subprocess.run([sys.executable,str(launcher),KEY,ACCOUNT],env=env,stdout=log,stderr=subprocess.STDOUT)
        dump(status,{**entry,'phase':'host_returned','exit_code':result.returncode,'formal_acceptance':False})
    finally:
        ledgers=list((OUT/'jobs/trial').glob('*/aliyun-*.json'))
        safe=all(not (d:=json.loads(p.read_text())).get('created') or d.get('destroyed') for p in ledgers)
        if safe:
            with (ROOT/'model-reservations.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                state=json.loads((ROOT/'model-reservations.json').read_text())
                released=state['leases'].pop(token,None)
                state.setdefault('released',[]).append({'lease':released,'reason':'retry worker ended and own learners absent'})
                dump(ROOT/'model-reservations.json',state)

if __name__=='__main__':main()
