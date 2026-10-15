"""Cheap deterministic least-squares shortcut screen using public inputs only."""
from pathlib import Path
import csv,json,sys,time
import numpy as np
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[2];TASK=ROOT/'samples/remaining-three-built-001/science-task-r3'
sys.path.insert(0,str(TASK/'public'));from simulator import simulate
OUT=ROOT/'runs/remaining-three-001/science-r3-ls-refinement';OUT.mkdir()
scene=json.loads((TASK/'public/scene.json').read_text());bounds=json.loads((TASK/'public/source_bounds.json').read_text())
params=json.loads((ROOT/'runs/remaining-three-001/science-r3-inverse-1200/answer.json').read_text())
rows=[r for r in csv.DictReader((TASK/'public/public_observations.csv').open()) if r['experiment']=='contaminant']
names=[k for k in bounds if not k.startswith('logK_')];days=sorted({float(r['day']) for r in rows})
y=np.array([float(r['concentration']) if r['concentration'] else float(r['detection_limit']) for r in rows]);cens=np.array([r['below_detection']=='1' for r in rows])
rms=max(float(np.sqrt(np.mean(y*y))),1e-6);started=time.monotonic();calls=0;best=float('inf');best_params=params.copy()
def residual(x):
 global calls,best,best_params
 candidate={**params,**dict(zip(names,map(float,x)))};states=simulate(scene,candidate,days,'contaminant')
 a=np.array([states[float(r['day'])][int(r['ix']),int(r['iy']),int(r['iz'])] for r in rows]);a[cens]=np.maximum(a[cens],y[cens])
 errors=np.r_[(a-y)/rms,np.log1p(a/.0003)-np.log1p(y/.0003)]/np.sqrt(2*len(y))
 loss=float(errors@errors);calls+=1
 if loss<best:
  best=loss;best_params=candidate;(OUT/'answer.json').write_text(json.dumps(candidate,indent=2)+'\n')
  with (OUT/'progress.jsonl').open('a') as f:f.write(json.dumps({'calls':calls,'public_loss':loss,'seconds':time.monotonic()-started})+'\n')
 return errors
fit=least_squares(residual,[params[k] for k in names],bounds=([bounds[k][0] for k in names],[bounds[k][1] for k in names]),
                  max_nfev=12,ftol=1e-7,xtol=1e-7,gtol=1e-7)
(OUT/'run_summary.json').write_text(json.dumps({'public_only':True,'model_runs':0,'residual_calls':calls,'optimizer_nfev':fit.nfev,
 'elapsed_seconds':time.monotonic()-started,'public_loss':best,'starts_from':'public-data-only 1200-evaluation reference'},indent=2)+'\n')
print(OUT,flush=True)
