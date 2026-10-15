"""One structured scoring authority, preserving genuine invalid submissions."""
import json,sys,traceback
from pathlib import Path
from runtime import SubmissionError,invalid
from grader import grade
try:
    report=grade(Path('/submission'),'feedback')
    report['pass_rate']=sum(c['pass'] for c in report['checks'])/max(1,len(report['checks']))
except SubmissionError as error:
    report=invalid(str(error));report['pass_rate']=0
except Exception as error:
    print(json.dumps({'status':'verifier_error','error':type(error).__name__,'summary':str(error)[:500]}));traceback.print_exc();sys.exit(2)
assert type(report['valid']) is bool and 0<=report['score']<=1
assert report['valid'] or report['score']==0
logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True)
(logs/'score.json').write_text(json.dumps(report,allow_nan=False,indent=2)+'\n')
(logs/'reward.txt').write_text(str(report['score'])+'\n')
print(json.dumps(report,allow_nan=False))
