import importlib.metadata,json
from pathlib import Path

root=Path(__file__).resolve().parents[1];batch=root/'samples/long-horizon-built-007';out=root/'runs/local-validation-003'
reports={'software':'runs/local-validation-002/software/report.json','science':'runs/local-validation-001/science/report.json',
         'finance':'runs/local-validation-003/finance/report.json','packing':'runs/local-validation-001/packing/report.json',
         'game':'runs/local-validation-001/game/report.json'}
rows=[]
for category,path in reports.items():
    d=json.loads((root/path).read_text());old=root/d['task'];new=batch/old.name
    files=list((old/'verifier').glob('*.py'))
    if category!='science':files+=list((old/'solution').rglob('*.py'))+list((old/'solution').rglob('*.lua'))
    if category=='game':files+=[old/'public/adapter.lua']
    assert all(p.read_bytes()==(new/p.relative_to(old)).read_bytes() for p in files),category
    rows.append({'category':category,'report':path,'status':d['status'],'checks':len(d['checks']),
                 'passed':sum(c['pass'] for c in d['checks']),'tested_component_files_match_latest':True,'files_compared':len(files)})
finance=json.loads((out/'finance/report.json').read_text())
c=json.loads((batch/'cross_asset_adaptive_allocator/public/scoring_metadata.json').read_text())['constants'];scores={}
for suite in ['public','feedback','audit']:
    records={r['policy']:r['metrics'] for r in finance['records'] if r['suite']==suite}
    ref=records['author_reference'];base=records['fixed_baseline']
    gain=max(0,min(1,(ref['utility']-base['utility'])/c['utility_scale']))
    scores[suite]=c['functional_weight']+c['utility_weight']*gain+c['calibration_weight']/(1+ref['pinball']/c['pinball_scale'])
curve=json.loads((out/'science-inference/scored_checkpoints.json').read_text())
budget=json.loads((out/'science-inference/run_summary.json').read_text())
small=json.loads((out/'science-budget-one/run_summary.json').read_text())
assert budget['evaluations']==budget['evaluation_budget']==200 and small['evaluations']==small['evaluation_budget']==1
summary={'mode':'trusted_author_components_on_macos_arm64','latest_batch':'samples/long-horizon-built-007',
 'docker_executed':False,'model_runs':0,'six_hour_runs':0,'formal_lean_executed':False,'accepted':False,'rows':rows,
 'science_inference':{'budget':budget,'checkpoints':len(curve['checkpoints']),
 'first_feedback_score':curve['checkpoints'][0]['scores']['feedback'],'final_feedback_score':curve['final']['feedback']['score'],
 'final_audit_score':curve['final']['audit']['score'],'repeat_differences':curve['repeat_score_absolute_difference'],
 'trajectory_type':'reference optimizer checkpoints scored retrospectively; not an agent run'},
 'finance_score_recomputed_from_ledger_metrics':scores,
 'difficulty_flags':['science inversion saturates quickly given a finished forward implementation',
 'finance feedback score saturates for the current reference; score scale/baseline need calibration'],
 'dependencies':{p:importlib.metadata.version(p) for p in ['numpy','scipy','shapely','requests','applicationinsights','lupa']}}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(batch/'local_validation.json').write_text(json.dumps({'summary':'../../runs/local-validation-003/summary.json',
 'scope':'trusted component validation, not container or six-hour acceptance','component_results':rows,
 'formal_lean_executed':False,'docker_executed':False,'model_runs':0,'accepted':False},indent=2)+'\n')
print(json.dumps({'checks':sum(r['checks'] for r in rows),'passed':sum(r['passed'] for r in rows),
 'finance_scores_from_ledger':scores,'science_feedback':curve['final']['feedback']['score']},indent=2))
