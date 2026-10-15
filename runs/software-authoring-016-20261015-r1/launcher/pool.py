"""Persistent dispatcher for all authorized author jobs. No solver/extra model agents."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'authoring'))
from refresh_capacity import assess,REG
LOCK=(ROOT/'all-pool.lock').open('a');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)
ENV=os.environ.copy();ENV['PYTHONDONTWRITEBYTECODE']='1'
MODELPY=sys.executable
state={'authorized_total':16,'phase':'task_authoring_only','pool_pid':os.getpid(),'pool_started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'teacher_runs_started':0,'events':[]}
children={}
def save():
 state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 tmp=ROOT/'reports/all-pool-status.tmp';tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');tmp.replace(ROOT/'reports/all-pool-status.json')
def current():
 plan=json.loads((ROOT/'launch-plan.json').read_text());jobs=plan['jobs'];pending=[];running=[];done=[];failed=[]
 for j in jobs:
  p=Path(j['cwd'])/'status.json'
  if not p.exists():pending.append(j['id']);continue
  s=json.loads(p.read_text())
  if s['state']=='author_returned':done.append(j['id'])
  elif s['state']=='launch_or_supervision_error':failed.append(j['id'])
  else:running.append(j['id'])
 state.update({'pending':pending,'running':running,'author_returned':done,'failed':failed})
 return {j['id']:j for j in jobs},pending

def capacity():
 q=subprocess.run([MODELPY,str(ROOT/'authoring/review_raymone123_actual_unused_accounts_r1.py')],env=ENV,capture_output=True,text=True,timeout=150)
 if q.returncode:raise RuntimeError('actual capacity inventory failed; models not launched')
 receipt=Path(json.loads(q.stdout.splitlines()[-1])['report']);a=json.loads(receipt.read_text());rows={v['account']:v for v in a['accounts']}
 assert time.time()-a['observed_epoch']<100
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 report={'observed_epoch':a['observed_epoch'],'actual_readonly_audit':str(receipt),'accounts':{},'authorization':'User explicitly requested all sixteen author attempts with raymone/1,2,3; preserve all leases and external reservations'}
 states={}
 for n in [1,2,3]:
  s=json.loads((REG/f'raymone{n}.json').read_text());account=s['account']
  try:
   assessed=assess(rows[account],s);states[n]=s
   report['accounts'][account]={'eligible':True,**assessed,'preserved_lease_count':len(s['leases']),'external_reserved':s['external_reserved']}
  except (AssertionError,KeyError,ValueError,OSError) as e:
   report['accounts'][account]={'eligible':False,'spare_slots':0,'reason':str(e),'preserved_lease_count':len(s['leases']),'external_reserved':s['external_reserved']}
 dest=ROOT/'reports'/f'all-pool-capacity-{stamp}.json';dest.write_text(json.dumps(report,indent=2)+'\n')
 for n,old in states.items():
  with (REG/f'raymone{n}.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);p=REG/f'raymone{n}.json';s=json.loads(p.read_text());account=s['account']
   if s['leases']!=old['leases'] or s['external_reserved']!=old['external_reserved'] or time.time()-a['observed_epoch']>=100:
    report['accounts'][account].update({'eligible':False,'spare_slots':0,'reason':'capacity changed during audit; retry later'});continue
   s['global_actual_audit']={**s.get('global_actual_audit',{}),'observed_epoch':a['observed_epoch'],'receipt':str(dest),'receipt_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'unknown_unreserved_slots':0,'scope':'All-sixteen author pool; fresh SDK/host/Docker actual inventory with every canonical and external reservation preserved.'}
   s.setdefault('events',[]).append({'event':'all_sixteen_author_pool_actual_capacity_refresh','receipt':str(dest),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'leases_preserved':len(s['leases']),'external_reserved_preserved':s['external_reserved']})
   tmp=p.with_suffix('.all-author-pool.tmp');tmp.write_text(json.dumps(s,indent=2)+'\n');tmp.chmod(0o600);tmp.replace(p)
 # Keep the receipt immutable after publishing its digest.
 state['latest_capacity_receipt']=str(dest);state['last_capacity']={k:{x:v[x] for x in ['eligible','spare_slots','preserved_lease_count','external_reserved']} for k,v in report['accounts'].items()}
 return report

def launch(cid,account):
 p=ROOT/'launch-plan.json';plan=json.loads(p.read_text());job=next(j for j in plan['jobs'] if j['id']==cid);d=Path(job['cwd'])
 assert not (d/'status.json').exists()
 job['account']=account;job['codex_home']='/ws/users/wcgu/new-codex-group/'+account
 tmp=p.with_suffix('.dispatch.tmp');tmp.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
 with (d/'supervisor.log').open('a') as log:
  child=subprocess.Popen([MODELPY,str(ROOT/'authoring/worker.py'),cid],env=ENV,stdin=subprocess.DEVNULL,stdout=log,stderr=log,cwd=d,start_new_session=True)
 children[cid]=child
 state['events'].append({'event':'author_dispatched','id':cid,'account':account,'worker_pid':child.pid,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 # Let the atomic lease acquisition finish before considering another slot.
 for _ in range(30):
  status=d/'status.json'
  if status.exists():
   j=json.loads(status.read_text())
   if j['state'] not in ['starting','slot_reserved']:break
  time.sleep(0.1)

while True:
 for cid,p in list(children.items()):
  if p.poll() is not None:children.pop(cid)
 jobs,pending=current();save()
 if pending:
  try:
   report=capacity()
   for account,c in report['accounts'].items():
    if not c['eligible']:continue
    for _ in range(c['spare_slots']):
     jobs,pending=current()
     if not pending:break
     launch(pending[0],account);save()
   current();save()
  except Exception as e:
   state['last_audit_or_dispatch_error']={'type':type(e).__name__,'message':str(e)[:400],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save()
 jobs,pending=current();save()
 if not pending and not children:
  state['dispatch_finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();break
 time.sleep(30)
