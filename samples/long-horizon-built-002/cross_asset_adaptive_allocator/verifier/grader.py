import csv,json,shutil
from pathlib import Path
import numpy as np
from runtime import PUBLIC,PRIVATE,ROOT,snapshot,workdir,JsonWorker,check,result
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
    raw={'SPY':.10,'IWM':.05,'EFA':.10,'EEM':.05,'TLT':.40,'GLD':.05,'VNQ':.05,'DBC':.05}
    def decide(history,state):
        p=np.array(history['prices']);r=p[1:]/p[:-1]-1
        cov=np.cov(r,rowvar=False,ddof=0);w=np.array([raw[a] for a in assets]);vol=np.sqrt(max(w@cov@w,0)*252)
        if vol>.10/.7:w*=max(.4/w.sum(),(.10/.7)/vol)
        reb=state['day_index']%20==0 or state['mandatory_rebalance']
        if not reb:w=np.array([state['weights'][a] for a in assets])
        variance=float(max(w@cov@w,1e-10))
        return dict(weights=dict(zip(assets,map(float,w))),risk_scale=.7,variance_daily=variance,
                    q05_daily=-1.645*np.sqrt(variance),rebalance=bool(reb),rebalance_reason='fixed reference schedule')
    return decide

def grade(submission,suite):
    prices,dates,start,assets=data(suite);mandate=json.loads((PUBLIC/'mandate.json').read_text())
    reference=simulate(prices,dates,start,assets,mandate,static_policy(assets,mandate))
    with workdir() as tmp:
        work=Path(tmp);snapshot(submission,work/'submission');shutil.copyfile(ROOT/'verifier/policy_worker.py',work/'policy_worker.py')
        worker=JsonWorker(work,['python','policy_worker.py'],readonly=['policy_worker.py','submission'])
        try:
            worker.exchange({'op':'initialize','metadata':{'assets':assets,'mandate':mandate}},timeout=20)
            m=simulate(prices,dates,start,assets,mandate,lambda h,s:worker.exchange({'op':'decide','history':h,'state':s},timeout=2))
        finally:worker.close()
    gain=max(0.,min(1.,(m['utility']-reference['utility'])/.10));cal=1/(1+m['pinball']/.01)
    m['reference_utility']=reference['utility'];m['utility_improvement_component']=gain;m['calibration_component']=cal
    checks=[check('causal_protocol',True),check('finite_forecasts',True),check('allocation_constraints',True),
            check('independent_ledger',True),check('positive_improvement',gain>0),check('tail_calibration',abs(m['breach_rate']-.05)<.03)]
    return result(.25+.60*gain+.15*cal,checks,m)
