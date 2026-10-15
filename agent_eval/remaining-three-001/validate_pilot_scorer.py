"""Exercise the exact new asynchronous scorer before its full agent run."""
from pathlib import Path
import argparse,asyncio,json,shutil,sys
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
async def main(kind):
 out=ROOT/(kind+'-pilot');F=out/'framework';sys.path[:0]=[str(F),str(F/'sdk')]
 from edgebench_harbor.restler_scorer import DockerScorer
 task=out/'task';profile=json.loads((task/'pipeline-profile.json').read_text());image=json.loads((out/'images.json').read_text())['verifier']['image_id']
 source=ROOT/('game-reuse-controls-r4' if kind=='game' else 'finance-reuse-controls-r3-extra')
 old=json.loads((source/'report.json').read_text());controls=out/'scorer-controls';controls.mkdir()
 report={'kind':'bound_pilot_scorer_actual_offline_controls','image_id':image,'formal_native_harbor_controls':False,'model_runs':0,'results':{},'status':'running'}
 def save():(controls/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save();scorer=DockerScorer(task,image,600)
 names=['reference','starter','economy_only','attack_only','invalid_policy','empty'] if kind=='game' else ['reference','starter','equal_weight','poor_tail','private_read','empty']
 try:
  for name in names:
   folder=controls/name;snapshot=folder/'snapshot';submission=snapshot/profile['submission_root'].lstrip('/');submission.mkdir(parents=True)
   shutil.copytree(source/name/'submission',submission,dirs_exist_ok=True)
   result,seconds=await scorer.grade(snapshot,folder/'grading')
   expected=old['results'][name]
   if result['valid']!=expected['valid'] or abs(result['score']-expected['score'])>1e-7:raise RuntimeError('new image/scorer does not reproduce '+name)
   report['results'][name]={'score':result['score'],'valid':result['valid'],'seconds':seconds,'raw_metrics':result['raw_metrics']};save();print(name,result['score'],result['valid'],flush=True)
  report.update(status='completed',passed=True,old_components_reproduced=True);save()
 except Exception as exc:report.update(status='failed',passed=False,error=str(exc));save();raise
if __name__=='__main__':p=argparse.ArgumentParser();p.add_argument('kind',choices=['game','finance']);asyncio.run(main(p.parse_args().kind))
