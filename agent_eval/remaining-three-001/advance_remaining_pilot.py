"""Start exactly one authorized model run after actual scorer and CLI gates."""
from pathlib import Path
import argparse,datetime,json,subprocess,time
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
def main(kind):
 out=ROOT/(kind+'-pilot');status=out/'advance.json';deadline=time.monotonic()+2400
 def save(stage,**x):status.write_text(json.dumps({'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**x},indent=2)+'\n');print(stage,flush=True)
 try:
  save('waiting_for_actual_scorer_and_official_cli_admission')
  while True:
   ready=True
   for path in [out/'scorer-controls/report.json',out/'admission-002/report.json',out/'isolation.json']:
    if not path.exists():ready=False;continue
    r=json.loads(path.read_text())
    if r.get('status') in ['failed','actual_official_smoke_failed']:raise RuntimeError('actual startup gate failed: '+str(path))
    if not r.get('passed'):ready=False
   if ready:break
   if time.monotonic()>deadline:raise TimeoutError('startup gates did not complete')
   time.sleep(5)
  save('launching_authorized_six_hour_trial',account='raymone/1',model='gpt-6.1-sol')
  SDK='/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python'
  subprocess.run([SDK,str(ROOT/'launch_agent.py'),kind],check=True)
  save('host_trial_finished_check_run_manifest')
 except Exception as exc:save('stopped_on_failure',error=str(exc));raise
if __name__=='__main__':p=argparse.ArgumentParser();p.add_argument('kind',choices=['game','finance']);main(p.parse_args().kind)
