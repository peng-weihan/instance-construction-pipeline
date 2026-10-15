"""Real fresh offline Docker score controls for newly constructed candidates."""
from pathlib import Path
import argparse,datetime,json,os,shutil,subprocess,time,uuid
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
def main(kind,revision):
    task=ROOT/(kind+'-task-'+revision);out=ROOT/(kind+'-controls-'+revision);out.mkdir()
    context=out/'judge';context.mkdir()
    shutil.copytree(task/'verifier',context/'verifier');shutil.copytree(task/'public',context/'public');shutil.copytree(task/'private',context/'private')
    shutil.copyfile(ROOT/'judge_entry.py',context/'verifier/judge_entry.py')
    base='edge-raymone-'+kind+':initial'
    (context/'Dockerfile').write_text('FROM '+base+'\nCOPY verifier /judge/verifier\nCOPY public /judge/public\nCOPY private /judge/private\nENTRYPOINT ["/opt/runtime/venv/bin/python", "/judge/verifier/judge_entry.py"]\n')
    image='edge-raymone-'+kind+':controls-'+revision
    with (out/'build.log').open('wb') as log:subprocess.run(['docker','build','--network','none','-t',image,str(context)],stdout=log,stderr=subprocess.STDOUT,check=True)
    image_id=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
    names=['reference','starter','empty','economy_only','attack_only','invalid_policy'] if kind=='game' else ['reference','starter','empty']
    report={'kind':'direct_offline_docker_controls','task':str(task),'image_id':image_id,'native_harbor_verified':False,'model_runs':0,'results':{},'status':'running'}
    def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    for name in names:
        folder=out/name;submission=folder/'submission';submission.mkdir(parents=True);logs=folder/'verifier';logs.mkdir()
        if name!='empty':
            if kind=='game':
                src=task/('solution/policy.lua' if name=='reference' else 'public/submission/policy.lua');shutil.copyfile(src,submission/'policy.lua')
                if name in ['economy_only','attack_only']:
                    source=(task/'solution/policy.lua').read_text();wrapper="local base=(function()\n"+source+"\nend)()\nreturn {decide=function(state) local filtered={} for _,a in ipairs(state.actions) do "
                    predicate="a.kind=='recruit' or a.kind=='move'" if name=='economy_only' else "a.kind=='attack'"
                    wrapper+="if "+predicate+" then filtered[#filtered+1]=a end end local copied={} for k,v in pairs(state) do copied[k]=v end copied.actions=filtered local answer=base.decide(copied) if answer then local chosen=filtered[answer.index] for i,a in ipairs(state.actions) do if a==chosen then return {index=i,priority=answer.priority} end end end return nil end}\n"
                    (submission/'policy.lua').write_text(wrapper)
                elif name=='invalid_policy':(submission/'policy.lua').write_text('return {decide=function(state) return {index=-1,priority=110000} end}\n')
            elif kind=='finance':
                src=task/'solution' if name=='reference' else task/'public/submission';shutil.copytree(src,submission,dirs_exist_ok=True)
            else:
                src=task/'private/truth.json' if name=='reference' else task/'public/submission/answer.json';shutil.copyfile(src,submission/'answer.json')
        cname='edge-raymone-'+kind+'-controls-'+uuid.uuid4().hex[:12]
        cpus=sorted(os.sched_getaffinity(0));dedicated=cpus[2:4] if len(cpus)>=4 else cpus[:2]
        command=['docker','run','--rm','--name',cname,'--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=4g','--cpus','2','--cpuset-cpus',','.join(map(str,dedicated)),'--memory','8g','--pids-limit','256','--cap-drop','ALL']
        for cap in ['SYS_ADMIN','SETUID','SETGID','SETFCAP','CHOWN','DAC_OVERRIDE','FOWNER','KILL']:command+=['--cap-add',cap]
        for option in ['seccomp=unconfined','apparmor=unconfined','systempaths=unconfined']:command+=['--security-opt',option]
        command+=['--mount','type=bind,source='+str(submission)+',target=/submission,readonly','--mount','type=bind,source='+str(logs)+',target=/logs/verifier',image_id]
        start=time.monotonic()
        try:
            with (folder/'stdout.txt').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:result=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=2700)
            (folder/'execution.json').write_text(json.dumps({'command':command,'exit_code':result.returncode,'seconds':time.monotonic()-start},indent=2)+'\n')
            if result.returncode:raise RuntimeError('verifier infrastructure failure for '+name)
            score=json.loads((logs/'score.json').read_text());reward=float((logs/'reward.txt').read_text());assert reward==score['score']
            report['results'][name]={'score':reward,'valid':score['valid'],'pass_rate':score['pass_rate'],'seconds':time.monotonic()-start,'raw_metrics':score['raw_metrics']};save();print(name,report['results'][name],flush=True)
        finally:subprocess.run(['docker','rm','-f',cname],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    report.update(status='completed',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    report['passed']=report['results']['empty']['score']==0 and report['results']['reference']['valid'] and report['results']['reference']['score']>0
    if kind=='game':report['passed']=report['passed'] and report['results']['invalid_policy']['score']==0
    save();return 0 if report['passed'] else 1
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['game','finance','science']);p.add_argument('revision');a=p.parse_args();raise SystemExit(main(a.kind,a.revision))
