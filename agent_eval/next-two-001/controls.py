"""Run real isolated grading controls; never synthesize scores on infra failure."""
import argparse,datetime,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path('/ws/users/raymone/edgebench/next-two-001')
IDS={'packing':'industrial_nesting_improvement','lean':'brownian_multibranch_proofs'}
def main(kind,revision):
 source=ROOT/(kind+('-task-r5' if kind=='packing' else '-task-r3'))
 out=ROOT/(kind+'-controls-'+revision);out.mkdir(exist_ok=False)
 context=out/'judge';context.mkdir()
 runtime=(source/'verifier/runtime.py').read_text().replace("'--unshare-all','--die-with-parent'","'--unshare-all','--share-net','--uid','2000','--gid','2000','--die-with-parent'")
 if kind=='lean' and "'--setenv','LEAN_NUM_THREADS','1'" not in runtime:runtime=runtime.replace("'--setenv','OMP_NUM_THREADS','1'", "'--setenv','LEAN_NUM_THREADS','1','--setenv','OMP_NUM_THREADS','1'")
 if kind=='lean':runtime=runtime.replace('def limits(cpu=1200,memory_gb=8):','def limits(cpu=1200,memory_gb=64):')
 (context/'runtime.py').write_text(runtime)
 shutil.copyfile(ROOT/'judge_entry.py',context/'judge_entry.py')
 shutil.copyfile(source/'verifier/grader.py',context/'grader.py')
 (context/'test.sh').write_text('#!/bin/sh\nset -eu\nunset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD\nexec /opt/runtime/venv/bin/python /judge/verifier/judge_entry.py\n')
 base=subprocess.check_output(['docker','image','inspect','edge-raymone-'+kind+':initial','--format','{{.Id}}'],text=True).strip()
 (context/'Dockerfile').write_text('FROM edge-raymone-'+kind+':initial\nCOPY runtime.py judge_entry.py grader.py /judge/verifier/\nCOPY test.sh /tests/test.sh\nRUN chmod 700 /judge/private\nENTRYPOINT ["/bin/sh", "/tests/test.sh"]\n')
 image='edge-raymone-'+kind+':controls'+revision
 with (out/'build.log').open('wb') as log:subprocess.run(['docker','build','--network','none','-t',image,str(context)],stdout=log,stderr=subprocess.STDOUT,check=True)
 image_id=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
 report={'kind':'direct_offline_docker_controls','task':IDS[kind],'image_id':image_id,'base_image_id':base,'status':'running','native_harbor_verified':False,'model_runs':0,'results':{}}
 def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save()
 names=['reference','starter','empty','partial_covariance','partial_covering'] if kind=='lean' else ['reference','empty','partial_order_filter']
 for name in names:
  folder=out/name;sub=folder/'submission';sub.mkdir(parents=True);logs=folder/'verifier';logs.mkdir()
  if name!='empty':
   if kind=='lean':
    targets=json.loads((source/'public/targets.json').read_text())
    for rel in sorted({t['file'] for t in targets}):
     dst=sub/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/'public/repo'/rel,dst)
    if name=='reference':shutil.copytree(source/'solution/reference',sub,dirs_exist_ok=True)
    elif name.startswith('partial_'):
     group=name.removeprefix('partial_')
     for rel in {t['file'] for t in targets if t['group']==group}:shutil.copyfile(source/'solution/reference'/rel,sub/rel)
   else:
    for rel in ['src/irregular','include/packingsolver/irregular']:shutil.copytree(source/'public/repo'/rel,sub/rel)
    if name=='partial_order_filter':
     rows=json.loads((source/'private/workloads.json').read_text());sizes=[]
     for row in rows:
      if row['split']=='feedback':
       d=json.loads((source/'private/feedback_cases'/(row['id']+'.json')).read_text());sizes.append(sum(i.get('copies',1) for i in d['item_types']))
     threshold=sorted(set(sizes))[len(set(sizes))//2]
     p=sub/'src/irregular/main.cpp';s=p.read_text();needle='const irregular::Output output = optimize(instance, parameters);';assert needle in s
     p.write_text(s.replace(needle,'if (instance.number_of_items() > '+str(threshold)+') return 1;\n        '+needle))
  cname='edge-raymone-'+kind+'-control-'+uuid.uuid4().hex[:10]
  cmd=['docker','run','--rm','--name',cname,'--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=20g','--cpus','2','--memory','28g','--pids-limit','512','--cap-drop','ALL']
  for cap in ['SYS_ADMIN','SETUID','SETGID','SETFCAP','CHOWN','DAC_OVERRIDE','FOWNER','KILL']:cmd+=['--cap-add',cap]
  for opt in ['seccomp=unconfined','apparmor=unconfined','systempaths=unconfined']:cmd+=['--security-opt',opt]
  cmd+=['--mount','type=bind,source='+str(sub)+',target=/submission,readonly','--mount','type=bind,source='+str(logs)+',target=/logs/verifier',image_id]
  began=time.monotonic()
  try:
   with (folder/'stdout.txt').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
    p=subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=2100)
   (folder/'execution.json').write_text(json.dumps({'command':cmd,'exit_code':p.returncode,'seconds':time.monotonic()-began},indent=2))
   if p.returncode:raise RuntimeError(name+' verifier infrastructure failure')
   score=json.loads((logs/'score.json').read_text());reward=float((logs/'reward.txt').read_text())
   assert score['valid'] and score['score']==reward and 0<=reward<=1
   report['results'][name]={'score':reward,'valid':score['valid'],'pass_rate':score['pass_rate'],'seconds':time.monotonic()-began,'raw_metrics':score.get('raw_metrics')};save();print(name,report['results'][name],flush=True)
  finally:subprocess.run(['docker','rm','-f',cname],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 results=report['results'];passed=results['empty']['score']==0
 if kind=='lean':passed=passed and results['reference']['score']==1 and results['starter']['score']==0 and all(0<results[k]['score']<1 for k in ['partial_covariance','partial_covering'])
 else:passed=passed and 0<results['reference']['score']<1 and 0<results['partial_order_filter']['score']<results['reference']['score']
 report.update(status='completed',passed=passed,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
 return 0 if passed else 1
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('kind',choices=IDS);parser.add_argument('--revision',default='001');args=parser.parse_args();raise SystemExit(main(args.kind,args.revision))
