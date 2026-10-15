"""Author reference: infer parameters from public observations, never read truth.
Usage: python solve.py PUBLIC_DIRECTORY OUTPUT_DIRECTORY [--evaluations 600]
"""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution,minimize
from forward import simulate

def main():
    ap=argparse.ArgumentParser();ap.add_argument('public');ap.add_argument('output');ap.add_argument('--evaluations',type=int,default=600);a=ap.parse_args()
    if a.evaluations<1:ap.error('--evaluations must be positive')
    root=Path(a.public);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    scene=json.loads((root/'scene.json').read_text());bounds=json.loads((root/'source_bounds.json').read_text());names=list(bounds)
    rows=list(csv.DictReader((root/'public_observations.csv').open()));days=sorted({float(r['day']) for r in rows})
    best=[float('inf')];calls=[0];started=time.monotonic()
    class BudgetExhausted(Exception):pass
    def objective(x):
        if calls[0]>=a.evaluations:raise BudgetExhausted
        p=dict(zip(names,map(float,x)));states=simulate(scene,p,days);res=[]
        for r in rows:
            pred=max(0.,float(states[float(r['day'])][int(r['ix']),int(r['iy']),int(r['iz'])]))
            if r['below_detection']=='1':res.append(max(0.,np.log(max(pred,1e-12)/float(r['detection_limit'])))/.08)
            else:res.append(np.log(max(pred,1e-12)/float(r['concentration']))/.08)
        # Soft-L1 likelihood protects a small number of large residuals.
        loss=float(np.mean(np.sqrt(1+np.array(res)**2)-1));calls[0]+=1
        if loss<best[0]:
            best[0]=loss;(out/'answer.json').write_text(json.dumps(p,indent=2)+'\n')
            checkpoint=out/'checkpoints'/f'{calls[0]:06d}';checkpoint.mkdir(parents=True,exist_ok=False)
            (checkpoint/'answer.json').write_text(json.dumps(p,indent=2)+'\n')
            with (out/'progress.jsonl').open('a') as f:f.write(json.dumps({'calls':calls[0],'public_loss':loss,
                'elapsed_seconds':time.monotonic()-started,'checkpoint':str(checkpoint.relative_to(out))})+'\n')
        return loss
    b=[bounds[n] for n in names]
    try:
        de=differential_evolution(objective,b,seed=714,popsize=5,maxiter=max(0,a.evaluations//100-1),polish=False,workers=1)
        if calls[0]<a.evaluations:
            minimize(objective,de.x,method='Powell',bounds=b,options={'maxfev':a.evaluations-calls[0],'xtol':.002,'ftol':.001})
    except BudgetExhausted:pass
    (out/'run_summary.json').write_text(json.dumps({'evaluations':calls[0],'evaluation_budget':a.evaluations,
        'elapsed_seconds':time.monotonic()-started,'best_public_loss':best[0],'uses_private_truth':False},indent=2)+'\n')
if __name__=='__main__':main()
