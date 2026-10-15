"""Match operational difficulty before exposing a task to a teacher.

This is a solver-response screen, not a statistical proof of equality of distributions.
The original pool is used only for aggregate calibration, never as training inputs.
"""
import argparse
import json
from pathlib import Path
import shutil
import statistics

from .calibrate import write_json
from .generator import FAMILIES


def select(pool, original, output, max_family_score_shift=5.0):
    pool, original, output = map(Path,[pool,original,output])
    generated = json.loads((pool/'summary.json').read_text())
    original = json.loads((original/'results.json').read_text())
    if not generated['complete'] or not original['complete']:
        raise ValueError('Both matched-budget calibration runs must be complete')
    output.mkdir(parents=True,exist_ok=False)
    selected, report = [], {}
    for family in FAMILIES:
        targets = sorted([r['short_score'] for r in original['records'] if r['family']==family])
        candidates = [r for r in generated['records'] if r['family']==family and r['accepted']]
        if len(candidates) < 2*len(targets)+1:
            raise ValueError('Insufficient independent candidates')
        splits = {'feedback':[], 'final':[]}
        # Interleave assignment to prevent the first split consuming every scarce hard case.
        for target in targets:
            for split in splits:
                chosen = min(candidates,key=lambda r:(abs(r['short_reference_score']-target),r['name']))
                splits[split].append(chosen)
                candidates.remove(chosen)
        public = min(candidates,key=lambda r:abs(r['short_reference_score']-statistics.mean(targets)))
        selected.extend([public,*splits['feedback'],*splits['final']])
        reference_mean = statistics.mean(targets)
        split_report = {s:{'count':len(rows), 'score_mean':statistics.mean(r['short_reference_score'] for r in rows),
            'score_shift':statistics.mean(r['short_reference_score'] for r in rows)-reference_mean} for s,rows in splits.items()}
        report[family] = {'original_count':len(targets),'original_score_mean':reference_mean,
                         'unselected_mean':statistics.mean(r['short_reference_score'] for r in generated['records'] if r['family']==family),
                         'splits':split_report}
    passed = all(abs(v['score_shift']) <= max_family_score_shift for row in report.values() for v in row['splits'].values())
    for record in selected:
        shutil.copytree(pool/'candidates'/record['name'],output/'candidates'/record['name'])
    for name in ['profiles.json','excluded_original_fingerprints.json','config.json']:
        shutil.copy2(pool/name,output/name)
    write_json(output/'summary.json',{'complete':True,'generated':len(selected),'accepted':len(selected),
        'original_instances_in_training':0,'records':selected,
        'status':'solver_response_matched' if passed else 'difficulty_alignment_failed'})
    write_json(output/'alignment.json',{'passed':passed,'selection_before_teacher':True,
        'maximum_absolute_family_score_shift':max_family_score_shift,'families':report,
        'interpretation':'Mean response to 1000 versus best-of-two 6000 PyVRP iterations, matched per family and split. '
                         'Not equality of joint distributions or matched long-horizon agent difficulty.'})
    print(json.dumps({'passed':passed,'cases':len(selected),'families':report}),flush=True)
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--pool',required=True)
    parser.add_argument('--original',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    select(args.pool,args.original,args.output)
