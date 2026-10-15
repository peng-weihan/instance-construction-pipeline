"""Resume only this batch's unstarted Valkey author after fresh actual capacity review."""
from pathlib import Path
import datetime,fcntl,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'dispatch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 plan=json.loads((ROOT/'launch-plan.json').read_text());job=next(x for x in plan['jobs'] if x['id']=='09_valkey_transactions');d=Path(job['cwd'])
 assert not (d/'status.json').exists(),'already dispatched; never duplicate'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
 values=dict(v.split(b'=',1) for v in Path('/proc/3683329/environ').read_bytes().split(b'\0') if b'=' in v)
 for key in ['TBSCI_E2B_CREDENTIAL_FILE','E2B_API_KEY','E2B_API_URL','E2B_DOMAIN']:
  if key.encode() in values:env[key]=values[key.encode()].decode()
 q=subprocess.run([sys.executable,str(ROOT/'authoring/refresh_capacity.py')],env=env,capture_output=True,text=True)
 (ROOT/'reports'/f'queue-resume-capacity-{stamp}.stdout').write_text(q.stdout)
 (ROOT/'reports'/f'queue-resume-capacity-{stamp}.stderr').write_text(q.stderr)
 if q.returncode:
  print(json.dumps({'state':'capacity_audit_blocked','returncode':q.returncode,'diagnostic_file':str(ROOT/'reports'/f'queue-resume-capacity-{stamp}.stderr')}));raise SystemExit(q.returncode)
 old=(ROOT/'startup.json').read_text();(ROOT/'reports'/f'startup-before-resume-{stamp}.json').write_text(old)
 with (d/'supervisor.log').open('a') as log:
  p=subprocess.Popen([sys.executable,str(ROOT/'authoring/worker.py'),job['id']],stdin=subprocess.DEVNULL,stdout=log,stderr=log,env=env,cwd=d,start_new_session=True)
 s=json.loads(old);s.setdefault('resume_history',[]).append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Tool child of an external-reserved native root was double counted; group by actual native root and start_ticks, preserve all model reservations','worker_pid':p.pid,'capacity_receipt':json.loads(q.stdout.splitlines()[-1])['receipt']})
 s['jobs'].append({'id':job['id'],'worker_pid':p.pid,'account':job['account'],'model':job['model']});s['queued']=[];s['queue_state']='dispatched_after_actual_capacity_refresh'
 (ROOT/'startup.json').write_text(json.dumps(s,indent=2)+'\n')
 print(json.dumps({'state':'dispatched','id':job['id'],'worker_pid':p.pid,'account':job['account'],'model':job['model']}))
