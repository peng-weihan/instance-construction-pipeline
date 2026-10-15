import asyncio,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path('/ws/users/raymone/edgebench/restler-agent-001');F=ROOT/'framework-r2';TASK=ROOT/'task-r2'
sys.path[:0]=[str(F),str(F/'sdk')]
from edgebench_harbor.restler_scorer import DockerScorer

async def main():
 image=json.loads((ROOT/'images-r2.json').read_text())['verifier']['image_id']
 out=ROOT/'controls-r2';out.mkdir(exist_ok=False)
 reference=TASK/'environment/public/repo/restler'
 jobs=[]
 for name in ['reference','starter','empty','partial_replay','partial_leases']:
  snap=out/name/'snapshot';sub=snap/'home/workspace/restler-resilient/submission';sub.mkdir(parents=True)
  if name!='empty':shutil.copytree(reference,sub,dirs_exist_ok=True)
  if name not in ('empty','starter'):shutil.copytree(TASK/'solution/reference',sub,dirs_exist_ok=True)
  if name=='partial_replay':
   with (sub/'engine/tools/replay_execution.py').open('a') as stream:stream.write('\ndef replay(records, policy):\n    return []\n')
  if name=='partial_leases':
   with (sub/'engine/core/execution_policy.py').open('a') as stream:stream.write('\nLeaseGraph.cleanup = lambda self, delete, context: ([], [])\n')
  jobs.append((name,snap))
 results={}
 for name,snap in jobs:
  report,seconds=await DockerScorer(TASK,image).grade(snap,out/name/'grade')
  results[name]={'score':report['score'],'valid':report['valid'],'seconds':seconds,'pass_rate':report['pass_rate']}
  (out/'report.json').write_text(json.dumps({'status':'running','results':results},indent=2)+'\n')
  print(name,results[name],flush=True)
 passed=results['reference']['score']==1 and results['starter']['score']==0 and results['empty']['score']==0 and all(0<results[n]['score']<1 for n in ('partial_replay','partial_leases'))
 report={'kind':'exact_offline_docker_score_controls','passed':passed,'results':results,'native_harbor_controls':False,'model_runs':0,'image_id':image,'task_hashes':{str(p.relative_to(TASK)):hashlib.sha256(p.read_bytes()).hexdigest() for p in TASK.rglob('*') if p.is_file()}}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 return 0 if passed else 1

if __name__=='__main__':sys.exit(asyncio.run(main()))
