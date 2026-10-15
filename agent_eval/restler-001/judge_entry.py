"""One authority for structured score and Harbor scalar reward."""
import json,sys,traceback
from pathlib import Path
from runtime import SubmissionError,workdir,snapshot,check,result
from grader import grade

logs=Path('/logs/verifier'); logs.mkdir(parents=True,exist_ok=True)
try:
 with workdir() as temporary:
  candidate=Path(temporary)/'submission'
  snapshot(Path('/submission'),candidate)
  report=grade(candidate,'feedback')
except SubmissionError as exc:
 report=result(0,[check('submission_contract',False,str(exc))],valid=True)
except Exception as exc:
 for name in ['reward.txt','reward.json']:(logs/name).unlink(missing_ok=True)
 (logs/'score.json').write_text(json.dumps({'status':'verifier_error','valid':False,'score':None,'error':type(exc).__name__,'summary':str(exc)[:500]}))
 traceback.print_exc();sys.exit(2)
report['pass_rate']=sum(c['pass'] for c in report['checks'])/len(report['checks'])
(logs/'score.json').write_text(json.dumps(report,allow_nan=False)+'\n')
(logs/'reward.txt').write_text(str(report['score'])+'\n')
print(json.dumps(report,allow_nan=False))
