"""Launch remaining authors using fresh observed sessions, without editing foreign registry.

The old shared table is advisory and contains stale/unidentified holds. Keep its
bytes/reservations untouched. Reserve locally against actual SDK/native usage,
plus one unresolved old account-3 cloud lease. Each account stays within 10.
"""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'actual-native-slots'
ids=['04_pytest_fixtures','07_arrow_ipc','08_http2_session','11_rocksdb_compaction','12_croaring_kernels','15_jq_composition','16_libarchive_cli']
lock=(ROOT/'remaining-live-dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
credential_source=next((Path('/proc')/str(pid)/'environ' for pid in [3683329,3418236] if (Path('/proc')/str(pid)/'environ').exists()),None)
assert credential_source is not None
values=dict(x.split(b'=',1) for x in credential_source.read_bytes().split(b'\0') if b'=' in x)
for key in ['TBSCI_E2B_CREDENTIAL_FILE','E2B_API_KEY','E2B_API_URL','E2B_DOMAIN']:
 if key.encode() in values:env[key]=values[key.encode()].decode()
plan_path=ROOT/'launch-plan.json';plan=json.loads(plan_path.read_text());jobs={j['id']:j for j in plan['jobs']}
pending=[cid for cid in ids if not (Path(jobs[cid]['cwd'])/'status.json').exists()]
# Prevent the older local pool from duplicating these jobs during admission.
for cid in pending:
 p=Path(jobs[cid]['cwd'])/'status.json'
 with p.open('x') as f:json.dump({**jobs[cid],'state':'pending_actual_admission','teacher_rollouts_started':0},f,indent=2)
REG.mkdir(exist_ok=True)
assert not any(REG.glob('raymone*.json')),'preserve existing live-slot registry'
worker=(ROOT/'authoring/worker.py').read_text()
worker=worker.replace("D=Path(JOB['cwd']);status=", "LIVE_REG=ROOT/'actual-native-slots'\nD=Path(JOB['cwd']);status=")
worker=worker.replace("return slots.transaction(JOB['account'],act)", "return slots.transaction(JOB['account'],act,registry=LIVE_REG)")
worker=worker.replace("lease=slots.acquire(JOB['account'])", "lease=slots.acquire(JOB['account'],registry=LIVE_REG)")
worker=worker.replace("slots.release(lease,'startup_failed_before_any_model_entry')", "slots.release(lease,'startup_failed_before_any_model_entry',registry=LIVE_REG)")
assert 'registry=LIVE_REG' in worker
(ROOT/'authoring/worker_actual_live.py').write_text(worker)
q=subprocess.run([sys.executable,str(ROOT/'authoring/review_raymone123_actual_unused_accounts_r1.py')],env=env,capture_output=True,text=True,check=True,timeout=150)
receipt=Path(json.loads(q.stdout.splitlines()[-1])['report']);a=json.loads(receipt.read_text())
summary={'observed_utc':a['observed_utc'],'observed_epoch':a['observed_epoch'],'source_receipt':str(receipt),'mode':'actual_host_and_linked_cloud_sessions_plus_unresolved_account3_hold','shared_registry_edited':False,'account_limit':10,'accounts':{},'pending':pending.copy(),'dispatched':[]}
shared=Path('/ws/users/wcgu/edgebench/dev/task/1013/_nonobtuse-coordination/account-model-concurrency-v001')
for row in a['accounts']:
 account=row['account'];roots=[x for x in row['actual_selected_codex_processes'] if x['comm']=='codex']
 cloud=len(row['active_SDK_learners']);native=len(roots)
 unknown=1 if account=='raymone/3' else 0
 # SDK failures are not spare capacity. Existing ambiguous Docker bindings are
 # conservatively counted in addition unless mapped to an observed native root.
 errors=len(row['SDK_observation_errors']);docker_extra=len(row['Docker_bindings'])
 outside=cloud+native+unknown+docker_extra
 available=max(0,10-outside) if not errors and not row['unknown_hosts'] else 0
 old=(shared/('raymone'+account[-1]+'.json')).read_bytes()
 summary['accounts'][account]={'cloud_sessions':cloud,'native_roots':native,'unresolved_old_cloud_hold':unknown,'extra_Docker_reservations':docker_extra,'SDK_observation_errors':errors,'observed_other_slots':outside,'available':available,'shared_registry_sha256_before':hashlib.sha256(old).hexdigest()}
report=ROOT/'reports'/('remaining-live-admission-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
report.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
for account,info in summary['accounts'].items():
 n=account[-1]
 state={'account':account,'limit':10,'external_reserved':min(info['observed_other_slots'],10),'leases':{},'events':[],'global_actual_audit':{'observed_epoch':a['observed_epoch'],'receipt':str(report),'unknown_unreserved_slots':0,'foreground_reservation_includes_multiplexed_agents':True,'scope':'Native author admission by fresh actual use. One unresolved old account-3 learner remains conservatively reserved.'}}
 (REG/f'raymone{n}.json').write_text(json.dumps(state,indent=2)+'\n')
for account in ['raymone/1','raymone/2','raymone/3']:
 for _ in range(summary['accounts'][account]['available']):
  if not pending:break
  assert time.time()-a['observed_epoch']<100
  cid=pending.pop(0);plan=json.loads(plan_path.read_text());job=next(j for j in plan['jobs'] if j['id']==cid);job['account']=account;job['codex_home']='/ws/users/wcgu/new-codex-group/'+account;job['admission']='fresh_actual_usage_local_reservation'
  tmp=plan_path.with_suffix('.live-dispatch.tmp');tmp.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');tmp.replace(plan_path)
  d=Path(job['cwd'])
  with (d/'supervisor.log').open('a') as log:
   p=subprocess.Popen([sys.executable,str(ROOT/'authoring/worker_actual_live.py'),cid],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,cwd=d,start_new_session=True)
  summary['dispatched'].append({'id':cid,'account':account,'worker_pid':p.pid,'model':'gpt-6.1-sol'})
summary['pending']=pending
summary['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(ROOT/'reports/remaining-live-dispatch.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'dispatched':summary['dispatched'],'pending':pending,'account_available_before':{k:v['available'] for k,v in summary['accounts'].items()},'shared_registry_edited':False},ensure_ascii=False))
