import csv,json
import numpy as np
from runtime import PUBLIC,PRIVATE,SubmissionError,check,result,finite
from forward import simulate

def grade(submission,suite):
    try:p=json.loads((submission/'answer.json').read_text())
    except Exception:raise SubmissionError('answer.json must be a JSON object')
    bounds=json.loads((PUBLIC/'source_bounds.json').read_text())
    if set(p)!=set(bounds) or any(not finite(p[k]) or not bounds[k][0]<=p[k]<=bounds[k][1] for k in bounds):
        raise SubmissionError('all ten parameters must be finite and within public bounds')
    scene=json.loads((PUBLIC/'scene.json').read_text());g=scene['grid']
    for i,k in enumerate('xyz'):
        if p['c'+k]-p['h'+k]<g['origin_m'][i] or p['c'+k]+p['h'+k]>g['origin_m'][i]+g['shape_xyz'][i]*g['spacing_m'][i]:
            raise SubmissionError('source extends outside domain')
    path=(PUBLIC if suite=='public' else PRIVATE)/(suite+'_observations.csv')
    rows=list(csv.DictReader(path.open()));pred=simulate(scene,p,sorted({float(r['day']) for r in rows}))
    a=np.array([pred[float(r['day'])][int(r['ix']),int(r['iy']),int(r['iz'])] for r in rows])
    # Public censored observations measure violation of the censor interval only.
    y=np.array([float(r['concentration']) if r['concentration'] else float(r['detection_limit']) for r in rows])
    cens=np.array([r['below_detection']=='1' for r in rows]);a[cens]=np.maximum(a[cens],y[cens])
    if not np.isfinite(a).all() or (a < -1e-12).any():raise SubmissionError('invalid concentration prediction')
    a=np.maximum(a,0);rel=float(np.sqrt(np.mean((a-y)**2))/max(np.sqrt(np.mean(y*y)),1e-6))
    log=float(np.sqrt(np.mean((np.log1p(a/.0003)-np.log1p(y/.0003))**2)))
    score=1/(1+.5*rel**2+.5*log**2)
    return result(score,[check('source_parameters',True),check('finite_forward_prediction',True),
        check('relative_rmse_below_one',rel<1),check('log_rmse_below_one',log<1)],
        {'relative_rmse':rel,'log_rmse':log,'observations':len(rows)})
