"""Trusted causal accounting, independent of policy-reported metrics."""
import math
import numpy as np
from runtime import SubmissionError,finite

def violations(w,mandate,assets):
    bad=[]
    if len(w)!=len(assets) or not np.isfinite(w).all():return ['finite_weights']
    for i,a in enumerate(assets):
        if abs(w[i])>(mandate['TLT_abs_cap'] if a=='TLT' else mandate['asset_abs_cap'])+1e-8:bad.append('asset_cap')
        if w[i]<-1e-8 and a not in mandate['shortable']:bad.append('shortable')
    for g,names in mandate['groups'].items():
        if sum(abs(w[assets.index(a)]) for a in names)>mandate['class_gross_caps'][g]+1e-8:bad.append('class_cap')
    if np.abs(w).sum()>mandate['gross_leverage_cap']+1e-8:bad.append('gross_cap')
    if np.maximum(-w,0).sum()>mandate['short_gross_cap']+1e-8:bad.append('short_cap')
    lo,hi=mandate['net_risky_exposure_bounds']
    if not lo-1e-8<=w.sum()<=hi+1e-8:bad.append('net_exposure')
    return sorted(set(bad))

def metrics(returns,navs,quantiles,variances,turnover):
    r=np.array(returns);nav=np.array(navs);q=np.array(quantiles);v=np.array(variances)
    if len(r)<2 or (1+r<=0).any():raise SubmissionError('bankruptcy or incomplete return series')
    annual_log=float(252*np.log1p(r).mean());vol=float(np.sqrt(252)*r.std(ddof=0))
    dd=float(np.max(1-nav/np.maximum.accumulate(nav)))
    pinball=float(np.mean((.05-(r<q).astype(float))*(r-q)))
    return {'utility':annual_log-.5*vol-dd,'annual_log_growth':annual_log,'annual_volatility':vol,
            'max_drawdown':dd,'pinball':pinball,'variance_mse':float(np.mean((v-r*r)**2)),
            'breach_rate':float(np.mean(r<q)),'turnover':float(turnover),'days':len(r),'final_nav':float(nav[-1])}

def simulate(prices,dates,start,assets,mandate,decide):
    nav=mandate['initial_nav'];w=np.zeros(len(assets));cash=1.;last_trade=-1000
    returns=[];navs=[nav];qs=[];vs=[];turnover=0.;trade_count=0;forecast_log=[]
    for t in range(start,len(prices)):
        day=t-start
        hist=prices[max(0,t-253):t]
        hist_returns=hist[1:]/hist[:-1]-1
        cov=np.cov(hist_returns,rowvar=False,ddof=0) if len(hist_returns)>=2 else np.eye(len(assets))*1e-4
        mandatory=bool(violations(w,mandate,assets))
        state={'day_index':day,'weights':dict(zip(assets,map(float,w))),'cash_weight':float(cash),
               'nav':nav,'last_rebalance_index':last_trade,'mandatory_rebalance':mandatory,
               'recent_forecasts':forecast_log[-20:]}
        history={'assets':assets,'dates':dates[max(0,t-253):t],'prices':hist.tolist()}
        a=decide(history,state)
        required={'weights','risk_scale','variance_daily','q05_daily','rebalance','rebalance_reason'}
        if not isinstance(a,dict) or not required<=set(a):raise SubmissionError('policy output missing required fields')
        if type(a['rebalance'])!=bool:raise SubmissionError('rebalance must be boolean')
        if not isinstance(a['weights'],dict) or set(a['weights'])!=set(assets):raise SubmissionError('weights must name every asset exactly once')
        if not isinstance(a['rebalance_reason'],str):raise SubmissionError('rebalance_reason must be text')
        if any(not finite(x) for x in list(a['weights'].values())+[a['risk_scale'],a['variance_daily'],a['q05_daily']]):raise SubmissionError('nonfinite policy output')
        if a['variance_daily']<0 or not .7<=a['risk_scale']<=2.2:raise SubmissionError('forecast or risk scale out of bounds')
        target=np.array([a['weights'][x] for x in assets],dtype=float)
        if a['rebalance']:
            if day%20 and day-last_trade<5 and not mandatory:raise SubmissionError('unscheduled rebalance inside minimum gap')
            bad=violations(target,mandate,assets)
            if bad:raise SubmissionError('allocation constraint failed: '+','.join(bad))
            risk=float(np.sqrt(max(0,target@cov@target)*252))
            if risk>(.10/a['risk_scale'])*1.2+1e-8:raise SubmissionError('risk budget exceeded')
            amount=float(np.abs(target-w).sum());turnover+=amount;cost=.0005*amount;w=target;cash=1-float(w.sum());last_trade=day;trade_count+=1
        else:
            if mandatory:raise SubmissionError('mandatory exposure repair omitted')
            if np.max(np.abs(target-w))>1e-7:raise SubmissionError('no-rebalance target must equal drifted holdings')
            cost=0.
        borrow=.03/252*float(np.maximum(-w,0).sum());financing=.05/252*max(-cash,0)
        net=nav*(1-cost-borrow-financing)
        actual=prices[t]/prices[t-1]-1;holdings=net*w*(1+actual);cash_amount=net*cash
        new=float(holdings.sum()+cash_amount)
        if not math.isfinite(new) or new<=0:raise SubmissionError('bankruptcy')
        r=new/nav-1;returns.append(r);navs.append(new);qs.append(float(a['q05_daily']));vs.append(float(a['variance_daily']))
        forecast_log.append({'date':dates[t],'return':r,'variance_daily':float(a['variance_daily']),'q05_daily':float(a['q05_daily'])})
        w=holdings/new;cash=cash_amount/new;nav=new
    m=metrics(returns,navs,qs,vs,turnover);m['rebalance_count']=trade_count
    return m
