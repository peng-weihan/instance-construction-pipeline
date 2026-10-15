"""Public-data-only reference inverse solver, deterministic evaluation budget."""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution,minimize
from forward import simulate,GLOBAL_KEYS

def main():
    parser=argparse.ArgumentParser();parser.add_argument('public');parser.add_argument('output');parser.add_argument('--evaluations',type=int,default=1200)
    a=parser.parse_args();root=Path(a.public);out=Path(a.output);out.mkdir(parents=True)
    scene=json.loads((root/'scene.json').read_text());bounds=json.loads((root/'source_bounds.json').read_text())
    all_rows=list(csv.DictReader((root/'public_observations.csv').open()));params={k:sum(v)/2 for k,v in bounds.items()};calls=0;started=time.monotonic()
    class BudgetExhausted(Exception):pass
    def optimize(names,selected,cap,phase):
        nonlocal params,calls
        phase_calls=0;best=float('inf');best_params=params.copy()
        def objective(x):
            nonlocal calls,phase_calls,best,best_params
            if calls>=a.evaluations or phase_calls>=cap:raise BudgetExhausted
            candidate={**params,**dict(zip(names,map(float,x)))};losses=[]
            for experiment in sorted({r['experiment'] for r in selected}):
                rows=[r for r in selected if r['experiment']==experiment]
                states=simulate(scene,candidate,sorted({float(r['day']) for r in rows}),experiment)
                errors=[]
                for r in rows:
                    prediction=max(1e-12,float(states[float(r['day'])][int(r['ix']),int(r['iy']),int(r['iz'])]))
                    if r['below_detection']=='1':residual=max(0.,np.log(prediction/float(r['detection_limit'])))
                    else:residual=np.log(prediction/max(float(r['concentration']),1e-12))
                    errors.append(residual/.05)
                losses.append(float(np.mean(np.sqrt(1+np.array(errors)**2)-1)))
            value=float(np.mean(losses));calls+=1;phase_calls+=1
            if value<best:
                best=value;best_params=candidate
                (out/'answer.json').write_text(json.dumps(candidate,indent=2)+'\n')
                checkpoint=out/'checkpoints'/('%06d'%calls);checkpoint.mkdir(parents=True)
                (checkpoint/'answer.json').write_text(json.dumps(candidate,indent=2)+'\n')
                with (out/'progress.jsonl').open('a') as f:f.write(json.dumps({'phase':phase,'evaluations':calls,'phase_loss':value,'elapsed_seconds':time.monotonic()-started})+'\n')
            return value
        try:
            population=3*len(names);iterations=max(0,cap//population-2)
            result=differential_evolution(objective,[bounds[n] for n in names],seed=713,popsize=3,maxiter=iterations,polish=False,workers=1)
            if phase_calls<cap:minimize(objective,result.x,method='Powell',bounds=[bounds[n] for n in names],options={'maxfev':cap-phase_calls,'xtol':.002,'ftol':.002})
        except BudgetExhausted:pass
        params=best_params
    (out/'answer.json').write_text(json.dumps(params,indent=2)+'\n')
    calibration=[r for r in all_rows if r['experiment']=='calibration']
    optimize(GLOBAL_KEYS,calibration,max(1,int(a.evaluations*.35)),'known_injection_calibration')
    optimize([k for k in bounds if k not in GLOBAL_KEYS],[r for r in all_rows if r['experiment']=='contaminant'],a.evaluations-calls,'source_separation')
    (out/'run_summary.json').write_text(json.dumps({'evaluations':calls,'evaluation_budget':a.evaluations,'elapsed_seconds':time.monotonic()-started,'uses_private_truth':False,'fixed_seed':713},indent=2)+'\n')
if __name__=='__main__':main()
