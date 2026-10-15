"""No build: score fresh offline containers using a pre-existing owned runtime.

Bind the complete newly frozen judge tree read-only. This checks runtime scoring,
not a rebuild from the delivered Dockerfiles or native Harbor oracle.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,time,uuid
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
def main(kind,revision,repeats,extra=False):
 task=ROOT/(kind+'-task-'+revision);out=ROOT/(kind+'-reuse-controls-'+revision+('-extra' if extra else ''));out.mkdir()
 judge=out/'judge';judge.mkdir()
 for folder in ['public','private','verifier']:shutil.copytree(task/folder,judge/folder)
 shutil.copyfile(ROOT/'judge_entry.py',judge/'verifier/judge_entry.py')
 image_id=subprocess.check_output(['docker','image','inspect','edge-raymone-game:initial','--format','{{.Id}}'],text=True).strip()
 names=['reference','starter','empty'] if kind=='finance' else ['reference','starter','economy_only','attack_only','invalid_policy','empty']
 if kind=='finance' and extra:names=['reference','starter','equal_weight','poor_tail','private_read','empty']
 names += ['reference_repeat_'+str(i) for i in range(2,repeats+1)]
 report={'kind':'direct_offline_docker_runtime_reuse','runtime_image_id':image_id,'source_task':str(task),
         'source_dockerfile_rebuilt':False,'native_harbor_verified':False,'model_runs':0,'results':{},'status':'running'}
 binary=(ROOT/('game-entropy-build-004' if revision=='r4' else 'game-entropy-build-002')/'wesnoth') if kind=='game' and revision in ['r3','r4'] else None
 if binary:report['patched_binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
 def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save()
 try:
  for name in names:
   folder=out/name;sub=folder/'submission';sub.mkdir(parents=True);logs=folder/'verifier';logs.mkdir()
   if name!='empty':
    src=task/'solution' if name.startswith('reference') else task/'public/submission'
    if kind=='finance':
     shutil.copytree(src,sub,dirs_exist_ok=True)
     if name=='equal_weight':
      p=sub/'policy.py';p.write_text(p.read_text().replace('target_w=opt.x','target_w=np.full(n,.5/n)'))
     elif name=='poor_tail':
      p=sub/'policy.py';p.write_text(p.read_text().replace("'q05_daily':q", "'q05_daily':0.0"))
     elif name=='private_read':(sub/'policy.py').write_text("def initialize(metadata):\n    return open('/judge/private/data/source_prices.csv').read()\n")
    else:
     shutil.copyfile(src/'policy.lua',sub/'policy.lua')
     if name=='invalid_policy':(sub/'policy.lua').write_text('return {decide=function(state) return {index=-1,priority=110000} end}\n')
     elif name in ['economy_only','attack_only']:
      old=ROOT/'game-controls-r1'/name/'submission/policy.lua';shutil.copyfile(old,sub/'policy.lua')
   cpus=sorted(os.sched_getaffinity(0));dedicated=cpus[2:4] if len(cpus)>=4 else cpus[:2]
   cname='edge-raymone-reuse-'+uuid.uuid4().hex[:12]
   cmd=['docker','run','--rm','--name',cname,'--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=4g','--cpus','2',
        '--cpuset-cpus',','.join(map(str,dedicated)),'--memory','8g','--pids-limit','256','--cap-drop','ALL']
   for cap in ['SYS_ADMIN','SETUID','SETGID','SETFCAP','CHOWN','DAC_OVERRIDE','FOWNER','KILL']:cmd+=['--cap-add',cap]
   for option in ['seccomp=unconfined','apparmor=unconfined','systempaths=unconfined']:cmd+=['--security-opt',option]
   for src,dest in [(judge,'/judge'),(sub,'/submission')]:cmd+=['--mount',f'type=bind,source={src},target={dest},readonly']
   if binary:cmd+=['--mount',f'type=bind,source={binary},target=/opt/runtime/wesnoth/bin/wesnoth,readonly']
   cmd+=['--mount',f'type=bind,source={logs},target=/logs/verifier','--entrypoint','/opt/runtime/venv/bin/python',image_id,'/judge/verifier/judge_entry.py']
   start=time.monotonic()
   try:
    with (folder/'stdout.txt').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
     proc=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=650)
    if proc.returncode:raise RuntimeError(f'{name}: verifier exit {proc.returncode}; inspect stderr')
    score=json.loads((logs/'score.json').read_text());assert float((logs/'reward.txt').read_text())==score['score']
    report['results'][name]={'seconds':time.monotonic()-start,**score};save();print(name,score['score'],score['valid'],flush=True)
   finally:subprocess.run(['docker','rm','-f',cname],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  ref=[r for n,r in report['results'].items() if n.startswith('reference')]
  report['reference_deterministic']=all((r['score'],r['raw_metrics'])==(ref[0]['score'],ref[0]['raw_metrics']) for r in ref)
  report['passed']=report['results']['empty']['score']==0 and ref[0]['valid'] and ref[0]['score']>0
  if kind=='game':report['passed'] &= report['results']['invalid_policy']['score']==0 and not report['results']['invalid_policy']['valid']
  report.update(status='completed',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
 except Exception as exc:report.update(status='infrastructure_failure',error=str(exc));save();raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['game','finance']);p.add_argument('revision');p.add_argument('--repeats',type=int,default=1)
 p.add_argument('--extra',action='store_true');a=p.parse_args();main(a.kind,a.revision,a.repeats,a.extra)
