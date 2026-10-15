import csv,json
import numpy as np
from runtime import PUBLIC,PRIVATE,SubmissionError,check,result,finite,scoring_constants
from forward import simulate
def grade(submission,suite):
    c=scoring_constants()
    try:p=json.loads((submission/'answer.json').read_text())
    except Exception:raise SubmissionError('answer.json must be an object')
    bounds=json.loads((PUBLIC/'source_bounds.json').read_text())
    if not isinstance(p,dict) or set(p)!=set(bounds) or any(not finite(p[k]) or not bounds[k][0]<=p[k]<=bounds[k][1] for k in bounds):raise SubmissionError('all 113 parameters must be finite and in bounds')
    scene=json.loads((PUBLIC/'scene.json').read_text());g=scene['grid']
    for source in [1,2]:
        for i,key in enumerate('xyz'):
            if p[f's{source}_c{key}']-p[f's{source}_h{key}']<g['origin_m'][i] or p[f's{source}_c{key}']+p[f's{source}_h{key}']>g['origin_m'][i]+g['shape_xyz'][i]*g['spacing_m'][i]:raise SubmissionError('source outside domain')
    rows=list(csv.DictReader(((PUBLIC if suite=='public' else PRIVATE)/(suite+'_observations.csv')).open()))
    scores=[];checks=[check('physical_parameters',True)];metrics={}
    for experiment in ['calibration','contaminant']:
        selected=[r for r in rows if r['experiment']==experiment]
        pred=simulate(scene,p,sorted({float(r['day']) for r in selected}),experiment)
        a=np.array([pred[float(r['day'])][int(r['ix']),int(r['iy']),int(r['iz'])] for r in selected])
        y=np.array([float(r['concentration']) if r['concentration'] else float(r['detection_limit']) for r in selected])
        cens=np.array([r['below_detection']=='1' for r in selected]);a[cens]=np.maximum(a[cens],y[cens])
        if not np.isfinite(a).all() or (a < -c['negative_prediction_tolerance']).any():raise SubmissionError('nonfinite or negative prediction')
        a=np.maximum(a,0);relative=float(np.sqrt(np.mean((a-y)**2))/max(np.sqrt(np.mean(y*y)),c['relative_rmse_floor']))
        logarithmic=float(np.sqrt(np.mean((np.log1p(a/c['log_scale'])-np.log1p(y/c['log_scale']))**2)))
        scores.append(1/(1+c['relative_mse_weight']*relative**2+c['log_mse_weight']*logarithmic**2))
        metrics[experiment]={'relative_rmse':relative,'log_rmse':logarithmic,'observations':len(selected),'score':scores[-1]}
        checks.extend([check(experiment+'/finite_prediction',True),check(experiment+'/relative_rmse_below_one',relative<1),check(experiment+'/log_rmse_below_one',logarithmic<1)])
    return result(sum(scores)/len(scores),checks,{'experiments':metrics,'aggregation':'equal mean of original prediction-quality formula'})
