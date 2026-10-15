"""Public-data-only reference inverse solver, deterministic evaluation budget."""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution,minimize,least_squares
from forward import simulate,GLOBAL_KEYS
from hydrology import hydraulic_fields

def main():
    parser=argparse.ArgumentParser();parser.add_argument('public');parser.add_argument('output');parser.add_argument('--evaluations',type=int,default=1200)
    parser.add_argument('--hydraulic-iterations',type=int,default=8)
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
    hydraulic_rows=list(csv.DictReader((root/'hydraulic_observations.csv').open()))
    hydraulic_names=[k for k in bounds if k.startswith('logK_')];hydraulic_calls=0
    def hydraulic_residual(x):
        nonlocal hydraulic_calls
        candidate={**params,**dict(zip(hydraulic_names,map(float,x)))};residual=[]
        for axis in [0,1]:
            head,_,total=hydraulic_fields(scene,candidate,axis)
            for r in hydraulic_rows:
                if int(r['axis'])!=axis:continue
                ix,iy,iz=[int(r[k]) for k in ['ix','iy','iz']]
                prediction=total if ix<0 else head[ix,iy,iz]
                residual.append((prediction-float(r['value']))/float(r['sd']))
        field=np.array(x).reshape(scene['conductivity_control_shape'])
        for axis in range(3):residual.extend((.1*np.diff(field,axis=axis)).ravel())
        hydraulic_calls+=1
        return np.array(residual)
    hyd=least_squares(hydraulic_residual,np.zeros(len(hydraulic_names)),bounds=(-1.,1.),
                      max_nfev=a.hydraulic_iterations,ftol=1e-7,xtol=1e-7,gtol=1e-7)
    params.update(dict(zip(hydraulic_names,map(float,hyd.x))))
    (out/'hydraulic_fit.json').write_text(json.dumps({'residual_calls':hydraulic_calls,'optimizer_nfev':hyd.nfev,
        'residual_cost':float(hyd.cost),'elapsed_seconds':time.monotonic()-started},indent=2)+'\n')
    (out/'answer.json').write_text(json.dumps(params,indent=2)+'\n')
    calibration=[r for r in all_rows if r['experiment']=='calibration']
    optimize(GLOBAL_KEYS,calibration,max(1,int(a.evaluations*.35)),'known_injection_calibration')
    optimize([k for k in bounds if k not in GLOBAL_KEYS and not k.startswith('logK_')],[r for r in all_rows if r['experiment']=='contaminant'],a.evaluations-calls,'source_separation')
    (out/'run_summary.json').write_text(json.dumps({'hydraulic_residual_calls':hydraulic_calls,'transport_evaluations':calls,'evaluation_budget':a.evaluations,'elapsed_seconds':time.monotonic()-started,'uses_private_truth':False,'fixed_seed':713},indent=2)+'\n')
if __name__=='__main__':main()
