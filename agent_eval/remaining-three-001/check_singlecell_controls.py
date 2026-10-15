"""Actual new-image controls plus the real public CPU baseline, no model calls."""
from pathlib import Path
import asyncio,json,shutil,subprocess,sys
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OUT=ROOT/'science-pilot';F=OUT/'framework'
sys.path[:0]=[str(F),str(F/'sdk')]
from edgebench_harbor.restler_scorer import DockerScorer
async def main():
 task=OUT/'task';profile=json.loads((task/'pipeline-profile.json').read_text());image=json.loads((OUT/'images.json').read_text())['verifier']['image_id']
 dest=OUT/'scorer-controls';dest.mkdir()
 report={'kind':'actual_offline_singlecell_controls','status':'running','passed':False,'image_id':image,'model_runs':0,'formal_native_harbor_controls':False,'results':{}}
 def save():(dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save()
 names=['oracle','reference','frozen_reference','starter','uint64','empty','bad_shape','bad_class','archive_disguised','private_symlink']
 for name in names:(dest/name/'snapshot'/profile['submission_root'].lstrip('/')).mkdir(parents=True)
 shutil.copyfile(ROOT/'singlecell_cross_site_graph_lab-r2/reference-predictions/predictions.npy',dest/'frozen_reference/snapshot'/profile['submission_root'].lstrip('/')/'predictions.npy')
 # Trusted fixture creation stays in the judge; target never receives these files.
 code='''import numpy as np
from pathlib import Path
root=Path('/controls');rel='home/workspace/cellgraph/submission/predictions.npy'
truth=np.load('/judge/private/target_labels.npy')
np.save(root/'oracle/snapshot'/rel,truth)
starter=np.load('/judge/public/submission/predictions.npy');np.save(root/'starter/snapshot'/rel,starter)
np.save(root/'uint64/snapshot'/rel,starter.astype(np.uint64))
np.save(root/'bad_shape/snapshot'/rel,starter[:-1])
np.save(root/'bad_class/snapshot'/rel,np.full(len(starter),36,dtype=np.int64))
with (root/'archive_disguised/snapshot'/rel).open('wb') as f:np.savez(f,pred=starter)
(root/'private_symlink/snapshot'/rel).symlink_to('/judge/private/target_labels.npy')
'''
 subprocess.run(['docker','run','--rm','--network','none','--read-only','--mount','type=bind,source='+str(dest)+',target=/controls','--entrypoint','/opt/runtime/venv/bin/python',image,'-c',code],check=True)
 baseline=dest/'reference/snapshot'/profile['submission_root'].lstrip('/')
 with (dest/'baseline-stdout.txt').open('w') as stdout,(dest/'baseline-stderr.txt').open('w') as stderr:
  subprocess.run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=2g','--cpus','4','--memory','12g','--mount','type=bind,source='+str(baseline)+',target=/out','--entrypoint','/opt/runtime/venv/bin/python',image,'/judge/public/baseline.py','/judge/public','/out'],stdout=stdout,stderr=stderr,timeout=600,check=True)
 scorer=DockerScorer(task,image,600)
 try:
  for name in names:
   folder=dest/name;r,seconds=await scorer.grade(folder/'snapshot',folder/'grading')
   valid=name in ['oracle','reference','frozen_reference','starter','uint64']
   assert r['valid']==valid,(name,r)
   if name=='oracle':assert r['score']==1
   elif name=='frozen_reference':assert abs(r['score']-.3885168478386856)<1e-12,r['score']
   elif name=='reference':assert 0<r['score']<1,r['score']
   elif not valid:assert r['score']==0
   if name=='uint64':assert r['score']==report['results']['starter']['score']
   report['results'][name]={'score':r['score'],'valid':r['valid'],'seconds':seconds};save();print(name,r['score'],r['valid'],flush=True)
  # Same immutable prediction, five fresh stateless judge containers.
  repeats=[]
  for index in range(5):
   r,_=await scorer.grade(dest/'reference/snapshot',dest/('repeat-'+str(index)))
   repeats.append(r['score'])
  assert len(set(repeats))==1
  report.update(passed=True,status='completed',five_same_snapshot_scores=repeats)
  save()
 except Exception as e:
  report.update(status='failed',error=str(e));save();raise
asyncio.run(main())
