"""One independent authorized full-budget finance rerun, with real guarded gates."""
from pathlib import Path
import datetime,json,subprocess,time
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OUT=ROOT/'finance-pilot-r3'
SDK='/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python'
def record(stage,**kw):
 (ROOT/'finance-retry-status.json').write_text(json.dumps({'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw},ensure_ascii=False,indent=2)+'\n');print(stage,flush=True)
def capacity():
 for attempt in range(20):
  p=subprocess.run([SDK,str(OUT/'capacity-audit/authoring/refresh_capacity.py')],capture_output=True,text=True)
  with (OUT/'capacity-refresh-attempts.log').open('a') as log:log.write(p.stdout+p.stderr)
  if p.returncode==0:
   print(p.stdout,flush=True);return
  record('waiting_for_actual_shared_capacity',attempt=attempt+1)
  time.sleep(30)
 raise RuntimeError('No freshly audited shared account capacity; no model launch')
try:
 record('preparing_independent_finance_retry')
 subprocess.run([SDK,str(ROOT/'prepare_finance_retry.py')],check=True)
 record('actual_scorer_controls_and_previous_failed_snapshot_replay')
 subprocess.run([SDK,str(ROOT/'check_finance_retry_controls.py')],check=True)
 record('fresh_actual_capacity_before_official_admission');capacity()
 record('actual_official_codex_admission')
 subprocess.run([SDK,str(OUT/'framework/check_docker_admission.py'),'--backend','aliyun','--cloud-context',str(OUT/'task/environment'),'--task',str(OUT/'task'),'--images',str(OUT/'images.json'),'--codex-home','/ws/users/wcgu/new-codex-group/raymone/1','--output',str(OUT/'admission'),'--native-transport','responses-websocket'],check=True)
 record('fresh_actual_capacity_before_full_learning');capacity()
 record('launching_one_new_six_hour_finance_session')
 subprocess.run([SDK,str(ROOT/'launch_finance_retry.py'),'finance'],check=True)
 record('host_trial_finished_check_final_evidence')
except Exception as e:
 record('stopped_on_failure',error=type(e).__name__+': '+str(e));raise
