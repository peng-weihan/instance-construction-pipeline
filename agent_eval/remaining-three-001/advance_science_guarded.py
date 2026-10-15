"""Refresh actual capacity using the existing host tool before each guarded entry."""
from pathlib import Path
import datetime,json,subprocess
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OUT=ROOT/'science-pilot'
SDK='/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python'
REFRESH='/root/professional-growth-20261014/authoring/refresh_owned_raymone1_capacity_r1.py'
def record(stage,**kw):
 (ROOT/'science-advance.json').write_text(json.dumps({'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw},indent=2)+'\n');print(stage,flush=True)
try:
 record('fresh_shared_capacity_audit_before_admission')
 subprocess.run([SDK,REFRESH],check=True)
 record('actual_guarded_official_codex_cloud_admission')
 subprocess.run([SDK,str(OUT/'framework-r2/check_docker_admission.py'),'--backend','aliyun','--cloud-context',str(OUT/'task/environment'),'--task',str(OUT/'task'),'--images',str(OUT/'images.json'),'--codex-home','/ws/users/wcgu/new-codex-group/raymone/1','--output',str(OUT/'admission-002'),'--native-transport','responses-websocket'],check=True)
 record('fresh_shared_capacity_audit_before_full_run')
 subprocess.run([SDK,REFRESH],check=True)
 record('launching_actual_six_hour_scientific_trial')
 subprocess.run([SDK,str(ROOT/'launch_science_agent_r2.py'),'science'],check=True)
 record('host_trial_finished_check_run_evidence')
except Exception as e:
 record('stopped_on_failure',error=type(e).__name__+': '+str(e));raise
