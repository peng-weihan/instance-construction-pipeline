"""Build a real-history, multi-regime allocation task with a public strong baseline."""
from pathlib import Path
import csv, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'samples/long-horizon-built-007/cross_asset_adaptive_allocator'
TASK = ROOT / 'samples/remaining-three-built-001/finance-task-r1'
shutil.copytree(BASE, TASK)
source = ROOT / 'materials/repos/portfolio-risk-engine/results/prices.csv'
with source.open() as f:
    reader = csv.reader(f); header = next(reader); rows = list(reader)

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

# Preserve original market observations. No fabricated market paths or prices.
for side in ['public', 'private']:
    shutil.rmtree(TASK / side / 'data')
    (TASK / side / 'data').mkdir()
for name, first, last in [('train', '2006-01-01', '2012-01-01'),
                          ('dev', '2012-01-01', '2014-01-01')]:
    with (TASK/'public/data'/(name+'_prices.csv')).open('w') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(r for r in rows if first<=r[0]<last)
shutil.copyfile(source, TASK/'private/data/source_prices.csv')
cases=[]
for split, years in [('public',[2012,2013]),('feedback',list(range(2014,2020))),('audit',list(range(2020,2026)))]:
    for year in years:
        for setting, cost, target in [('ordinary',.0005,.10),('costly',.002,.085)]:
            cases.append({'id':f'{split}_{year}_{setting}','split':split,
                          'first_date':f'{year}-01-01','last_date':f'{year+1}-01-01',
                          'mandate_overrides':{'cost_per_abs_weight_change':cost,'risk_target_annual':target}})
write_json(TASK/'private/episodes.json',cases)

baseline=(BASE/'solution/policy.py').read_text()
baseline=baseline.replace("risk_scale=.7;target=.10/risk_scale", "risk_scale=mandate['risk_scale_bounds'][0];target=mandate['risk_target_annual']/risk_scale")
baseline=baseline.replace("state['day_index']%20", "state['day_index']%mandate['rebalance_review_days']")
baseline=baseline.replace("state['last_rebalance_index']>=5", "state['last_rebalance_index']>=mandate['min_extra_rebalance_gap_days']")
baseline=baseline.replace("extra=state", "extra=state")
(TASK/'verifier/baseline_policy.py').write_text(baseline)
(TASK/'public/baseline_policy.py').write_text(baseline)
(TASK/'public/submission/policy.py').write_text(baseline)
(TASK/'solution/policy.py').write_text(baseline)

grader='''import csv,json,shutil
from pathlib import Path
import numpy as np
from runtime import PUBLIC,PRIVATE,ROOT,snapshot,workdir,JsonWorker,check,result,scoring_constants,SubmissionError
from ledger import simulate
import baseline_policy

def episode(case):
    file=PUBLIC/'data/dev_prices.csv' if case['split']=='public' else PRIVATE/'data/source_prices.csv'
    if case['split']=='public':
        files=[PUBLIC/'data/train_prices.csv',file]
    else:files=[file]
    rows=[]
    for p in files:
        with p.open() as f:
            rd=csv.reader(f);header=next(rd);rows.extend(list(rd))
    ix=[i for i,r in enumerate(rows) if case['first_date']<=r[0]<case['last_date']]
    if not ix:raise RuntimeError('empty historical episode')
    first=ix[0];begin=max(0,first-253);end=ix[-1]+1
    p=np.array([[float(x) for x in row[1:]] for row in rows[begin:end]])
    p=100*p/p[0] # price-level normalization preserves every daily return.
    dates=['step-%05d'%i for i in range(len(p))]
    return p,dates,first-begin,header[1:]

def baseline_decider(assets,mandate):
    user_state=baseline_policy.initialize({'assets':assets,'mandate':mandate})
    def decide(h,s):return baseline_policy.decide(h,{**s,'user_state':user_state})
    return decide

def grade(submission,suite):
    c=scoring_constants();cases=[x for x in json.loads((PRIVATE/'episodes.json').read_text()) if x['split']==suite]
    scores=[];records=[];checks=[]
    with workdir() as tmp:
        work=Path(tmp);snapshot(submission,work/'submission');shutil.copyfile(ROOT/'verifier/policy_worker.py',work/'policy_worker.py')
        for case in cases:
            prices,dates,start,assets=episode(case)
            mandate={**json.loads((PUBLIC/'mandate.json').read_text()),**case['mandate_overrides']}
            baseline=simulate(prices,dates,start,assets,mandate,baseline_decider(assets,mandate))
            worker=JsonWorker(work,['python','policy_worker.py'],readonly=['policy_worker.py','submission'])
            try:
                ready=worker.exchange({'op':'initialize','metadata':{'assets':assets,'mandate':mandate}},timeout=c['initialize_seconds'])
                if ready!={'initialized':True}:raise SubmissionError('policy initialization failed')
                m=simulate(prices,dates,start,assets,mandate,lambda h,s:worker.exchange({'op':'decide','history':h,'state':s},timeout=c['decision_seconds']))
            finally:worker.close()
            gain=max(0.,min(1.,(m['utility']-baseline['utility'])/c['utility_scale']))
            calibration=1/(1+m['pinball']/c['pinball_scale'])
            score=c['functional_weight']+c['utility_weight']*gain+c['calibration_weight']*calibration
            scores.append(score);records.append({'case':case['id'],'score':score,'reference_utility':baseline['utility'],**m})
            checks.extend([check(case['id']+'/allocation_and_causality',True),
                           check(case['id']+'/positive_utility_gain',gain>0),
                           check(case['id']+'/tail_calibration',abs(m['breach_rate']-c['quantile'])<c['breach_rate_tolerance'])])
    return result(sum(scores)/len(scores),checks,{'episodes':records,'episode_count':len(scores),'aggregation':'equal mean of original per-episode formula'})
'''
(TASK/'verifier/grader.py').write_text(grader)

instruction='''# 多市场阶段的风险自适应配置

改进公开 baseline_policy.py，在股票、债券、黄金、商品和地产这八类 ETF 的真实历史上构建一个可跨市场阶段运行的配置策略。工作预算六小时。

public/data 提供 2006—2011 年训练行情及 2012—2013 年开发行情。固定反馈使用 2014—2019 年六个独立年度工作负载，独立审计使用 2020—2025 年六个年度。每个年度分别在普通交易成本和较高交易成本/较低风险预算下评测：这是六份行情、十二种评测配置。每轮重置策略状态，提供至决策前一天的 253 行滚动历史。评判时将价格归一化，日历替换为相对步号；实际收益完全保留。

提交 submission/policy.py 及其离线模块/参数文件，接口见 policy_interface.md。initialize 收到本轮真实 mandate；约束、借券、融资、风险限额及独立 NAV 记账规则保持原协议。所有决策只使用给定历史；任一非法决策使整个提交无效。公开 baseline_policy.py 是冻结比较基线，不能修改评分器中的基线。起始 policy.py 已复制这个可运行基线，可以立即取得反馈。

每个配置仍按原公式 0.25+0.60*clip((U-U_ref)/0.10,0,1)+0.15/(1+pinball/0.01) 计分，总分为十二个配置的等权平均。权重与归一化常量没有调整。原始年度收益、波动、回撤、换手、尾部校准和基线效用逐配置返回。可改进风险估计、趋势/状态识别、约束优化和成本敏感调仓；不能仅针对一个牛市或单一成本设定选参数。

素材为固定上游缓存中的 yfinance 历史行情，不是合成行情。本版本用于本地研究验证；训练数据再分发许可尚未确认。
'''
(TASK/'instruction.md').write_text(instruction);(TASK/'public/instruction.md').write_text(instruction)
write_json(TASK/'public/evaluation_contract.json',{'public_years':[2012,2013],'feedback_years':list(range(2014,2020)),
 'audit_years':list(range(2020,2026)),'configurations_per_year':2,'calendar_visible_to_policy':False,
 'source_prices_unchanged':True,'formula_constants_unchanged':True,'baseline':'published shrinkage covariance and constrained allocation policy'})
for name in ['scoring_metadata.json','score_design.json']:
    p=TASK/'public'/name;d=json.loads(p.read_text());d['episode_aggregation']='equal arithmetic mean';d['baseline_version']='public/baseline_policy.py; frozen independent copy in verifier'
    write_json(p,d)
for side in ['agent','verifier']:
    ctx=TASK/'environment'/side
    shutil.rmtree(ctx/'public');shutil.copytree(TASK/'public',ctx/'public')
    if side=='verifier':
        shutil.rmtree(ctx/'private');shutil.copytree(TASK/'private',ctx/'private')
        shutil.rmtree(ctx/'verifier');shutil.copytree(TASK/'verifier',ctx/'verifier')
write_json(TASK/'REVISION.json',{'source_task':str(BASE.relative_to(ROOT)),'price_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'source_commit':'a00e1a48e05b1c561a4b753ee03302fdf57f25b9','changes':['independent historical years','paired cost/risk mandates','public stronger comparison baseline','causal relative-time episodes'],
 'score_constants_unchanged':True,'redistribution_rights':'not_confirmed','runtime_verified':False})
print(TASK)
