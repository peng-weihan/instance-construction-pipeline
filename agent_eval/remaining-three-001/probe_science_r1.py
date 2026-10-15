"""Actual source/inference checks; kept distinct from Docker and agent evidence."""
from pathlib import Path
import json,sys,time
ROOT=Path(__file__).resolve().parents[2];TASK=ROOT/'samples/remaining-three-built-001/science-task-r1'
OUT=ROOT/'runs/remaining-three-001/science-probe-001';OUT.mkdir()
sys.path.insert(0,str(TASK/'verifier'))
import grader
from runtime import SubmissionError
truth=json.loads((TASK/'private/truth.json').read_text());starter=json.loads((TASK/'public/submission/answer.json').read_text())
variants={'truth':truth,'starter':starter,'low_release':{**starter,**{k:.005 for k in starter if '_rate' in k}},
          'medium_misspecified':{**truth,'capacity':.15,'exchange':.065},
          'inverse_200':json.loads((ROOT/'runs/remaining-three-001/science-inverse-200/answer.json').read_text()),
          'inverse_1200':json.loads((ROOT/'runs/remaining-three-001/science-inverse-1200/answer.json').read_text())}
report={'mode':'trusted_author_host_components','docker_executed':False,'model_runs':0,'records':[]}
for name,p in variants.items():
    folder=OUT/name;folder.mkdir();(folder/'answer.json').write_text(json.dumps(p,indent=2)+'\n')
    for suite in ['public','feedback','audit']:
        start=time.monotonic();score=grader.grade(folder,suite)
        report['records'].append({'control':name,'suite':suite,'seconds':time.monotonic()-start,'feedback':score})
        print(name,suite,score['score'],flush=True)
nop=OUT/'nop';nop.mkdir()
try:grader.grade(nop,'feedback');report['missing_answer_rejected']=False
except SubmissionError:report['missing_answer_rejected']=True
report['truth_matches_hidden']=all(r['feedback']['score']>1-1e-10 for r in report['records'] if r['control']=='truth' and r['suite']!='public')
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
