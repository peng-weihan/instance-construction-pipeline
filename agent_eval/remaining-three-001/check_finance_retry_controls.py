"""Same judge and score, through the new failure-recovery wrapper."""
from pathlib import Path
import asyncio,json,shutil,sys
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OLD=ROOT/'finance-pilot-r2';OUT=ROOT/'finance-pilot-r3';F=OUT/'framework'
sys.path[:0]=[str(F),str(F/'sdk')]
from edgebench_harbor.restler_scorer import DockerScorer
async def main():
 profile=json.loads((OUT/'task/pipeline-profile.json').read_text());image=json.loads((OUT/'images.json').read_text())['verifier']['image_id']
 previous=json.loads((OLD/'scorer-controls/report.json').read_text());dest=OUT/'scorer-controls';dest.mkdir()
 report={'status':'running','passed':False,'kind':'actual_finance_retry_controls','image_id':image,'model_calls':0,'formula_and_hidden_data_unchanged':True,'results':{}}
 def save():(dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save();scorer=DockerScorer(OUT/'task',image,600)
 for name in ['starter','private_read','empty','previous_startup_fault_snapshot']:
  folder=dest/name;source=OLD/'run-6h-001/evaluation/submissions/agent-66/snapshot' if name=='previous_startup_fault_snapshot' else OLD/'scorer-controls'/name/'snapshot'
  shutil.copytree(source,folder/'snapshot',symlinks=True)
  r,seconds=await scorer.grade(folder/'snapshot',folder/'grading')
  if name!='previous_startup_fault_snapshot':
   expected=previous['results'][name];assert r['valid']==expected['valid'] and abs(r['score']-expected['score'])<1e-10
  report['results'][name]={'score':r['score'],'valid':r['valid'],'seconds':seconds};save();print(name,r['score'],r['valid'],flush=True)
 report.update(passed=True,status='completed');save()
try:asyncio.run(main())
except Exception:
 raise
