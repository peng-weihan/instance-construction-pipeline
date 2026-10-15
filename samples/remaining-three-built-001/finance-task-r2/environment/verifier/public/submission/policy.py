"""Meaningful author reference: shrinkage risk model, constrained allocation,
cost-aware rebalancing and empirical tail forecasts; only causal input is used."""
import numpy as np
from scipy.optimize import minimize

def initialize(metadata):return {'mandate':metadata['mandate']}
def decide(history,state):
    assets=history['assets'];p=np.array(history['prices']);r=p[1:]/p[:-1]-1
    mandate=state['user_state']['mandate'];n=len(assets);old=np.array([state['weights'][a] for a in assets])
    cov=np.cov(r[-126:],rowvar=False,ddof=0) if len(r)>2 else np.eye(n)*.0001
    cov=.8*cov+.2*np.diag(np.diag(cov))+np.eye(n)*1e-9
    # Conservative shrinkage of drift avoids overreacting to recent price levels.
    mu=np.clip(np.mean(r[-126:],axis=0)*252,-.15,.20)*.25 if len(r) else np.zeros(n)
    risk_scale=mandate['risk_scale_bounds'][0];target=mandate['risk_target_annual']/risk_scale
    bounds=[(0.,.45 if a=='TLT' else .30) for a in assets]
    constraints=[{'type':'ineq','fun':lambda w:w.sum()-.4},{'type':'ineq','fun':lambda w:1.2-w.sum()},
                 {'type':'ineq','fun':lambda w:(target*.95)**2-252*(w@cov@w)}]
    for group,names in mandate['groups'].items():
        ix=[assets.index(a) for a in names];cap=mandate['class_gross_caps'][group]
        constraints.append({'type':'ineq','fun':lambda w,ix=ix,cap=cap:cap-w[ix].sum()})
    x=np.full(n,.4/n);x[assets.index('TLT')]=.2;x*=.5/x.sum()
    objective=lambda w:5*252*(w@cov@w)-mu@w+.002*np.sqrt((w-old)**2+1e-8).sum()
    opt=minimize(objective,x,method='SLSQP',bounds=bounds,constraints=constraints,
                 options={'maxiter':120,'ftol':1e-10})
    if not opt.success:
        # Construct minimum-variance feasible allocation, not a silent invalid output.
        opt=minimize(lambda w:w@cov@w,x,method='SLSQP',bounds=bounds,constraints=constraints,
                     options={'maxiter':300,'ftol':1e-12})
        if not opt.success:raise RuntimeError('no feasible allocation found')
    target_w=opt.x
    due=state['day_index']%mandate['rebalance_review_days']==0 or state['mandatory_rebalance']
    extra=state['day_index']-state['last_rebalance_index']>=mandate['min_extra_rebalance_gap_days'] and np.abs(target_w-old).sum()>.20
    rebalance=bool(due or extra);w=target_w if rebalance else old
    # Explicit reductions avoid spurious floating-point flags from the host BLAS
    # matrix-vector kernel; no warning suppression or replacement of nonfinite data.
    sample=np.sum(r*w[None,:],axis=1)
    variance=float(max(np.einsum('i,ij,j->',w,cov,w,optimize=False),1e-10))
    q=float(np.quantile(sample,.05)-.0002) if len(sample) else -1.645*np.sqrt(variance)
    return {'weights':dict(zip(assets,map(float,w))),'risk_scale':risk_scale,
            'variance_daily':variance,'q05_daily':q,'rebalance':rebalance,
            'rebalance_reason':'repair/review/deviation' if rebalance else 'hold'}
