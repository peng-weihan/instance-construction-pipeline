"""Score saved public-only author-solver checkpoints after inference finishes.
These are optimizer checkpoints, not agent trajectories or a six-hour run.
"""
import argparse
import json
import sys
import time
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--task',required=True);parser.add_argument('--run',required=True)
args=parser.parse_args();task=Path(args.task).resolve();run=Path(args.run).resolve()
sys.path.insert(0,str(task/'verifier'));sys.dont_write_bytecode=True
from grader import grade

progress=[json.loads(line) for line in (run/'progress.jsonl').read_text().splitlines()]
rows=[];best={suite:0 for suite in ['public','feedback','audit']}
for checkpoint in progress:
    row=dict(checkpoint);row['scores']={};row['best_so_far']={}
    for suite in best:
        feedback=grade(run/checkpoint['checkpoint'],suite)
        row['scores'][suite]=feedback['score'];best[suite]=max(best[suite],feedback['score'])
        row['best_so_far'][suite]=best[suite]
    rows.append(row)
final={suite:grade(run,suite) for suite in best}
repeat={suite:grade(run,suite)['score'] for suite in best}
report={'scope':'public-only author inverse solver; hidden feedback evaluated retrospectively, never used by solver',
        'model_runs':0,'docker_executed':False,'six_hour_runs':0,'checkpoints':rows,'final':final,
        'repeat_score_absolute_difference':{suite:abs(final[suite]['score']-repeat[suite]) for suite in best},
        'not_a_six_hour_agent_curve':True}
(run/'scored_checkpoints.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({'checkpoints':len(rows),'first_scores':rows[0]['scores'],'final_scores':{k:v['score'] for k,v in final.items()},
                  'repeat_differences':report['repeat_score_absolute_difference']},indent=2))
