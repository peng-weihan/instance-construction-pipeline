from pathlib import Path
import argparse,json,subprocess,uuid
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
def main(kind):
 out=ROOT/(kind+'-pilot');image=json.loads((out/'images.json').read_text())['verifier']['image_id']
 worker="import os,json;from pathlib import Path;print(json.dumps({'uid':os.getuid(),'gid':os.getgid(),'judge_visible':Path('/judge').exists(),'status':[x for x in Path('/proc/self/status').read_text().splitlines() if x.startswith(('CapEff:','NoNewPrivs:'))],'routes':Path('/proc/net/route').read_text()}))"
 code="from runtime import run,workdir;\nwith workdir() as work:\n rc,out,err=run(work,['python','-c',"+repr(worker)+"]);print(out);print(err);assert rc==0\n"
 name='edge-raymone-isolation-'+uuid.uuid4().hex[:10]
 command=['docker','run','--rm','--name',name,'--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=1g','--cpus','2','--memory','4g','--pids-limit','256','--cap-drop','ALL']
 for cap in ['SYS_ADMIN','SETUID','SETGID','SETFCAP','CHOWN','DAC_OVERRIDE','FOWNER','KILL']:command+=['--cap-add',cap]
 for option in ['seccomp=unconfined','apparmor=unconfined','systempaths=unconfined']:command+=['--security-opt',option]
 command+=['--entrypoint','/opt/runtime/venv/bin/python',image,'-c',code]
 result=subprocess.run(command,capture_output=True,text=True,timeout=90);report={'image':image,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'passed':False}
 if not result.returncode:
  data=json.loads(result.stdout);report['candidate']=data;report['passed']=data['uid']==2000 and data['gid']==2000 and not data['judge_visible'] and 'CapEff:\t0000000000000000' in data['status'] and len(data['routes'].splitlines())==1
 (out/'isolation.json').write_text(json.dumps(report,indent=2)+'\n');print(kind,report['passed'],flush=True)
 if not report['passed']:raise RuntimeError('actual candidate namespace isolation failed')
if __name__=='__main__':p=argparse.ArgumentParser();p.add_argument('kind',choices=['science']);main(p.parse_args().kind)
