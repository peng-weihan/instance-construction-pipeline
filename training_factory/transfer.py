"""Audit already-frozen teacher solvers on originals; never feed results to teachers."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from pathlib import Path
import shutil

from .calibrate import write_json
from .contract import official_score
from .pack import snapshot
from .teacher import grade


def audit(run, original_calibration, output, budget=1):
    run, output = Path(run), Path(output)
    output.mkdir(parents=True,exist_ok=False)
    task = output/'author_only_original_task'
    source = Path('data/routing_alignment/original_judge/internal/cases')
    shutil.copytree(Path('data/routing_alignment/original_work/tools'),task/'work/tools')
    shutil.copytree(source/'raw',task/'judge/feedback')
    calibrated = json.loads((Path(original_calibration)/'results.json').read_text())
    refs = [{'name':r['name'],'filename':r['name']+'.txt','family':r['family'],'reference':r['reference']}
            for r in calibrated['records']]
    write_json(task/'judge/cases.json',{'feedback':refs})
    write_json(task/'manifest.json',{'judge_sha256':snapshot(task/'judge')})
    with (source/'bks_snapshot.csv').open() as stream:
        published = {r['name']:{'valid':True,'nv':int(r['nv']),'td':float(r['td'])} for r in csv.DictReader(stream)}
    jobs = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for episode in sorted((run/'episodes').iterdir()):
            quality_path = episode/'quality.json'
            if not quality_path.exists():
                raise ValueError('Every teacher must finish and freeze before any transfer audit starts')
            quality = json.loads(quality_path.read_text())
            if not quality['checks']['code_changed']:
                continue
            files = json.loads((episode/'final_submission.json').read_text())
            jobs.append((episode.name, executor.submit(grade,task,files,output/episode.name,budget=budget)))
        reports=[]
        for name,job in jobs:
            result=job.result()
            published_scores=[official_score(row,published[row['name']]) for row in result['details']]
            report={'episode':name,'per_case_budget_seconds':budget,'valid_cases':result['valid_cases'],
                'total_cases':result['total_cases'],'raw_score_same_pyvrp_anchor_budget':result['raw_score'],
                'raw_score_official_bks_table':sum(published_scores)/len(published_scores),
                'source_sha256':result['source_sha256'],'teacher_received_this_result':False,
                'family_scores':{f:sum(s for r,s in zip(result['details'],published_scores) if r['family']==f)/
                    sum(r['family']==f for r in result['details']) for f in ['C1','C2','R1','R2','RC1','RC2']}}
            reports.append(report)
    summary={'reports':reports,'original_inputs_used_for_sft':False,'models_called':0,
        'interpretation':'Frozen source transfer at matched per-case runtime. Published BKS is an original judge anchor, '
                         'not a newly verified solution certificate; this is not the 12-hour benchmark protocol.'}
    write_json(output/'summary.json',summary)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--original-calibration',default='runs/original-matched-budget-001')
    parser.add_argument('--output',required=True)
    parser.add_argument('--budget',type=int,default=1)
    args=parser.parse_args()
    audit(args.run,args.original_calibration,args.output,args.budget)
