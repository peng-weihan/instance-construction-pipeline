"""Authorized first scientific rollout, actual gates before starting the clock."""
from pathlib import Path
import datetime,json,subprocess
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OUT=ROOT/'science-pilot'
SDK='/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python'
def record(stage,**kw):
 (ROOT/'science-advance.json').write_text(json.dumps({'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw},indent=2)+'\n');print(stage,flush=True)
try:
 record('building_offline_ml_runtime')
 subprocess.run([SDK,str(ROOT/'prepare_singlecell_remote.py')],check=True)
 record('actual_controls_and_public_baseline')
 subprocess.run([SDK,str(ROOT/'check_singlecell_controls.py')],check=True)
 record('actual_isolation_probe')
 subprocess.run(['python3',str(ROOT/'probe_science_isolation.py'),'science'],check=True)
 record('real_official_codex_cloud_admission')
 subprocess.run([SDK,str(OUT/'framework/check_docker_admission.py'),'--backend','aliyun','--cloud-context',str(OUT/'task/environment'),'--task',str(OUT/'task'),'--images',str(OUT/'images.json'),'--codex-home','/ws/users/wcgu/new-codex-group/raymone/1','--output',str(OUT/'admission'),'--native-transport','responses-websocket'],check=True)
 record('launching_six_hour_scientific_trial')
 subprocess.run([SDK,str(ROOT/'launch_science_agent.py'),'science'],check=True)
 record('host_trial_finished_check_run_evidence')
except Exception as e:
 record('stopped_on_failure',error=type(e).__name__+': '+str(e));raise
