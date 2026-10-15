"""Build six source-grounded long-horizon candidate packages, without runtime grading.

This constructs materials/specifications, not calibrated benchmark acceptances.
Requires the pinned repositories acquired for this workspace. Does not call an LLM.
"""
from pathlib import Path
import argparse, csv, hashlib, io, json, math, random, re, shutil
from construct_category_samples import ROOT, REPOS, write, dump, copy, repo_snapshot, source, sha

OLD=ROOT/'samples/category-pilot-004'

def candidate(out, task, category, title, anchor, sources, progression, gaps):
    p=out/task
    (p/'public').mkdir(parents=True);(p/'private').mkdir()
    dump(p/'candidate.json',dict(task_id=task,category=category,title=title,anchor=anchor,
        status='constructed_unverified',construction_stage='materials_and_spec_constructed',sources=sources,
        authoring='interactive source inspection + deterministic construction scripts; no independent CLI model run',
        long_horizon_potential='design hypothesis, not an observed six-hour curve',
        empirical_training_benefit=None,accepted=False,progression=progression,
        construction_gaps=gaps,runtime_verification='deferred_by_user'))
    dump(p/'public/contract.draft.json',dict(schema='local-candidate-v2-not-official-Harbor',
        agent_budget_seconds=21600,submission='explicit files listed in instruction.md',
        runtime_network=dict(agent='none',verifier='none'),separate_environments=True,
        stateless_verifier=True,score_depends_only_on_snapshot=True,
        official_run_result='maximum valid score over submissions on the SAME frozen feedback suite',
        audit_holdout='for transfer/generalization audit only, not a replacement for best-of-run selection',
        score_output=dict(score='bounded [0,1]',valid='boolean',checks='named pass/fail + diagnostic',raw_metrics='object'),
        budget_note='Feedback deadlines are construction targets; no timing measurements exist.',
        calibration=dict(baseline=None,oracle=None,model_runs=0,difficulty_calibrated=False),
        pending_delivery=['official Harbor schema','two Docker build contexts','offline dependency closure','implemented and audited verifier','runtime evidence']))
    return p

def finish(p, spec, design, score):
    write(p/'public/instruction.md',spec)
    write(p/'DESIGN.md',design)
    dump(p/'public/score_design.json',score)

def software(out):
    p=candidate(out,'restler_resilient_execution','Systems & Software Engineering','RESTler 可恢复执行与资源生命周期路线图',
        'schemathesis_datagen_pipeline',[source('restler-fuzzer',['restler/engine/core/request_utilities.py','restler/engine/core/async_request_utilities.py','restler/engine/dependencies.py','restler/restler_settings.py'])],
        ['配置与确定性调度','幂等重试、异步 deadline 与清理集成','可回放诊断、兼容性与组合故障'],
        ['New-feature reference branch and executable acceptance tests still need construction; old upstream code is not an oracle for new requirements.'])
    repo_snapshot('restler-fuzzer',p/'public/repo')
    features=[
      ('policy',.10,'按 global→endpoint→HTTP method 继承执行策略，严格验证未知键和类型，错误包含配置路径。'),
      ('retry',.15,'同时支持 Retry-After 秒数/HTTP-date、指数回退、显式上限、可复现 jitter 与统一截止时间。'),
      ('idempotency',.15,'GET/HEAD/PUT/DELETE 可按配置重试；POST/PATCH 仅在显式 idempotency key 策略启用时重试，网络失败不重复提交不安全写入。'),
      ('async',.15,'请求、重试等待、轮询和最终 GET 共享一个 monotonic deadline，统一返回完成/失败/超时/取消状态。'),
      ('leases',.20,'用资源依赖 DAG 管理临时资源和 create-once lease，引用未释放不清理，按逆依赖顺序清理，部分创建失败仍回收已创建资源。'),
      ('trace',.10,'输出稳定 JSONL 状态事件，记录策略决策和因果 request/resource ID，脱敏认证及 idempotency key，不能泄露原始秘密。'),
      ('replay',.15,'提供离线故障轨迹回放；注入时钟与 transport 后产生与原运行一致的规范化决策轨迹；原有未启用策略的行为兼容。')]
    dump(p/'public/roadmap.json',[dict(id=i,weight=w,requirement=t) for i,w,t in features])
    policy={'schema_version':1,'global':{'max_attempts':4,'deadline_seconds':30,'cleanup_deadline_seconds':10,'base_delay_seconds':1,'delay_cap_seconds':8,'jitter_fraction':0,'retry_statuses':[429,503]},
      'endpoints':{'/jobs':{'POST':{'idempotency_header':'Idempotency-Key','max_attempts':3}}}}
    dump(p/'public/policy_example.json',policy)
    fixtures=[
      dict(id='get_retry_after',method='GET',statuses=[429,200],retry_after='2',deadline=10,expected={'attempts':2,'wait_seconds':[2],'terminal':'succeeded'}),
      dict(id='unsafe_post',method='POST',statuses=[503,200],idempotency_key=None,deadline=10,expected={'attempts':1,'terminal':'failed'}),
      dict(id='deadline_before_retry',method='GET',statuses=[503,200],retry_after='8',deadline=5,expected={'attempts':1,'terminal':'timed_out','extra_transport_calls':0}),
      dict(id='rollback_dependency_chain',resources=[['namespace',None],['job','namespace'],['artifact','job']],failure='artifact creation',expected={'cleanup_order':['job','namespace']}),
      dict(id='shared_lease',references={'namespace':2},release_count=1,expected={'deleted_resources':[]}),
      dict(id='trace_redaction',headers={'Authorization':'TEST_SECRET','Idempotency-Key':'TEST_KEY'},expected={'forbidden_trace_values':['TEST_SECRET','TEST_KEY']})]
    dump(p/'public/behavior_examples.json',fixtures)
    write(p/'public/interface.md','''Policy is configured under a new `execution_policy` key in RESTler settings.
All durations are seconds; max_attempts includes the first attempt. A response at the deadline is too late.
Attempt k (k=1 for the first retry) has base delay min(cap, base*2**(k-1)); use the larger of this and a valid Retry-After.
For HTTP-date parsing, capture wall-clock and monotonic time once per response; convert to nonnegative delay. Malformed Retry-After uses backoff.
With nonzero jitter_fraction j, multiply the chosen delay by Uniform(1-j,1+j) using an injected RNG; record the chosen delay. Tests use fixed RNG streams.
Never sleep past deadline, never issue a new transport request at/after deadline. Cancellation stops new work and starts cleanup; cleanup_deadline_seconds is a separate budget measured from cleanup start. At that deadline stop issuing deletions and record unreleased resource IDs as cleanup_incomplete, without extending the work deadline.
Policy precedence: exact normalized path+method > exact path defaults > global. Unknown keys and negative durations are configuration errors.
Resource graph is a DAG; cycles are rejected before execution. A parent can be deleted only after all children and references are gone.
Canonical event keys: event_index, request_id, resource_id, event, attempt, elapsed_ms, decision, reason. No raw body/auth/key values.
Implement `python -m engine.tools.replay_execution INPUT.jsonl --policy POLICY.json --output TRACE.jsonl` from the restler directory.
Integration remains through existing rendering, transport, async and GC call sites; a standalone mock implementation earns no integration checks.
''')
    dump(p/'private/check_plan.json',{'feature_groups':[{'id':i,'weight':w,'required_layers':['unit','caller_integration','cross_feature_regression']} for i,w,t in features],
         'cross_faults':['retry budget consumed before async completion','cancellation while shared parent is leased','creation failure during multi-level cleanup','schema error before transport','redaction survives replay']})
    finish(p,'''# 实现可恢复的 API 测试执行链

在完整 RESTler 工程上实现 roadmap.json 的七项新需求。起始仓库保留原功能；任务是建设新的执行策略、资源生命周期及可回放诊断能力。读取 interface.md 中的精确边界与 behavior_examples.json 的公开行为样例。

提交 repo/restler/ 的源码目录，可新增模块和本地测试。保留未启用 execution_policy 时的兼容行为；禁止更改外部评分器。所有模块必须通过实际引擎调用链集成，不能只写独立演示程序。上游自带测试用于帮助理解，不代表新增需求已有答案。

可以先完成配置、策略与基础重试，再做异步/取消/资源清理，最后处理组合故障、追踪和回放。各功能有独立部分分，集成行为决定每组剩余分。评分只取提交文件快照，固定反馈集合提供具名失败项。目标预算为 6 小时。
''','''# 长程潜力与素材依据

保留原题“真实 API 测试框架、多项功能路线图、兼容性和集成”的能力结构，改为 RESTler 的可恢复执行链。七项功能共享 deadline、重试状态和资源依赖，存在真实的设计取舍与后期组合故障；不是把原来的 9 个函数再多挖几个洞。

原 repo、MIT 许可、调用方和设置文档均已取得。新增 6 份公开行为样例、精确接口约定和七组检查计划。下一步出题工作是让 constructor 实现完整参考分支并据真实 diff 构造私有测试；这些尚未完成，不能把上游旧版本称为新需求的 oracle。借用 DeepSWE query/specialize 的完整行为构造路线，保留 NL2Repo 的需求—接口绑定。

风险：若只测试局部 helper，题目会缩水；若所有分数依赖最终总集成，曲线会卡死。评分设计应使各层可独立诊断、最后由跨功能用例拉开差距。
''',{'aggregation':'sum(weight[group]*pass_fraction[group])','groups':{i:w for i,w,t in features},'feedback_deadline_target_seconds':300,'fixed_checks_pending':True})
    return p

FV_GENERATOR='''"""Private authoring generator for an original layered ADE scene; synthetic data only.
Cell-centred finite volume, first-order upwind advection, centred diffusion.
Not supplied to the solving agent. No inverse solver or candidate grading here.
"""
import numpy as np
def states(scene, source, sample_days):
    nx,ny,nz=scene['grid']['shape_xyz']; dx,dy,dz=scene['grid']['spacing_m']
    x0,y0,z0=scene['grid']['origin_m']; dt=scene['time_step_days']
    x=x0+(np.arange(nx)+.5)*dx;y=y0+(np.arange(ny)+.5)*dy;z=z0+(np.arange(nz)+.5)*dz
    v=np.array([.07 if zz<-.5 else (.12 if zz<1.5 else .17) for zz in z])[None,None,:]
    R=np.array([1.5 if zz<-.5 else (1.2 if zz<1.5 else 1.) for zz in z])[None,None,:]
    overlaps=[]
    for a,h,centres,spacing in [(source['cx'],source['hx'],x,dx),(source['cy'],source['hy'],y,dy),(source['cz'],source['hz'],z,dz)]:
        overlaps.append(np.maximum(0,np.minimum(centres+spacing/2,a+h)-np.maximum(centres-spacing/2,a-h))/spacing)
    q=source['rate']*overlaps[0][:,None,None]*overlaps[1][None,:,None]*overlaps[2][None,None,:]/(8*source['hx']*source['hy']*source['hz']*scene['porosity'])
    C=np.zeros((nx,ny,nz)); snapshots={}; nsteps=round(max(sample_days)/dt); wanted=set(sample_days)
    for k in range(1,nsteps+1):
        mid=(k-.5)*dt
        # Incoming concentration is zero at x_min; outflow uses zero gradient at x_max.
        px=np.pad(C,((1,1),(0,0),(0,0)),mode='edge');px[0]=0
        py=np.pad(C,((0,0),(1,1),(0,0)),mode='edge')
        pz=np.pad(C,((0,0),(0,0),(1,1)),mode='edge')
        diff=scene['D_xyz'][0]*(px[2:]-2*C+px[:-2])/dx**2+scene['D_xyz'][1]*(py[:,2:]-2*C+py[:,:-2])/dy**2+scene['D_xyz'][2]*(pz[:,:,2:]-2*C+pz[:,:,:-2])/dz**2
        rhs=diff-v*(C-px[:-2])/dx-source['decay']*C
        if source['t_start']<=mid<source['t_start']+source['duration']:rhs=rhs+q
        C=C+dt*rhs/R
        day=k*dt
        if day in wanted:snapshots[day]=C.copy()
    return snapshots
'''

def science(out):
    p=candidate(out,'layered_aquifer_source_lab','Scientific Problems & ML','分层含水层中的有限时污染源反演',
      'borden_source_inversion',[source('modflow6-examples',['scripts/ex-gwt-moc3d-p02.py','doc/sections/ex-gwt-moc3d-p02.tex'])],
      ['构造守恒前向模型与可用答案','联合反演源几何、释放时间和强度','处理检测限、分层输运与空间/时间外推'],
      ['Numerical reference fidelity/convergence and inverse identifiability remain unaudited.','Reference inverse solution and executable scoring still pending.'])
    scene={'name':'Layered-62','grid':{'shape_xyz':[31,17,9],'spacing_m':[2,2,1],'origin_m':[0,-17,-4.5]},
      'porosity':.25,'D_xyz':[.12,.025,.008],'time_step_days':.25,
      'layers':[{'z_max':-.5,'vx':.07,'R':1.5},{'z_min':-.5,'z_max':1.5,'vx':.12,'R':1.2},{'z_min':1.5,'vx':.17,'R':1.0}],
      'observation_operator':'cell average at named grid index; x/y/z coordinates identify cell centres',
      'noise':{'multiplicative_log_sd':.08,'detection_limit_g_m3':.0003},'units':['m','day','g/m3'],
      'initial':'zero concentration','boundary':'zero inlet concentration; zero concentration gradient at outlet; zero normal flux at y/z boundaries'}
    bounds={'cx':[5,16],'cy':[-3,3],'cz':[-2,2],'hx':[1,5],'hy':[.5,2.5],'hz':[.3,1.5],
      'rate':[.01,.2],'t_start':[0,40],'duration':[30,120],'decay':[0,.005]}
    truth={'cx':9.2,'cy':.8,'cz':-.4,'hx':3.4,'hy':1.3,'hz':.8,'rate':.08,'t_start':18.,'duration':72.,'decay':.0015}
    dump(p/'public/scene.json',scene);dump(p/'public/source_bounds.json',bounds);dump(p/'private/truth.json',truth)
    write(p/'private/generate_scene.py',FV_GENERATOR)
    scope={};exec(FV_GENERATOR,scope)
    days_public=list(range(50,401,50));days_final=list(range(75,526,50))
    states=scope['states'](scene,truth,sorted(set(days_public+days_final)))
    rng=random.Random(2026101405);used=set();counts={}
    for split,nw,days in [('public',12,days_public),('feedback',12,days_public),('audit',18,days_final)]:
        rows=[]
        while len(rows)<nw*len(days):
            ijk=(rng.randrange(8,29),rng.randrange(5,12),rng.randrange(1,8))
            if ijk in used:continue
            used.add(ijk);i,j,k=ijk;well=f'{split}_{len(rows)//len(days):02d}'
            for day in days:
                c=float(states[day][ijk]);obs=c*math.exp(rng.gauss(0,.08)) if split=='public' else c
                cens=split=='public' and obs<.0003
                rows.append([well,i,j,k,1+2*i,-16+2*j,-4+k,day,'' if cens else obs,int(cens),.0003])
        b=io.StringIO();w=csv.writer(b);w.writerow(['well','ix','iy','iz','x','y','z','day','concentration','below_detection','detection_limit']);w.writerows(rows)
        write(p/('public' if split=='public' else 'private')/f'{split}_observations.csv',b.getvalue());counts[split]=len(rows)
    dump(p/'private/generation_record.json',{'seed':2026101405,'synthetic':True,'model':'original finite-volume layered ADE, not a MODFLOW execution','counts':counts,'numerically_validated':False})
    dump(p/'public/submission/answer.json',{k:sum(v)/2 for k,v in bounds.items()})
    write(p/'public/submission/solve.py','''"""Implement physical model + inverse solver; write answer.json after improvement."""
if __name__=='__main__':
    raise NotImplementedError('Implement the public PDE and inference procedure')
''')
    write(p/'public/physics.md','''Equation: R(z) dC/dt = Dx C_xx + Dy C_yy + Dz C_zz - vx(z) C_x - lambda C + q(x,y,z,t)/porosity.
R, vx, porosity and D are public and fixed. Unknown source is a uniform rectangular region with centre c and half-widths h, active on [t_start,t_start+duration).
rate is TOTAL mass per day; q=rate/(8*hx*hy*hz) inside the region and zero outside. decay has units day^-1.
Use the public grid and boundary conventions. At interfaces C and normal diffusive flux are continuous; v is parallel to interfaces.
The inlet boundary's discrete ghost cell concentration is zero; the outlet and transverse ghost cells copy the adjacent cell. Public grid indices are zero-based.
Observations are cell averages; fractional source-cell overlap matters. A below_detection record means [0,detection_limit), not an exact zero observation.
The private generating discretization is first-order upwind advection and centred diffusion; agents may use a conservative equivalent or more accurate numerical approximation.
Useful public self-checks: zero source preserves zero; no source/decay/flux preserves total sum(porosity*R*C*cell_volume); diffusion of a pulse smooths without negative concentrations.
''')
    finish(p,'''# 从观测重建污染源

根据 scene.json 的分层流速/滞后系数、网格、边界和 physics.md 的方程，自己实现前向输运模型，再利用 public_observations.csv 反演有限时长方体源。公开包不提供可调用的前向求解器。数据是本项目生成的合成观测，包含带噪实值与检测限删失记录。

提交 submission/answer.json 和 submission/ 内的推断源码、诊断结果。评分读取答案，在独立前向程序中计算新井位和未来时间预测；源码用于复现审阅，不能通过修改评分程序影响分数。所有源参数必须满足 source_bounds.json，源必须整体位于域内。

你可以先实现一维/均质近似取得可用解，再引入分层、源体积与离散守恒，最后改善删失似然、多起点反演和外推。每次更好的参数都应立即写入 answer.json。核心分来自隐藏预测质量，而不是报告篇幅或方程文本。预算 6 小时。
''','''# 长程潜力与素材依据

从 MOC3D/Wexler 三维输运材料出发，构造新的公开物理场景；保留 Borden 的“模型建设→有限体积源反演→外推”能力链。新生成器在 private，公开明确方程、边界、观测算子与误差机制，不能用未说明的隐藏物理增加难度。

本轮实际生成了分层网格观测与隐藏标签，没有运行反演或给候选评分。计算代码是独立构造的低阶参考，不是已经验证的科学真值。需要后续出题审计数值收敛、可辨识性和非退化井位。与上一版相比，核心变化是恢复前向模型建设并加入有物理意义的分层、守恒与检测限；不是仅增加未知数。
''',{'formula':'valid/(1+0.5*relative_rmse**2+0.5*log_rmse**2)',
      'relative_rmse':'sqrt(mean((pred-true)^2))/max(sqrt(mean(true^2)),1e-6)',
      'log_rmse':'sqrt(mean((log1p(pred/0.0003)-log1p(true/0.0003))^2))',
      'physical_self_checks':'public debugging guidance only; no extra credit for unexecuted model claims',
      'constants':{'floor':1e-6,'log_scale':.0003,'relative_mse_weight':.5,'log_mse_weight':.5},
      'validity_gate':['finite bounded parameters','source inside domain','nonnegative finite predictions'],
      'feedback_deadline_target_seconds':300,'reference_numerics_pending':True})
    return p

def packing(out):
    p=candidate(out,'industrial_nesting_improvement','Combinatorial Optimization','工业异形排样的基线突破',
      'jagua_nesting_optimization',[source('packingsolver',['src/irregular/optimize.cpp','src/irregular/local_search.cpp'])],
      ['稳定输出可行排样并建立性能画像','改进初始布局与搜索邻域','在固定预算下跨设计族改进并超越冻结参考'],
      ['Frozen reference lengths have not been measured.','Independent geometry checks and data-rights review pending.'])
    repo_snapshot('packingsolver',p/'public/repo',exclude=('data','test','tests','images','docs','scripts','web'))
    old=OLD/'industrial_irregular_strip';manifest=json.loads((old/'private/case_manifest.json').read_text());rows=[]
    split_of={'chair':'public','stool_x10':'public','stepladder':'public','adirondack_chair':'feedback','deer':'feedback',
      'sofa_structure':'audit','knight_body':'audit','knight_armor':'audit','table':'audit'}
    for r in manifest:
        oldfolder='public/cases' if r['split']=='public' else 'private/'+r['split']+'_cases'
        original=json.loads((old/oldfolder/(r['id']+'.json')).read_text()); split=split_of[r['id']]
        for multiplier in [1,2,3]:
            d=json.loads(json.dumps(original))
            for item in d['item_types']:item['copies']=item.get('copies',1)*multiplier
            d['bin_types'][0]['width']*=multiplier
            ident=r['id']+f'_order{multiplier}'
            dst=p/('public/cases' if split=='public' else 'private/'+split+'_cases')/(ident+'.json');dump(dst,d)
            rows.append(dict(id=ident,source_design=r['id'],family='knight' if r['id'].startswith('knight') else r['id'],split=split,
              order_multiplier=multiplier,pieces=r['items']*multiplier,area=r['total_item_area']*multiplier,height=r['strip_height'],
              lower_bound=r['area_lower_bound_length']*multiplier,reference_length=None,sha256=sha(dst)))
    dump(p/'private/workloads.json',rows)
    dump(p/'private/reference_lock.json',{'source':source('packingsolver',['src/irregular/optimize.cpp']),
         'same_per_case_cpu_budget_seconds':20,'threads':1,'seed':4187,'baseline_lengths':None,'run_status':'not_executed'})
    finish(p,'''# 在固定预算下突破异形排样基线

修改真实 PackingSolver irregular 求解器，目标为 fixed-height open-dimension-x。每例必须放入全部零件、遵守旋转/镜像限制并保持几何可行。保持 CLI 与 certificate 格式；提交 repo/src/irregular/ 与 repo/include/packingsolver/irregular/。

每个生产订单单线程 20 秒，固定种子，与冻结的原始求解器使用同一资源预算。无效或遗漏的例子记零且不从分母删除。有效性占 20%，剩余 80% 衡量相对原始参考布局缩短的长度；原样提交基线无法获得改进分。评分器独立验证轮廓，不能相信候选自己报告的面积、相交或长度。

公开订单来自椅具、凳具和梯具；反馈及审计使用独立设计族。订单大小变化是同一道任务的工作负载，不算新题。可从 profile、初始布局、排序、邻域、重启与几何查询加速逐步推进。不得缓存隐藏实例的答案表。预算 6 小时。
''','''# 长程潜力与素材依据

保留真实求解器工程、固定时间预算和独立几何验证，把评分改为与 Jagua 一致方向的“超越冻结参考”。9 份已有工业设计形成 27 个订单；按几何来源族整体分区，knight_body 与 knight_armor 同属 audit。增加订单用来暴露算法取舍，不把它当作长程难度证据。

形状数量有限仍是候选风险：必须检查公开几何是否足以支撑改进、基线是否留有空间，后续继续寻找独立工业设计。参考源版本已固定但未运行，L_ref 仍为空，当前不能评分。构造配方借用 ProgramBench 的冻结参考与接口契约，复杂算法和工作负载选择仍需出题 agent 判断。OpenCutList 数据单独的再分发授权尚待核对。
''',{'formula':'mean(valid_i*(0.2+0.8*clip((L_ref_i-L_i)/max(L_ref_i-LB_i,epsilon_i),0,1)))',
      'lower_bound':'total_item_area/strip_height','epsilon_i':'max(1e-9,1e-6*L_ref_i)',
      'constants':{'validity_weight':.2,'improvement_weight':.8,'seed':4187,'seconds_per_case':20,'threads':1},
      'baseline_endpoint':'unchanged feasible baseline = 0.2; not empirically measured',
      'feedback_cases':6,'feedback_deadline_target_seconds':300,'reference_lengths_pending':True})
    return p

def mask_lean(src,names):
    starts=list(re.finditer(r'(?m)^(?:(?:lemma|theorem|def|end|section|namespace|noncomputable|variable|omit|open|include|nonrec|attribute)\b|@\[|/--|/-!)',src));edits=[];records=[]
    for name in names:
        m=re.search(r'(?m)^(?:lemma|theorem) '+re.escape(name)+r'(?=\s|\{)',src);assert m,name
        end=next((x.start() for x in starts if x.start()>m.start()),len(src));block=src[m.start():end]
        sep=block.find(':= by')
        if sep<0:sep=block.find(':=\n')
        assert sep>=0,name
        edits.append((m.start()+sep+2,end,' by\n  sorry\n\n'))
        records.append({'name':name,'signature':block[:sep].strip(),'proof_lines':block[sep:].count('\n')})
    for a,b,s in sorted(edits,reverse=True):src=src[:a]+s+src[b:]
    return src,records

def formal(out):
    old_targets=json.loads((OLD/'kolmogorov_holder_modification/private/targets.json').read_text())
    groups={
      'covariance':('BrownianMotion/Gaussian/CovMatrix.lean',['covarianceBilin_apply_prod','covMatrix_mulVec','dotProduct_covMatrix_mulVec','covMatrix_map','posSemidef_covMatrix']),
      'covering':('BrownianMotion/Continuity/CoveringNumber.lean',['TotallyBounded.coveringNumber_ne_top','coveringNumber_Icc_zero_one_le_one_div','volume_le_of_isCover','le_volume_of_isSeparated','coveringNumber_closedBall_le']),
      'moment':('BrownianMotion/Gaussian/Moment.lean',['centralMoment_two_mul_gaussianReal']),
      'process':('BrownianMotion/Gaussian/BrownianMotion.lean',['HasIndepIncrements.isGaussianProcess','IsPreBrownianReal.isAEKolmogorovProcess','IsBrownianReal.inv','ContinuousMap.borel_eq_iSup_comap_eval']),
      'continuity':(old_targets[0]['file'],[x['name'] for x in old_targets])}
    p=candidate(out,'brownian_multibranch_proofs','Formal Math & Theorem Proving','布朗运动基础与连续性多分支证明',
      'lean_analysis_proofs',[source('brownian-motion',[v[0] for v in groups.values()])],
      ['独立协方差与覆盖引理','高斯矩估计和过程性质','Hölder 修正及综合结果'],
      ['Lean compilation, actual dependency graph and shortcut audit remain pending.','Original benchmark theorem inventory not fully acquired; exact deduplication pending.'])
    repo_snapshot('brownian-motion',p/'public/repo',exclude=('Manuscript','verso','blueprint'))
    targets=[]
    for group,(f,names) in groups.items():
        src=(REPOS/'brownian-motion'/f).read_text();masked,rr=mask_lean(src,names)
        copy(REPOS/'brownian-motion'/f,p/'private/reference'/f);write(p/'public/repo'/f,masked)
        for r in rr:r.update(file=f,group=group);targets.append(r)
    dump(p/'public/targets.json',targets)
    # This is a lexical authoring aid, never a substitute for Lean dependency closure.
    deps=[]
    for a in targets:
        for b in targets:
            if a is not b and b['name'] in a['signature']:deps.append([a['name'],b['name']])
    dump(p/'private/dependency_audit_pending.json',{'status':'kernel graph not measured','signature_text_references_only':deps,'required':'collect transitive axioms and exact constant dependencies from elaborated declarations'})
    finish(p,'''# 完成布朗运动构造的多个证明分支

在固定 BrownianMotion 项目中补全 targets.json 的 31 个目标，覆盖 5 个 Lean 文件。可从协方差和覆盖引理开始，也可以推进高斯矩、过程性质或连续修正；这些分支为增量得分提供不同切入点，最终需要处理跨文件依赖。

提交 targets.json 列出的五个源文件，可在文件内增加辅助 lemma。冻结既有声明的类型、定义、import 和依赖版本；不允许新增公理、绕过 kernel 或引用未授权的外部答案。允许未完成目标暂留 sorry，但一个目标只有在传递公理闭包中不含 sorryAx 且仅使用 propext、Classical.choice、Quot.sound 时计分。

每组内按目标完成比例计分。高斯矩与过程性质合占 20%，协方差 20%，覆盖 20%，连续修正 40%。补全后自行构建并检查公理依赖，提交快照即可。预算 6 小时。
''','''# 长程潜力与素材依据

当前实际挖空 31 个真实证明，分布于协方差、覆盖数、高斯矩、布朗过程、Hölder 修正五个文件。完整原证明私有保留，签名、库版本和目标清单公开；使用与原题一致的传递公理计分机制。

比上一版的单文件链增加了独立数学切入点，不预设“31 个一定要花 6 小时”。分支独立性与可绕过程度仍需 elaborated dependency graph 确认，文本扫描不能证明。上游证明公开，后续训练集划分应按项目/定理族隔离，不能把恢复公开证明称为新数学发现。
''',{'formula':'0.2*covariance_completion+0.2*covering_completion+0.2*mean(moment_and_process_target_completion)+0.4*continuity_completion',
      'groups':{'covariance':.2,'covering':.2,'moment_and_process':.2,'continuity':.4},
      'allowed_axioms':['propext','Classical.choice','Quot.sound'],'feedback_deadline_target_seconds':600,'partial_proof_credit':'only fully kernel-closed targets count'})
    return p

def finance(out):
    repo=REPOS/'portfolio-risk-engine';fs=['results/prices.csv','results/prices_source.txt','src/portrisk/backtest.py','src/portrisk/optimization.py']
    p=candidate(out,'cross_asset_adaptive_allocator','Professional Knowledge Work','跨资产风险自适应配置与成本控制',
      'portfolio_risk_calibration',[source('portfolio-risk-engine',fs)],
      ['因果账本和可行配置','风险校准驱动的约束优化','成本感知再平衡和市场状态适应'],
      ['Price cache is attributed upstream to yfinance; provider-level accuracy and training redistribution rights unconfirmed.','Trusted execution/accounting reference and evaluator still need construction.'])
    with (repo/'results/prices.csv').open() as f:r=csv.reader(f);header=next(r);rows=list(r)
    split={'train':[r for r in rows if r[0]<'2016-01-01'],'dev':[r for r in rows if '2016-01-01'<=r[0]<'2020-01-01'],
      'feedback':[r for r in rows if '2020-01-01'<=r[0]<'2023-01-01'],'audit':[r for r in rows if '2023-01-01'<=r[0]<'2026-01-01']}
    counts={}
    for name,data in split.items():
        b=io.StringIO();w=csv.writer(b);w.writerow(header);w.writerows(data);write(p/('public/data' if name in ['train','dev'] else 'private/data')/(name+'_prices.csv'),b.getvalue());counts[name]=len(data)
    copy(repo/'src/portrisk',p/'private/source_reference/portrisk');copy(repo/'LICENSE',p/'private/source_reference/LICENSE')
    dump(p/'private/data_lineage.json',{'source_sha256':sha(repo/'results/prices.csv'),'upstream_declared_source':(repo/'results/prices_source.txt').read_text(),'independently_verified_market_prices':False,'counts':counts,'rights':'repository MIT covers code; underlying market-data terms not established'})
    mandate={'assets':header[1:],'groups':{'equity':['SPY','IWM','EFA','EEM'],'bonds':['TLT'],'commodity':['GLD','DBC'],'real_estate':['VNQ']},
      'asset_abs_cap':.30,'TLT_abs_cap':.45,'class_gross_caps':{'equity':.65,'bonds':.45,'commodity':.30,'real_estate':.20},
      'gross_leverage_cap':1.6,'short_gross_cap':.25,'net_risky_exposure_bounds':[.4,1.2],
      'shortable':['SPY','IWM','EFA','EEM','GLD','DBC','VNQ'],'cash_weight':'1-sum(risky_weights)',
      'cost_per_abs_weight_change':.0005,'short_borrow_annual':.03,'negative_cash_financing_annual':.05,'year_days':252,
      'risk_scale_bounds':[.7,2.2],'risk_target_annual':.10,'rebalance_review_days':20,'min_extra_rebalance_gap_days':5,
      'initial_nav':1000000,'execution':'decision uses prices through t-1; trades at observed t-1 close; holdings receive day t returns; costs deducted once'}
    dump(p/'public/mandate.json',mandate)
    write(p/'public/submission/policy.py','''"""Implement initialize(metadata) and decide(history, state).
history includes prices only through previous close; state contains drifted weights,
cash, NAV and past execution/forecast records supplied by the trusted simulator.
Return all asset weights, risk_scale, variance_daily, q05_daily and rebalance_reason.
All returned numbers must be finite; submitted forecasts are stored before outcomes.
"""
def initialize(metadata): return {}
def decide(history, state):
    raise NotImplementedError('Implement risk model, constrained allocator and rebalance policy')
''')
    write(p/'public/accounting.md','''The trusted ledger, not the candidate's reported NAV, determines score.
At each t, candidate sees history through t-1, drifted pretrade weights and current NAV. If no rebalance, use drifted weights; do not silently restore yesterday's target.
Trading cost fraction = 0.0005*sum(abs(target-pretrade)); borrow fraction=0.03/252*sum(max(-w,0)); financing=0.05/252*max(-cash_weight,0).
Let net capital after these costs be NAV_net. New risky and cash amounts are NAV_net*w and NAV_net*cash_weight. Apply observed close-to-close returns; cash has zero return.
New NAV equals cash + sum(marked risky holdings); derive next drifted weights from those holdings. Fees must never be charged twice.
Weight constraints apply after cost normalization. Insufficient history must produce feasible conservative allocations, not missing days.
Policy must emit forecasts before the next return. VaR is a 5% return quantile (normally negative); a breach means realized return < forecast quantile.
Cold start and data gaps are explicit cases. No forward filling using future rows and no date-to-weight lookup. Execution is offline.
''')
    finish(p,'''# 构造完整的风险自适应配置系统

使用公开 train/dev 历史和 mandate.json，构造包含风险校准、约束配置、执行成本、动态再平衡的完整政策。资产覆盖股票、国债、黄金/商品、地产，并有现金账户；这是一项研究工程任务，不是投资建议。

实现 submission/policy.py，可在 submission/ 中增加模块与离线参数文件。输出所有资产权重、风险缩放因子、波动/尾部预测及调仓原因。规模上限、可做空资产、借券与融资成本、时间因果约束见 mandate.json 和 accounting.md。风险缩放增大应降低目标风险预算：target_vol=0.10/risk_scale。

评分器以逐日历史调用你的政策，独立记账并生成 NAV、交易、风险预测和调仓记录，不能相信你自行填的回测成绩。基本接口、约束与记账测试提供部分分；主要分来自相对固定基线的净风险调整表现及风险校准。可以先完成可行配置，再改善协方差/尾部、优化器、换手与状态触发。预算 6 小时。

数据来自上游公开缓存并标注 yfinance，尚未与供应商原始数据逐值核验。本候选用于本地研究审阅，进入训练分发前还需确认数据许可。
''','''# 长程潜力与素材依据

新取得的八资产价格缓存覆盖 SPY/IWM/EFA/EEM/TLT/GLD/VNQ/DBC，恢复跨资产结构；没有继续用 49 个股票行业假装替代跨资产任务。完整代码与上游风险/优化模块作为作者参考保存在 private，不向 agent 暴露全时段价格、全样本权重或上游成绩。

采用新的资产集合、时间段和委托约束，保留原题四模块耦合：风险估计影响约束配置，成本影响调仓，调仓影响回撤和校准。长期空间来自方法诊断和系统协同，而非历史行数。独立账本与真实参考政策尚待实现；当前是资料和契约齐备的候选，未形成可运行评分器。金融数据授权仍是转入正式训练的材料门槛。
''',{'formula':'valid*(0.25*functional_fraction+0.60*clip((U-U_ref)/0.10,0,1)+0.15/(1+scaled_pinball))',
      'U':'252*mean(log(net_daily_growth))-0.5*sqrt(252)*std(daily_return)-max_drawdown',
      'scaled_pinball':'mean((0.05-I[r<q])*(r-q))/0.01',
      'constants':{'functional_weight':.25,'utility_weight':.60,'calibration_weight':.15,'utility_scale':.10,'pinball_scale':.01,'quantile':.05},
      'reference':'frozen feasible static allocation with same accounting, not yet executed',
      'feedback_deadline_target_seconds':300,'normalization_status':'proposed; empirical endpoints pending'})
    return p

def game(out):
    repo=REPOS/'wesnoth-1.18.0'
    p=candidate(out,'wesnoth_frontier_campaign_ai','Interactive Games & Simulators','Wesnoth 多地形经济与战术 AI',
      'wesnoth_tactical_ai',[source('wesnoth-1.18.0',['data/ai/ais/ai_default_rca.cfg','data/multiplayer/scenarios/2p_The_Freelands.cfg'])],
      ['合法 CA 与招募/占村经济','地形、时段与阵营驱动的战术协同','多场景稳健性、胜率与获胜效率'],
      ['Authored WML/maps have not been loaded by the game; fairness/playability and match cost are unmeasured.','Engine dependencies and immutable scenario/verifier packaging pending.'])
    copy(repo/'data/ai/lua',p/'public/api_examples/ai_lua')
    for name in ['COPYING','COPYING.txt','LICENSE']:
        if (repo/name).exists():copy(repo/name,p/'public'/name)
    starter=(repo/'data/ai/ais/ai_default_rca.cfg').read_text()
    starter=starter.replace('id=ai_default_rca\n','id=my_custom_ai\n',1)
    write(p/'public/submission/my_custom_ai.cfg',starter)
    catalog=[]
    for split in ['public','feedback','audit']:
        v=['public','feedback','audit'].index(split)
        for family in ['river_crossings','forest_flanks','open_economy']:
            n=25;grid=[['Gg' for _ in range(n)] for _ in range(n)]
            for y in range(n):
                for x in range(n):
                    if family=='river_crossings' and x in [11,12,13]:grid[y][x]='Ww' if y not in [6+v,18-v] else 'Wwf'
                    if family=='forest_flanks' and (x+2*y+v)%7 in [0,1]:grid[y][x]='Gs^Fp'
                    if family=='forest_flanks' and (2*x+y+v)%11==0:grid[y][x]='Hh'
                    if family=='open_economy' and (x-y+v)%9==0:grid[y][x]='Hh'
            # Exact rotational terrain symmetry in odd-width layout; game fairness still unverified.
            for y in range(n):
                for x in range(n):
                    if y*n+x<(n-1-y)*n+(n-1-x):grid[n-1-y][n-1-x]=grid[y][x]
            for side,(x,y) in enumerate([(3,12),(21,12)],1):
                for ox,oy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1)]:grid[y+oy][x+ox]='Ch'
                grid[y][x]=f'{side} Kh'
            villages=[(6,5+v),(7,18-v),(9,11),(5,9),(10,4+v)] if family!='open_economy' else [(5,4),(8,7+v),(10,17-v),(6,20),(11,10)]
            for x,y in villages:
                for xx,yy in [(x,y),(n-1-x,n-1-y)]:grid[yy][xx]='Gg^Vh'
            ident=f'frontier_{family}_{split}';folder=p/('public/scenarios' if split=='public' else f'private/{split}_scenarios')
            write(folder/(ident+'.map'),'\n'.join(', '.join(row) for row in grid)+'\n')
            map_text='\n'.join(', '.join(row) for row in grid)
            wml=f'''[multiplayer]
    id={ident}
    name="{ident}"
    map_data="{map_text}"
    turns=45
    random_start_time=no
    {{DEFAULT_SCHEDULE}}
    [side]
        side=1
        controller=ai
        team_name=one
        canrecruit=yes
        gold=100
        fog=no
        shroud=no
    [/side]
    [side]
        side=2
        controller=ai
        team_name=two
        canrecruit=yes
        gold=100
        fog=no
        shroud=no
    [/side]
[/multiplayer]
'''
            write(folder/(ident+'.cfg'),wml)
            catalog.append({'id':ident,'family':family,'split':split,'map_sha256':sha(folder/(ident+'.map')),'new_map':True})
    dump(p/'private/scenarios.json',catalog)
    dump(p/'public/match_contract.json',{'engine_version':'1.18.0','era':'era_default','faction_pairings':[['Loyalists','Rebels'],['Rebels','Northerners']],
       'canonical_feedback':{'maps':3,'pairings':2,'paired_seats':2,'seeds':[17],'games':12},
       'audit':{'maps':3,'pairings':2,'paired_seats':2,'seeds':[29,61,101],'games':36},
       'turn_cap':45,'per_game_wall_cap_seconds':40,'feedback_wall_cap_target_seconds':600,
       'timeout_policy':'timeout is infrastructure/budget diagnostic, not automatically a draw; exact forfeit behavior must be fixed before acceptance'})
    finish(p,'''# 开发跨场景的 Wesnoth 战术 AI

使用 Wesnoth 1.18.0 的 Lua Candidate Action 接口，开发能处理河道争夺、森林侧翼和开阔地占村经济的 AI。三种新地形族各有公开、反馈和审计场景；阵营配对和双座位测试要求策略适应兵种、时段与地形，而不是为一个起点硬编码行动。

提交 submission/ 下 my_custom_ai.cfg 与引用的任意 Lua 模块。保留引擎和固定场景，禁止 wml_actions、game_events、os.execute、io.open、debug 等修改环境或绕过决策的接口。公开 api_examples 提供官方 AI 实现作为接口学习材料。可以先保留默认 CA，再逐步替换招募、占村、集火、治疗/撤退和领袖保护。

固定反馈集合共 12 局，胜率占 80%，赢局效率占 20%；效率按固定 45 回合上限归一化，失败不获得效率分。完整跨种子审计另行进行，不用每次提交跑满所有比赛。得分来自 verifier 重新加载提交源码并完成对局，不依赖 agent 容器的活进程。预算 6 小时。
''','''# 长程潜力与素材依据

从 microRTS 回到原题相同的 Wesnoth 引擎、Lua CA 与默认 AI 机制；变化放在新地形、阵营配对和双座位泛化上。官方 1.18.0 源版本、AI 例程和 WML 语法参照已下载，新生成 9 张地图/场景，未复制原题的三张地图。

三类地形分别要求河道通过顺序、地形防御与侧翼、占村经济和招募配置；中后期可以继续改进战术配合和获胜效率。每次反馈从上一版 96 局减为固定 12 局，仍需实测耗时以免 agent 大部分时间等待。40 秒单局 cap、WML 启动、阵营 ID、座位公平性均未运行验证。

地图和 API 禁令属于构造规格，不能替代隔离执行器。官方代码和派生素材须保留对应 GPL 许可。新场景的可达性/平衡和廉价必胜策略应在下一阶段审查。
''',{'formula':'mean(0.8*win+0.2*win*max(0,(45-turns_to_win)/44))','constants':{'win_weight':.8,'efficiency_weight':.2,'turn_cap':45,'earliest_turn':1},
       'draw_score':0,'loss_score':0,'feedback_matches':12,'feedback_deadline_target_seconds':600,'baseline_score':None})
    return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for build in [software,science,packing,formal,finance,game]:
        p=build(out);d=json.loads((p/'candidate.json').read_text());rows.append({k:d[k] for k in ['task_id','category','title','status','construction_gaps']})
        dump(p/'material_manifest.json',[dict(path=str(f.relative_to(p)),sha256=sha(f),bytes=f.stat().st_size) for f in sorted(p.rglob('*')) if f.is_file()])
        print('constructed candidate',p.name,flush=True)
    dump(out/'index.json',rows);dump(out/'recipe.json',{'script':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__)),'model_runs':0,'runtime_validation_runs':0})
    print('Six candidate packages saved; no runtime or six-hour validation claimed.')

if __name__=='__main__':main()
