from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2];src=ROOT/'samples/remaining-three-built-001/finance-task-r2';dst=src.with_name('finance-task-r3');shutil.copytree(src,dst)
for folder in ['verifier','environment/verifier/verifier']:
 p=dst/folder/'runtime.py';text=p.read_text().replace("if not src.is_dir(): raise SubmissionError('submission must be a directory')", "if not src.is_dir(): raise SubmissionError('submission must be a directory')\n    dst.mkdir(parents=True,exist_ok=True)")
 p.write_text(text)
 p=dst/folder/'grader.py';text=p.read_text().replace("    c=scoring_constants();cases=", "    if not (submission/'policy.py').is_file():raise SubmissionError('policy.py missing')\n    c=scoring_constants();cases=")
 p.write_text(text)
(dst/'REVISION.json').write_text(json.dumps({'previous_revision':'finance-task-r2','change':'missing policy is invalid submission; empty snapshot directory exists',
 'score_constants_unchanged':True,'real_prices_unchanged':True,'redistribution_rights':'not_confirmed'},indent=2)+'\n')
print(dst)
