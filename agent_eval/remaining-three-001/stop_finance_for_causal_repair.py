"""Stop only the owned faulty finance pilot; preserve all existing evidence."""
from pathlib import Path
import datetime,json,os,sys
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');pilot=ROOT/'finance-pilot';run=pilot/'run-6h-001'
sys.path.insert(0,str(pilot/'framework/sdk'))
from sandbox_smoke import connection,api_options
from e2b import Sandbox
os.environ['TBSCI_E2B_CREDENTIAL_FILE']='/ws/users/wcgu/aliyun-sandbox-runtime/private/connection.json'
probe=json.loads((ROOT/'finance-case-state-probe.json').read_text());assert probe['cross_episode_file_leak']
paths=list((run/'jobs/trial').glob('*/aliyun-*.json'));assert len(paths)==1
state=json.loads(paths[0].read_text());assert not state['destroyed']
box=Sandbox.connect(state['sandbox_id'],timeout=3600,**api_options(connection()))
result=box.commands.run('/usr/bin/python3 -I /opt/edgebench-runtime/learning_guardian.py stop',user='root',timeout=30)
assert result.exit_code==0;stop=json.loads(result.stdout);assert not stop['surviving_learning_processes']
record={'reason':'confirmed_cross_episode_file_leak_in_grader','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'evidence':str(ROOT/'finance-case-state-probe.json'),'owned_run':str(run),'trusted_stop':stop,'formal_six_hour_completed':False,
 'history_and_trajectory_retained':True,'difficulty_early_stop':False}
(run/'grading-fault-stop.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'stopped_owned_finance_pilot':True,'reason':record['reason'],'learning_elapsed_seconds':stop['actual_all_stop_dispatched_elapsed_sec']}))
