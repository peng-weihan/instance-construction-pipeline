from pathlib import Path
import asyncio,json,shutil,sys
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');out=ROOT/'finance-pilot-r2';F=out/'framework'
sys.path[:0]=[str(F),str(F/'sdk')]
from edgebench_harbor.restler_scorer import DockerScorer
async def main():
 task=out/'task';profile=json.loads((task/'pipeline-profile.json').read_text());image=json.loads((out/'images.json').read_text())['verifier']['image_id']
 src=ROOT/'finance-reuse-controls-r3-extra';old=json.loads((src/'report.json').read_text());dest=out/'scorer-controls';dest.mkdir()
 report={'kind':'actual_new_image_and_scorer_controls','image_id':image,'status':'running','results':{},'model_runs':0,'formal_native_harbor_controls':False}
 def save():(dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save();scorer=DockerScorer(task,image,600);sem=asyncio.Semaphore(2)
 async def check(name):
  async with sem:
   folder=dest/name;snapshot=folder/'snapshot';submission=snapshot/profile['submission_root'].lstrip('/');submission.mkdir(parents=True)
   if name=='episode_guard':
    shutil.copytree(src/'starter/submission',submission,dirs_exist_ok=True)
    p=submission/'policy.py';p.write_text(p.read_text()+"\nfrom pathlib import Path\n_base_initialize=initialize\ndef initialize(metadata):\n p=Path('/work/episode_marker')\n if p.exists():raise RuntimeError('earlier episode file leaked into this episode')\n p.write_text('current episode only')\n return _base_initialize(metadata)\n")
    expected=old['results']['starter']
   else:shutil.copytree(src/name/'submission',submission,dirs_exist_ok=True);expected=old['results'][name]
   r,seconds=await scorer.grade(snapshot,folder/'grading')
   assert r['valid']==expected['valid'] and abs(r['score']-expected['score'])<1e-7,(name,r['score'],r['valid'])
   report['results'][name]={'score':r['score'],'valid':r['valid'],'seconds':seconds,'raw_metrics':r['raw_metrics']};save();print(name,r['score'],r['valid'],flush=True)
 try:
  await asyncio.gather(*(check(n) for n in ['reference','episode_guard','starter','equal_weight','poor_tail','private_read','empty']))
  report.update(status='completed',passed=True,cross_episode_cache_guard_passed=True);save()
 except Exception as exc:report.update(status='failed',passed=False,error=str(exc));save();raise
asyncio.run(main())
