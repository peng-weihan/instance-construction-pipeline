"""Trusted host screen of genuine strategy improvements; not container acceptance."""
from pathlib import Path
import importlib.util,json,sys,time
ROOT=Path(__file__).resolve().parents[2]
TASK=ROOT/'samples/remaining-three-built-001/finance-task-r1'
OUT=ROOT/'runs/remaining-three-001/finance-probe-001';OUT.mkdir()
sys.path.insert(0,str(TASK/'verifier'))
import grader
from ledger import simulate
from runtime import scoring_constants

text=(TASK/'public/baseline_policy.py').read_text()
variants={
 'baseline':text,
 'responsive':text.replace('r[-126:]','r[-42:]').replace('*252,-.15,.20)*.25','*252,-.15,.20)*.6').replace('5*252*','2*252*'),
 'slow':text.replace('r[-126:]','r[-252:]').replace('*252,-.15,.20)*.25','*252,-.15,.20)*.1'),
 'trend':text.replace('*252,-.15,.20)*.25','*252,-.15,.20)*1.0').replace('5*252*','1*252*'),
}
modules={}
for name,source in variants.items():
 p=OUT/(name+'.py');p.write_text(source);spec=importlib.util.spec_from_file_location('probe_'+name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);modules[name]=m
cases=json.loads((TASK/'private/episodes.json').read_text());c=scoring_constants();records=[];started=time.monotonic()
def save():
 report={'mode':'trusted_author_host_strategy_screen','docker_executed':False,'model_runs':0,'records':records,'elapsed_seconds':time.monotonic()-started}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
for case in cases:
 prices,dates,start,assets=grader.episode(case)
 mandate={**json.loads((TASK/'public/mandate.json').read_text()),**case['mandate_overrides']}
 baseline=simulate(prices,dates,start,assets,mandate,grader.baseline_decider(assets,mandate))
 for name,m in modules.items():
  state=m.initialize({'assets':assets,'mandate':mandate})
  try:
   metrics=baseline if name=='baseline' else simulate(prices,dates,start,assets,mandate,lambda h,s:m.decide(h,{**s,'user_state':state}))
   gain=max(0.,min(1.,(metrics['utility']-baseline['utility'])/c['utility_scale']))
   score=c['functional_weight']+c['utility_weight']*gain+c['calibration_weight']/(1+metrics['pinball']/c['pinball_scale'])
   row={'case':case['id'],'split':case['split'],'strategy':name,'valid':True,'score':score,'reference_utility':baseline['utility'],**metrics}
  except Exception as e:row={'case':case['id'],'split':case['split'],'strategy':name,'valid':False,'error':type(e).__name__+': '+str(e)}
  records.append(row);save();print(case['id'],name,row.get('score'),row.get('error'),flush=True)
means={}
for split in ['public','feedback','audit']:
 means[split]={}
 for name in variants:
  rows=[r for r in records if r['split']==split and r['strategy']==name]
  means[split][name]=sum(r['score'] for r in rows)/len(rows) if all(r['valid'] for r in rows) else None
(OUT/'means.json').write_text(json.dumps(means,indent=2)+'\n');print(json.dumps(means,indent=2))
