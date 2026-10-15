from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];task=ROOT/'samples/remaining-three-built-001'/('science-task-'+(sys.argv[1] if len(sys.argv)>1 else 'r2'))
source=(Path(__file__).parent/'science_reference.py').read_text()
source=source.replace('differential_evolution,minimize','differential_evolution,minimize,least_squares')
source=source.replace('from forward import simulate,GLOBAL_KEYS','from forward import simulate,GLOBAL_KEYS\nfrom hydrology import hydraulic_fields')
source=source.replace("a=parser.parse_args();", "parser.add_argument('--hydraulic-iterations',type=int,default=8)\n    a=parser.parse_args();")
phase='''    hydraulic_rows=list(csv.DictReader((root/'hydraulic_observations.csv').open()))
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
        'residual_cost':float(hyd.cost),'elapsed_seconds':time.monotonic()-started},indent=2)+'\\n')
    (out/'answer.json').write_text(json.dumps(params,indent=2)+'\\n')
'''
source=source.replace("    calibration=[r for r in all_rows",phase+"    calibration=[r for r in all_rows")
source=source.replace("[k for k in bounds if k not in GLOBAL_KEYS]","[k for k in bounds if k not in GLOBAL_KEYS and not k.startswith('logK_')]")
source=source.replace("'evaluations':calls,'evaluation_budget'", "'hydraulic_residual_calls':hydraulic_calls,'transport_evaluations':calls,'evaluation_budget'")
(task/'solution/solve.py').write_text(source)
print(task/'solution/solve.py')
