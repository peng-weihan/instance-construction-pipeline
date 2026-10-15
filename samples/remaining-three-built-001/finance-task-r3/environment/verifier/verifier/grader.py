import csv,json,shutil
from pathlib import Path
import numpy as np
from runtime import PUBLIC,PRIVATE,ROOT,snapshot,workdir,JsonWorker,check,result,scoring_constants,SubmissionError
from ledger import simulate
import baseline_policy

def episode(case):
    file=PUBLIC/'data/dev_prices.csv' if case['split']=='public' else PRIVATE/'data/source_prices.csv'
    if case['split']=='public':
        files=[PUBLIC/'data/train_prices.csv',file]
    else:files=[file]
    rows=[]
    for p in files:
        with p.open() as f:
            rd=csv.reader(f);header=next(rd);rows.extend(list(rd))
    ix=[i for i,r in enumerate(rows) if case['first_date']<=r[0]<case['last_date']]
    if not ix:raise RuntimeError('empty historical episode')
    first=ix[0];begin=max(0,first-253);end=ix[-1]+1
    p=np.array([[float(x) for x in row[1:]] for row in rows[begin:end]])
    p=100*p/p[0] # price-level normalization preserves every daily return.
    dates=['step-%05d'%i for i in range(len(p))]
    return p,dates,first-begin,header[1:]

def baseline_decider(assets,mandate):
    user_state=baseline_policy.initialize({'assets':assets,'mandate':mandate})
    def decide(h,s):return baseline_policy.decide(h,{**s,'user_state':user_state})
    return decide

def grade(submission,suite):
    if not (submission/'policy.py').is_file():raise SubmissionError('policy.py missing')
    c=scoring_constants();cases=[x for x in json.loads((PRIVATE/'episodes.json').read_text()) if x['split']==suite]
    scores=[];records=[];checks=[]
    with workdir() as tmp:
        work=Path(tmp);snapshot(submission,work/'submission');shutil.copyfile(ROOT/'verifier/policy_worker.py',work/'policy_worker.py')
        for case in cases:
            prices,dates,start,assets=episode(case)
            mandate={**json.loads((PUBLIC/'mandate.json').read_text()),**case['mandate_overrides']}
            baseline=simulate(prices,dates,start,assets,mandate,baseline_decider(assets,mandate))
            worker=JsonWorker(work,['python','policy_worker.py'],readonly=['policy_worker.py','submission'])
            try:
                ready=worker.exchange({'op':'initialize','metadata':{'assets':assets,'mandate':mandate}},timeout=c['initialize_seconds'])
                if ready!={'initialized':True}:raise SubmissionError('policy initialization failed')
                m=simulate(prices,dates,start,assets,mandate,lambda h,s:worker.exchange({'op':'decide','history':h,'state':s},timeout=c['decision_seconds']))
            finally:worker.close()
            gain=max(0.,min(1.,(m['utility']-baseline['utility'])/c['utility_scale']))
            calibration=1/(1+m['pinball']/c['pinball_scale'])
            score=c['functional_weight']+c['utility_weight']*gain+c['calibration_weight']*calibration
            scores.append(score);records.append({'case':case['id'],'score':score,'reference_utility':baseline['utility'],**m})
            checks.extend([check(case['id']+'/allocation_and_causality',True),
                           check(case['id']+'/positive_utility_gain',gain>0),
                           check(case['id']+'/tail_calibration',abs(m['breach_rate']-c['quantile'])<c['breach_rate_tolerance'])])
    return result(sum(scores)/len(scores),checks,{'episodes':records,'episode_count':len(scores),'aggregation':'equal mean of original per-episode formula'})
