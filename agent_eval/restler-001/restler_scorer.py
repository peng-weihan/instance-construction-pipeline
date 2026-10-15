"""Grade immutable cloud snapshots using the separately built offline judge."""
import asyncio,json,time,uuid
from pathlib import Path

class DockerScorer:
 def __init__(self,task_dir,image,timeout_sec=300):
  self.task_dir=Path(task_dir);self.image=image;self.timeout_sec=timeout_sec;self.job_wall_timeout_sec=timeout_sec+120
  if not image.startswith('sha256:'):raise ValueError('immutable judge image ID required')
 async def grade(self,snapshot,folder):
  folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
  submission=Path(snapshot)/'home/workspace/restler-resilient/submission'
  if not submission.is_dir():
   submission=folder/'empty-submission';submission.mkdir(exist_ok=True)
  logs=folder/'verifier';logs.mkdir(exist_ok=True)
  name='edge-raymone-grade-'+uuid.uuid4().hex[:12]
  argv=['docker','run','--name',name,'--rm','--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=12g','--cpus','2','--memory','12g','--pids-limit','512','--cap-drop','ALL']
  for cap in ['SYS_ADMIN','SETUID','SETGID','SETFCAP','CHOWN','DAC_OVERRIDE','FOWNER','KILL']:argv+=['--cap-add',cap]
  for opt in ['seccomp=unconfined','apparmor=unconfined','systempaths=unconfined']:argv+=['--security-opt',opt]
  argv+=['--mount',f'type=bind,source={submission.resolve()},target=/submission,readonly','--mount',f'type=bind,source={logs.resolve()},target=/logs/verifier',self.image]
  began=time.monotonic();process=None
  try:
   process=await asyncio.create_subprocess_exec(*argv,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
   out,err=await asyncio.wait_for(process.communicate(),self.timeout_sec)
   (folder/'test-stdout.txt').write_bytes(out);(folder/'test-stderr.txt').write_bytes(err)
   (folder/'execution.json').write_text(json.dumps({'command':argv,'exit_code':process.returncode,'elapsed_seconds':time.monotonic()-began}))
   if process.returncode:raise RuntimeError('offline verifier failed; see private stderr')
   report=json.loads((logs/'score.json').read_text());reward=float((logs/'reward.txt').read_text())
   if report.get('status')!='scored' or report.get('valid') is not True or reward!=report['score'] or not 0<=reward<=1:raise RuntimeError('reward/report contract mismatch')
   (folder/'feedback.json').write_text(json.dumps(report,indent=2)+'\n')
   return report,time.monotonic()-began
  finally:
   clean=await asyncio.create_subprocess_exec('docker','rm','-f',name,stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL);await clean.wait()
   if process is not None and process.returncode is None:process.kill();await process.wait()
