"""Admit each actually prepared task once, using a fresh account observation."""
from pathlib import Path
import datetime
import fcntl
import json
import os
import subprocess
import sys
import time
import uuid

ROOT=Path(sys.argv[1]).resolve(strict=True)
KEYS=sys.argv[2:]
AUDIT=ROOT.parent/'swe-authoring-016-20261015-r1/authoring/review_raymone123_actual_unused_accounts_r1.py'

def dump(p,d):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');tmp.replace(p)

def ready(key):
    p=ROOT/key
    if (p/'roll-status.json').exists():return False
    try:
        controls=json.loads((p/'scorer-controls.json').read_text())
        native=json.loads((p/'native-controls/report.json').read_text())
    except (FileNotFoundError,ValueError):return False
    return controls.get('passed') is True and native.get('passed') is True and all(native.get('results',{}).get(k,{}).get('passed') for k in ['oracle','nop','partial'])

def dispatch(keys):
    check=subprocess.run([sys.executable,str(AUDIT)],capture_output=True,text=True,timeout=150,check=True)
    path=Path(json.loads(check.stdout.splitlines()[-1])['report']);observed=json.loads(path.read_text())
    assert time.time()-observed['observed_epoch']<90
    registry=ROOT/'model-reservations.json'
    with (ROOT/'model-reservations.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads(registry.read_text()) if registry.exists() else {'leases':{},'released':[],'account_limit':10,'shared_registries_modified':False}
        outside={};available={}
        for row in observed['accounts']:
            account=row['account']
            external_cloud=[x for x in row['active_SDK_learners'] if not str(x.get('task','')).startswith(str(ROOT)+'/')]
            count=len(external_cloud)+len(row['Docker_bindings'])+sum(x['comm']=='codex' for x in row['actual_selected_codex_processes'])
            if account=='raymone/3':count+=1  # Preserve the older unresolved external reservation.
            outside[account]=count
            owned=sum(v['account']==account for v in state['leases'].values())
            available[account]=max(0,10-count-owned) if not row['unknown_hosts'] and not row['SDK_observation_errors'] else 0
        state.update(outside_counts=outside,observed_epoch=observed['observed_epoch'],actual_audit_receipt=str(path),purpose='one independent learner per prepared task')
        dump(registry,state)
        dispatched=[]
        for key in keys:
            if not ready(key):continue
            account=max(available,key=available.get)
            if available[account]<1:break
            token=uuid.uuid4().hex
            with (ROOT/key/'roll-worker.log').open('xb') as log:
                child=subprocess.Popen([sys.executable,'-u',str(ROOT/'scripts/roll_worker.py'),key,account,token],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
            ticks=Path('/proc',str(child.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
            entry={'task':key,'account':account,'worker_pid':child.pid,'worker_start_ticks':ticks,'lease':token,'model_slots':1,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            state['leases'][token]=entry;dump(registry,state)
            available[account]-=1;dispatched.append(entry)
        return dispatched

def main():
    lock=(ROOT/'ready-queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    end=time.monotonic()+21600
    history=[]
    while time.monotonic()<end:
        pending=[k for k in KEYS if not (ROOT/k/'roll-status.json').exists()]
        candidates=[k for k in pending if ready(k)]
        if candidates:
            try:history.extend(dispatch(candidates))
            except Exception as exc:
                # No raw SDK messages, account values, or authentication material.
                history.append({'event':'admission_observation_error','error_type':type(exc).__name__,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        remaining=[k for k in KEYS if not (ROOT/k/'roll-status.json').exists()]
        dump(ROOT/'ready-queue-status.json',{'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'pending_preparation_or_account_capacity':remaining,'attempted':history,'model':'gpt-6.1-sol',
            'budget_seconds':21600,'interval_seconds':600,'difficulty_early_stop':False,
            'does_not_retry_failed_model_or_cloud_attempts':True,'queue_pid':os.getpid(),
            'queue_active':bool(remaining),'preparation_wait_limit_seconds':21600})
        if not remaining:return
        time.sleep(60)
    p=ROOT/'ready-queue-status.json';d=json.loads(p.read_text());d.update(queue_active=False,queue_exit_reason='preparation_wait_deadline');dump(p,d)

if __name__=='__main__':main()
