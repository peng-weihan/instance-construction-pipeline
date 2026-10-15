"""Trusted causal accounting, independent of policy-reported metrics."""
import math
import numpy as np
from runtime import SubmissionError,finite,scoring_constants

def violations(w,mandate,assets,constants):
    bad=[];tol=constants["constraint_tolerance"]
    if len(w)!=len(assets) or not np.isfinite(w).all():return ['finite_weights']
    for i,a in enumerate(assets):
        if abs(w[i])>(mandate['TLT_abs_cap'] if a=='TLT' else mandate['asset_abs_cap'])+tol:bad.append('asset_cap')
        if w[i]<-tol and a not in mandate['shortable']:bad.append('shortable')
    for g,names in mandate['groups'].items():
        if sum(abs(w[assets.index(a)]) for a in names)>mandate['class_gross_caps'][g]+tol:bad.append('class_cap')
    if np.abs(w).sum()>mandate['gross_leverage_cap']+tol:bad.append('gross_cap')
    if np.maximum(-w,0).sum()>mandate['short_gross_cap']+tol:bad.append('short_cap')
    lo,hi=mandate['net_risky_exposure_bounds']
    if not lo-tol<=w.sum()<=hi+tol:bad.append('net_exposure')
    return sorted(set(bad))

def metrics(returns,navs,quantiles,variances,turnover,c,year_days):
    r=np.array(returns);nav=np.array(navs);q=np.array(quantiles);v=np.array(variances)
    if len(r)<2 or (1+r<=0).any():raise SubmissionError('bankruptcy or incomplete return series')
    annual_log=float(year_days*np.log1p(r).mean());vol=float(np.sqrt(year_days)*r.std(ddof=0))
    dd=float(np.max(1-nav/np.maximum.accumulate(nav)))
    pinball=float(np.mean((c['quantile']-(r<q).astype(float))*(r-q)))
    return {'utility':annual_log-c['volatility_penalty']*vol-c['drawdown_penalty']*dd,'annual_log_growth':annual_log,'annual_volatility':vol,
            'max_drawdown':dd,'pinball':pinball,'variance_mse':float(np.mean((v-r*r)**2)),
            'breach_rate':float(np.mean(r<q)),'turnover':float(turnover),'days':len(r),'final_nav':float(nav[-1])}

def simulate(prices,dates,start,assets,mandate,decide):
    c=scoring_constants();tol=c['constraint_tolerance'];year_days=mandate['year_days']
    nav=mandate['initial_nav'];w=np.zeros(len(assets));cash=1.;last_trade=-1000
    returns=[];navs=[nav];qs=[];vs=[];turnover=0.;trade_count=0;forecast_log=[]
    for t in range(start,len(prices)):
        day=t-start
        hist=prices[max(0,t-c['history_rows']):t]
        hist_returns=hist[1:]/hist[:-1]-1
        cov=np.cov(hist_returns,rowvar=False,ddof=0) if len(hist_returns)>=2 else np.eye(len(assets))*c['insufficient_history_variance']
        mandatory=bool(violations(w,mandate,assets,c))
        state={'day_index':day,'weights':dict(zip(assets,map(float,w))),'cash_weight':float(cash),
               'nav':nav,'last_rebalance_index':last_trade,'mandatory_rebalance':mandatory,
               'recent_forecasts':forecast_log[-c['forecast_history_rows']:]}
        history={'assets':assets,'dates':dates[max(0,t-c['history_rows']):t],'prices':hist.tolist()}
        a=decide(history,state)
        required={'weights','risk_scale','variance_daily','q05_daily','rebalance','rebalance_reason'}
        if not isinstance(a,dict) or not required<=set(a):raise SubmissionError('policy output missing required fields')
        if type(a['rebalance'])!=bool:raise SubmissionError('rebalance must be boolean')
        if not isinstance(a['weights'],dict) or set(a['weights'])!=set(assets):raise SubmissionError('weights must name every asset exactly once')
        if not isinstance(a['rebalance_reason'],str):raise SubmissionError('rebalance_reason must be text')
        if any(not finite(x) for x in list(a['weights'].values())+[a['risk_scale'],a['variance_daily'],a['q05_daily']]):raise SubmissionError('nonfinite policy output')
        if a['variance_daily']<0 or not mandate['risk_scale_bounds'][0]<=a['risk_scale']<=mandate['risk_scale_bounds'][1]:raise SubmissionError('forecast or risk scale out of bounds')
        target=np.array([a['weights'][x] for x in assets],dtype=float)
        if a['rebalance']:
            if day%mandate['rebalance_review_days'] and day-last_trade<mandate['min_extra_rebalance_gap_days'] and not mandatory:raise SubmissionError('unscheduled rebalance inside minimum gap')
            bad=violations(target,mandate,assets,c)
            if bad:raise SubmissionError('allocation constraint failed: '+','.join(bad))
            risk=float(np.sqrt(max(0,target@cov@target)*year_days))
            if risk>(mandate['risk_target_annual']/a['risk_scale'])*c['risk_budget_tolerance']+tol:raise SubmissionError('risk budget exceeded')
            amount=float(np.abs(target-w).sum());turnover+=amount;cost=mandate['cost_per_abs_weight_change']*amount;w=target;cash=1-float(w.sum());last_trade=day;trade_count+=1
        else:
            if mandatory:raise SubmissionError('mandatory exposure repair omitted')
            if np.max(np.abs(target-w))>c['hold_weight_tolerance']:raise SubmissionError('no-rebalance target must equal drifted holdings')
            cost=0.
        borrow=mandate['short_borrow_annual']/year_days*float(np.maximum(-w,0).sum());financing=mandate['negative_cash_financing_annual']/year_days*max(-cash,0)
        net=nav*(1-cost-borrow-financing)
        actual=prices[t]/prices[t-1]-1;holdings=net*w*(1+actual);cash_amount=net*cash
        new=float(holdings.sum()+cash_amount)
        if not math.isfinite(new) or new<=0:raise SubmissionError('bankruptcy')
        r=new/nav-1;returns.append(r);navs.append(new);qs.append(float(a['q05_daily']));vs.append(float(a['variance_daily']))
        forecast_log.append({'date':dates[t],'return':r,'variance_daily':float(a['variance_daily']),'q05_daily':float(a['q05_daily'])})
        w=holdings/new;cash=cash_amount/new;nav=new
    m=metrics(returns,navs,qs,vs,turnover,c,year_days);m['rebalance_count']=trade_count
    return m
