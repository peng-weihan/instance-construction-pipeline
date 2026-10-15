"""Retry only Docker exit125 before judge startup; keep each attempt's evidence."""
import asyncio,json,time
from pathlib import Path
from .singlecell_scorer_base import DockerScorer as BaseScorer

class DockerScorer(BaseScorer):
 async def grade(self,snapshot,folder):
  root=Path(folder);root.mkdir(parents=True,exist_ok=True);began=time.monotonic();attempts=[]
  for attempt in range(3):
   dest=root/('attempt-'+str(attempt+1))
   try:
    report,_=await super().grade(snapshot,dest)
    attempts.append({'attempt':attempt+1,'status':'completed'})
    (root/'attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
    (root/'feedback.json').write_text(json.dumps(report,indent=2)+'\n')
    return report,time.monotonic()-began
   except RuntimeError:
    execution=dest/'execution.json';stderr=dest/'test-stderr.txt'
    code=json.loads(execution.read_text()).get('exit_code') if execution.exists() else None
    error=stderr.read_text().lower() if stderr.exists() else ''
    retryable=code==125 and not (dest/'verifier/score.json').exists() and any(s in error for s in ['failed to create task','cgroup','message bus','cannot connect to the docker daemon'])
    attempts.append({'attempt':attempt+1,'status':'startup_error','docker_exit_code':code,'retryable':retryable})
    (root/'attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
    if not retryable or attempt==2:raise
    await asyncio.sleep(2 if attempt==0 else 5)
