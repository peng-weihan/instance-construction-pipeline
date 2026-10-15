import csv,json,shutil
from pathlib import Path
import numpy as np
from runtime import PUBLIC,PRIVATE,ROOT,snapshot,workdir,JsonWorker,check,result,scoring_constants,SubmissionError
from ledger import simulate

def data(suite):
    names=['train','dev'] if suite=='public' else (['train','dev','feedback'] if suite=='feedback' else ['train','dev','feedback','audit'])
    rows=[];start=0;assets=None
    for name in names:
        root=PUBLIC/'data' if name in ['train','dev'] else PRIVATE/'data'
        with (root/(name+'_prices.csv')).open() as f:
            rd=csv.reader(f);header=next(rd);part=list(rd)
        if name==names[-1]:start=len(rows)
        rows+=part;assets=header[1:]
    return np.array([[float(x) for x in r[1:]] for r in rows]),[r[0] for r in rows],start,assets

def static_policy(assets,mandate):
    # Fixed target allocation with deterministic exposure repairs. No fitted future parameters.
    c=scoring_constants();raw=c['baseline_weights'];scale=mandate['risk_scale_bounds'][0]
    def decide(history,state):
        p=np.array(history['prices']);r=p[1:]/p[:-1]-1
        cov=np.cov(r,rowvar=False,ddof=0);w=np.array([raw[a] for a in assets]);vol=np.sqrt(max(w@cov@w,0)*mandate['year_days'])
        if vol>mandate['risk_target_annual']/scale:w*=max(mandate['net_risky_exposure_bounds'][0]/w.sum(),(mandate['risk_target_annual']/scale)/vol)
        reb=state['day_index']%mandate['rebalance_review_days']==0 or state['mandatory_rebalance']
        if not reb:w=np.array([state['weights'][a] for a in assets])
        variance=float(max(w@cov@w,c['baseline_variance_floor']))
        return dict(weights=dict(zip(assets,map(float,w))),risk_scale=scale,variance_daily=variance,
                    q05_daily=c['baseline_tail_z']*np.sqrt(variance),rebalance=bool(reb),rebalance_reason='fixed reference schedule')
    return decide

def grade(submission,suite):
    c=scoring_constants()
    prices,dates,start,assets=data(suite);mandate=json.loads((PUBLIC/'mandate.json').read_text())
    reference=simulate(prices,dates,start,assets,mandate,static_policy(assets,mandate))
    with workdir() as tmp:
        work=Path(tmp);snapshot(submission,work/'submission');shutil.copyfile(ROOT/'verifier/policy_worker.py',work/'policy_worker.py')
        worker=JsonWorker(work,['python','policy_worker.py'],readonly=['policy_worker.py','submission'])
        try:
            initialized=worker.exchange({'op':'initialize','metadata':{'assets':assets,'mandate':mandate}},timeout=c['initialize_seconds'])
            if initialized!={'initialized':True}:raise SubmissionError('policy initialization failed')
            m=simulate(prices,dates,start,assets,mandate,lambda h,s:worker.exchange({'op':'decide','history':h,'state':s},timeout=c['decision_seconds']))
        finally:worker.close()
    gain=max(0.,min(1.,(m['utility']-reference['utility'])/c['utility_scale']));cal=1/(1+m['pinball']/c['pinball_scale'])
    m['reference_utility']=reference['utility'];m['utility_improvement_component']=gain;m['calibration_component']=cal
    checks=[check('causal_protocol',True),check('finite_forecasts',True),check('allocation_constraints',True),
            check('independent_ledger',True),check('positive_improvement',gain>0),check('tail_calibration',abs(m['breach_rate']-c['quantile'])<c['breach_rate_tolerance'])]
    return result(c['functional_weight']+c['utility_weight']*gain+c['calibration_weight']*cal,checks,m)
