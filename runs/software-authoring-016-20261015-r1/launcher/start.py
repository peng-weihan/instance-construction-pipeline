"""Two native authors on account 3; resume the queued third after a slot is released."""
from pathlib import Path
import datetime,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
assert not (ROOT/'startup.json').exists(),'do not duplicate jobs'
plan=json.loads((ROOT/'launch-plan.json').read_text());jobs={j['id']:j for j in plan['jobs']}
started=[];active={}
def launch(cid):
 job=jobs[cid];d=Path(job['cwd']);assert not (d/'status.json').exists()
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
 with (d/'supervisor.log').open('a') as log:
  p=subprocess.Popen([sys.executable,str(ROOT/'authoring/worker.py'),cid],stdin=subprocess.DEVNULL,stdout=log,stderr=log,cwd=d,env=env,start_new_session=True)
 active[cid]=p;started.append({'id':cid,'worker_pid':p.pid,'account':job['account'],'model':job['model']})
 return p
launch('01_openapi_streaming');launch('14_tree_sitter_incremental')
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scheduler_pid':os.getpid(),'jobs':started.copy(),'queued':['09_valkey_transactions'],'phase':'native_task_authoring_only_no_solver','account_selection_reason':'Other TB batch has unregistered native uses on accounts 1/2; use the two freshly audited slots of account 3 only.'}
(ROOT/'startup.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
# No time-based model stopping. Only poll our own supervised processes.
while all(p.poll() is None for p in active.values()):time.sleep(5)
finished=[cid for cid,p in active.items() if p.poll() is not None]
try:
 for cid in finished:
  state=json.loads((Path(jobs[cid]['cwd'])/'status.json').read_text())
  assert state.get('capacity_released'),'previous worker has not proved release'
 q=subprocess.run([sys.executable,str(ROOT/'authoring/refresh_capacity.py')],capture_output=True,text=True,check=True)
 launch('09_valkey_transactions');report.update({'jobs':started.copy(),'queued':[],'queue_dispatch_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
except Exception as exc:
 report.update({'queue_error_type':type(exc).__name__,'queue_state':'waiting_for_capacity_or_audit_fix'})
(ROOT/'startup.json').write_text(json.dumps(report,indent=2)+'\n')
for p in active.values():p.wait()
report['supervision_finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(ROOT/'startup.json').write_text(json.dumps(report,indent=2)+'\n')
