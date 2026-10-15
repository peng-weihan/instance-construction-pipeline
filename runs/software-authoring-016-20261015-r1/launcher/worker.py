"""One reserved native Codex author. No cloud learner, solver or subagents."""
from pathlib import Path
import datetime,json,os,signal,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'authoring'))
import global_account_model_slots as slots
JOB=next(j for j in json.loads((ROOT/'launch-plan.json').read_text())['jobs'] if j['id']==sys.argv[1])
D=Path(JOB['cwd']);status={**JOB,'worker_pid':os.getpid(),'worker_start_ticks':slots.ticks(os.getpid()),'state':'starting','phase':'authoring_only','teacher_rollouts_started':0}
def save(**values):
 status.update(values);status['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 tmp=D/'status.tmp.json';tmp.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');tmp.replace(D/'status.json')
def change_owned(lease,fn):
 def act(s):
  v=s['leases'][lease['lease']]
  assert v['host_pid']==os.getpid() and v['host_start_ticks']==slots.ticks(os.getpid())
  return fn(s,v)
 return slots.transaction(JOB['account'],act)
def members(pgid):
 result=[]
 for p in Path('/proc').glob('[0-9]*/stat'):
  try:
   fields=p.read_text().rsplit(')',1)[1].split()
   if int(fields[2])==pgid and fields[0]!='Z':result.append(int(p.parent.name))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
 return result
lease=None;child=None
try:
 save()
 lease=slots.acquire(JOB['account'])
 def mark(s,v):v.update({'kind':'native_task_author','job_id':JOB['id'],'job_dir':str(D),'launch_controller_pid':os.getpid()})
 change_owned(lease,mark);save(lease_id=lease['lease'],state='slot_reserved')
 home=Path(JOB['codex_home']);exe=home/'bin/codex'
 assert exe.is_file()
 env=os.environ.copy();env.update({'CODEX_HOME':str(home),'PATH':str(home/'bin')+os.pathsep+env.get('PATH','/usr/bin:/bin'),'PYTHONDONTWRITEBYTECODE':'1','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','EDGEBENCH_AUTHOR_JOB':JOB['id']})
 for secret_key in ['TBSCI_E2B_CREDENTIAL_FILE','E2B_API_KEY','E2B_API_URL','E2B_DOMAIN']:
  env.pop(secret_key,None)
 cmd=[str(exe),'exec','--model',JOB['model'],'-c','model_reasoning_effort="high"','-c','features.multi_agent=false','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-C',str(D),'--json','--output-last-message',str(D/'final.md'),'-']
 with (D/'prompt.md').open() as inp,(D/'trajectory.jsonl').open('a') as out,(D/'codex.stderr.log').open('a') as err:
  child=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,env=env,cwd=D,start_new_session=True)
  native_ticks=slots.ticks(child.pid)
  def mark_native(s,v):v.update({'native_pid':child.pid,'native_start_ticks':native_ticks,'codex_home':str(home),'model':JOB['model']})
  change_owned(lease,mark_native)
  save(state='native_started',native_pid=child.pid,native_start_ticks=native_ticks,selected_binary=str(exe),resolved_binary=str(exe.resolve()),native_started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  code=child.wait()
 # Only clean the child's own process group; never touch foreign processes.
 if members(child.pid):
  os.killpg(child.pid,signal.SIGTERM);time.sleep(1)
 if members(child.pid):
  os.killpg(child.pid,signal.SIGKILL);time.sleep(0.2)
 assert not members(child.pid),'own child process group survives; retain reservation'
 save(state='author_returned',native_exit_code=code,result_file_exists=(D/'AUTHOR_RESULT.json').exists(),native_finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 def release(s,v):
  del s['leases'][lease['lease']]
  s.setdefault('events',[]).append({'event':'native_task_author_exit_release','lease':lease['lease'],'job_id':JOB['id'],'native_pid':child.pid,'native_exit_code':code,'own_process_group_empty':True,'utc':slots.utc()})
 change_owned(lease,release);lease=None;save(capacity_released=True)
except Exception as exc:
 save(state='launch_or_supervision_error',error_type=type(exc).__name__,error_message=str(exc)[:600],capacity_released=False)
 if lease and child is None:
  slots.release(lease,'startup_failed_before_any_model_entry');lease=None;save(capacity_released=True)
 raise
