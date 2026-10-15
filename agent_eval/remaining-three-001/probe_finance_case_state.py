"""Check whether independent finance episodes can pass files to each other."""
from pathlib import Path
import json,subprocess,uuid
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');pilot=ROOT/'finance-pilot'
image=json.loads((pilot/'images.json').read_text())['verifier']['image_id']
code="""from pathlib import Path
import shutil,json
from runtime import JsonWorker,workdir,ROOT
records=[]
with workdir() as tmp:
 w=Path(tmp);(w/'submission').mkdir();shutil.copyfile(ROOT/'verifier/policy_worker.py',w/'policy_worker.py')
 (w/'submission/policy.py').write_text("from pathlib import Path\\ndef initialize(metadata):\\n return {}\\ndef decide(history,state):\\n p=Path('/work/episode_marker');seen=p.exists();p.write_text('written by previous episode');return {'previous_episode_file_visible':seen}\\n")
 for i in range(2):
  worker=JsonWorker(w,['python','policy_worker.py'],readonly=['policy_worker.py','submission'])
  try:
   init=worker.exchange({'op':'initialize','metadata':{}})
   answer=worker.exchange({'op':'decide','history':{},'state':{}})
   records.append({'episode':i,'initialize':init,'answer':answer})
  finally:worker.close()
print(json.dumps(records))
"""
name='edge-raymone-case-state-'+uuid.uuid4().hex[:10]
argv=['docker','run','--rm','--name',name,'--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=1g','--cpus','2','--memory','4g','--pids-limit','256','--cap-drop','ALL']
for cap in ['SYS_ADMIN','SETUID','SETGID','SETFCAP','CHOWN','DAC_OVERRIDE','FOWNER','KILL']:argv+=['--cap-add',cap]
for option in ['seccomp=unconfined','apparmor=unconfined','systempaths=unconfined']:argv+=['--security-opt',option]
argv+=['--entrypoint','/opt/runtime/venv/bin/python',image,'-c',code]
result=subprocess.run(argv,capture_output=True,text=True,timeout=120)
report={'image':image,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
if not result.returncode:
 report['records']=json.loads(result.stdout);report['cross_episode_file_leak']=report['records'][1]['answer'].get('previous_episode_file_visible') is True
(ROOT/'finance-case-state-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
