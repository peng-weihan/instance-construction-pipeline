"""Continue an authorized pilot only after measured controls and cloud admission."""
import datetime,json,subprocess,sys,time
from pathlib import Path
R=Path('/ws/users/raymone/edgebench/next-two-001');kind,revision=sys.argv[1:];assert kind in ('packing','lean')
SDK='/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python'
report=R/(kind+'-controls-'+revision)/'report.json'
state=R/(kind+'-advance-'+revision+'.json')
def record(stage,**kw):state.write_text(json.dumps({'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw},indent=2)+'\n');print(stage,flush=True)
try:
 record('waiting_for_actual_controls');deadline=time.monotonic()+1800
 while True:
  if report.exists():
   d=json.loads(report.read_text())
   if d.get('status')=='completed':
    assert d['passed'],'controls failed';break
  if time.monotonic()>deadline:raise TimeoutError('controls did not complete')
  time.sleep(15)
 record('preparing_public_runtime')
 subprocess.run([SDK,str(R/'prepare_pilot.py'),kind,'--revision',revision],check=True)
 record('checking_candidate_isolation')
 subprocess.run(['python3',str(R/'probe_judge_identity.py'),kind,revision],check=True)
 pilot=R/(kind+'-pilot');f=pilot/'framework'
 record('running_real_official_cloud_admission')
 subprocess.run([SDK,str(f/'check_docker_admission.py'),'--backend','aliyun','--cloud-context',str(pilot/'task/environment'),'--task',str(pilot/'task'),'--images',str(pilot/'images.json'),'--codex-home','/ws/users/wcgu/new-codex-group/raymone/'+('2' if kind=='packing' else '3'),'--output',str(pilot/'admission'),'--native-transport','responses-websocket'],check=True)
 record('launching_authorized_six_hour_pilot')
 subprocess.run([SDK,str(R/'launch_agent.py'),kind],check=True)
 record('host_pilot_completed_check_run_manifest')
except Exception as e:
 record('stopped_on_failure',error=type(e).__name__+': '+str(e));raise
