"""Material-to-task pilot. Constructs files only; does not run task solutions/tests.

Run with a fresh --output directory. Source repositories must already be pinned
under materials/repos. This is an authored construction recipe, not an autonomous
LLM factory or evidence of runtime/difficulty acceptance.
"""
from pathlib import Path
import argparse, ast, csv, hashlib, io, json, math, random, re, shutil, subprocess, zipfile

ROOT = Path(__file__).resolve().parents[1]
REPOS = ROOT / 'materials/repos'

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding='utf-8')

def dump(path, data):
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.git', '__pycache__', '.lake', 'node_modules'))
    else:
        shutil.copy2(src, dst)

def repo_snapshot(name, dst, exclude=()):
    src = REPOS / name
    dst.mkdir(parents=True)
    for p in src.iterdir():
        if p.name.startswith('.') or p.name in exclude:
            continue
        copy(p, dst / p.name)

def source(name, files):
    p = REPOS / name
    git = lambda *args: subprocess.check_output(['git', '-C', str(p), *args], text=True).strip()
    return {'repository': git('remote', 'get-url', 'origin'), 'commit': git('rev-parse', 'HEAD'),
            'files': [{'path': f, 'sha256': sha(p/f)} for f in files],
            'acquired': True, 'runtime_verified': False}

def base(out, task_id, category, title, anchor, inputs, method, gap, submit, formula, constants, checks):
    p = out/task_id
    (p/'public').mkdir(parents=True)
    (p/'private').mkdir()
    dump(p/'construction.json', {
        'task_id': task_id, 'category': category, 'title': title,
        'status': 'constructed_unverified', 'original_anchor': anchor,
        'sources': inputs, 'construction_method': method,
        'authoring': {'mode': 'interactive_agent_source_inspection_and_scripted_transformation',
                      'independent_cli_model_called': False},
        'similarity_claim': 'mechanism-level design hypothesis, not empirically same-distribution',
        'known_gap': gap, 'runtime_validation': 'deferred_by_user',
        'difficulty_calibrated': False, 'accepted': False,
        'redistribution_review': 'See SOURCE_TO_TASK.md; repository license does not automatically license all third-party data.'})
    dump(p/'public/evaluation_contract.draft.json', {
        'schema': 'local-authoring-draft-v1-not-Harbor', 'task_id': task_id,
        'agent_budget_seconds': 10800, 'submit_paths': submit,
        'snapshot_only': True, 'verifier_stateless': True,
        'runtime_network': {'agent': 'none', 'verifier': 'none'},
        'run_aggregation': 'max(valid_submission_scores)',
        'curve': 'elapsed_interaction_seconds,best_score_so_far',
        'score': {'direction': 'higher_is_better', 'range': [0,1], 'formula': formula,
                  'constants': constants, 'raw_metrics_required': True,
                  'baseline_measured': None, 'upper_endpoint_measured': None,
                  'normalization_policy': 'fixed_bounded_formula_v1; empirical endpoints pending'},
        'named_checks': checks,
        'feedback_schema': {'score': 'finite number in [0,1]', 'valid': 'boolean',
                            'checks': [{'name': 'string', 'pass': 'boolean', 'summary': 'string'}],
                            'raw_metrics': 'object', 'summary': 'string'},
        'invalid_submission': 'valid=false, score=0, named diagnostics',
        'verifier_failure': 'separate infrastructure error, never silently score zero',
        'feedback_policy': 'aggregate by named group; never return hidden inputs or target values',
        'pending_delivery': ['official Harbor schema/network fields', 'two Docker build contexts',
                             'offline dependency closure and dual-architecture digests',
                             'oracle/nop scores and repeated-model curves']})
    return p

def system(out):
    files = ['restler/engine/core/async_request_utilities.py', 'restler/engine/core/preprocessing.py',
             'restler/engine/dependencies.py']
    p = base(out, 'restler_resource_lifecycle', 'Systems & Software Engineering',
        '恢复 RESTler 异步资源与 create-once 生命周期', 'schemathesis_datagen_pipeline',
        [source('restler-fuzzer',files)], 'DeepSWE ablation: coherent lifecycle slice, AST body removal, private inverse patch',
        'RESTler stateful fuzzing differs from the original Schemathesis project; difficulty and test coverage unmeasured.',
        ['repo/restler/engine/core/async_request_utilities.py','repo/restler/engine/core/preprocessing.py','repo/restler/engine/dependencies.py'],
        'sum(group_weight[g]*passed_checks[g]/total_checks[g])', {'group_weights': {'polling':.35,'create_once':.4,'cache':.25}},
        ['snapshot_scope','import_contract','polling','create_once','cache','regression'])
    repo_snapshot('restler-fuzzer', p/'public/repo', exclude=('restler',))
    copy(REPOS/'restler-fuzzer/restler', p/'public/repo/restler')
    # Preserve upstream tests in private reference; do not expose fixtures as answers.
    tests = p/'public/repo/restler/unit_tests'
    if tests.exists():
        shutil.move(str(tests),str(p/'private/upstream_unit_tests'))
    selected = {
        files[0]: ['get_polling_request','make_GET_request','try_parse_GET_request','try_async_poll'],
        files[1]: ['apply_create_once_resources'],
        files[2]: ['clear_saved_local_dyn_objects','start_saving_local_dyn_objects','stop_saving_local_dyn_objects','set_saved_dynamic_objects']}
    records=[]
    for f,names in selected.items():
        src=REPOS/'restler-fuzzer'/f; text=src.read_text(); lines=text.splitlines(keepends=True)
        edits=[]
        for node in ast.parse(text).body:
            if isinstance(node,ast.FunctionDef) and node.name in names:
                body=node.body
                if isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str): body=body[1:]
                start,end=body[0].lineno-1,node.end_lineno
                edits.append((start,end,'    raise NotImplementedError("Restore lifecycle behavior: '+node.name+'")\n'))
                records.append({'file':f,'symbol':node.name,'removed_lines':end-start,'original_span':[start+1,end]})
        assert len(edits)==len(names),f
        for start,end,replacement in reversed(edits): lines[start:end]=[replacement]
        write(p/'public/repo'/f,''.join(lines)); copy(src,p/'private/reference'/f)
    dump(p/'private/ablation_manifest.json', records)
    groups={
      'polling': ['Location on 201 returns resource payload','Location on 202 takes precedence over Azure-AsyncOperation',
                 'Azure status InProgress then Succeeded triggers resource GET','Failed status sets resource_error',
                 'deadline exhaustion terminates polling','disabled setting and zero timeout bypass polling',
                 'DELETE polling opt-in does not fetch deleted resource','missing token is not literal None in request',
                 'non-HTTPS polling URL rejected','malformed poll JSON does not crash fuzzing'],
      'create_once': ['missing endpoint raises InvalidCreateOnce with accumulated destructors',
                      'invalid rendering raises FailedToCreateResource','generator prerequisites computed in dependency order',
                      'consumers lock generated dynamic values','producers and destructors excluded from fuzzing',
                      'smoke-test coverage metadata preserved','saved resources survive normal garbage collection',
                      'no configured endpoints returns without side effects'],
      'cache': ['nested pause raises','stop without reset preserves saved cache','stop with reset releases saved cache',
                'clear while paused raises','release merges lists under optional lock','second global save raises']}
    dump(p/'private/check_roster.json', [{'group':g,'id':f'{g}_{i:02}','behavior':s,'oracle':'pinned original implementation; future deterministic mocked transport/clock'} for g,v in groups.items() for i,s in enumerate(v,1)])
    write(p/'public/instruction.md', '''# 恢复有状态 API 模糊测试的资源生命周期

RESTler 的请求渲染器、动态依赖、异步轮询和资源清理必须协同工作。当前工作区有 9 个函数的实现被移除。恢复这条完整功能链，使依赖刚创建资源的后续请求能安全执行，create-once 资源能跨测试序列保留，并在专门清理阶段释放。

修改范围为 evaluation_contract.draft.json 中的三个文件。保留所有公开函数签名、异常类型和调用者行为，可以在这三个文件内添加辅助函数。其余引擎、设置、transport 与 grammar 接口冻结。

具体行为：从 201/202 响应的 Location 或 Azure-AsyncOperation 选择轮询地址；保持当前库规定的 HTTPS 与认证头语义、两种响应模式和超时行为；轮询成功后向调用者提供可用于 parser 的响应列表；失败、删除轮询、无法解析和禁用轮询均须正确收尾。create-once 需要计算前置请求序列、渲染并保存产生的动态对象、锁定消费者引用、从 fuzzing 阶段排除生产/删除请求，并返回延后清理的 destructors。局部保存与全局保存的对象缓存必须遵守已有暂停/恢复、锁与重复保存规则。

从调用方、保留的 docstring、设置及用户文档恢复契约。提交修改后的源码快照，不提交运行中的服务。评分按 polling、create_once、cache 三组行为检查加权，回归破坏会反映在相应组的检查中。你可以自行添加本地测试；正式评分器固定且不接受提交覆盖。
''')
    write(p/'SOURCE_TO_TASK.md', '''# 素材 → 题目

真实素材：Microsoft RESTler 的固定 revision；三个核心文件、调用者、设置和文档均已落盘。MIT 许可证保留在 public/repo/LICENSE。

变换：从 Python AST 选取 9 个完整函数，保留签名与 docstring，删除实际实现。精确行段、移除行数见 private/ablation_manifest.json，完整参考源码见 private/reference。使用 DeepSWE 的“完整功能→消融→私有恢复依据”，借用 NL2Repo 的 AST 契约提取；没有假称运行了三个 factory 的完整控制器。

难度来自异步状态机、跨请求依赖、缓存与 GC 的协同，不来自随机删行。24 个行为检查已具名；还需要把检查实现成隔离的固定时钟/伪 transport 测试，覆盖与长程难度未校准。私有上游测试是出题依据，不能直接当作已验证 oracle。原 benchmark 的代码/数据未用于生成此任务；完整跨库重合检查仍待后续。
''')
    return p

def formal(out):
    f='BrownianMotion/Continuity/KolmogorovChentsov.lean'
    p=base(out,'kolmogorov_holder_modification','Formal Math & Theorem Proving',
        '形式化随机过程的 Hölder 连续修正','lean_analysis_proofs',[source('brownian-motion',[f,'lake-manifest.json','lean-toolchain'])],
        'dependency-linked proof ablation with exact original signatures and private proof reference',
        'Public upstream proofs may be in pretraining. Novel task packaging is not novel mathematics. Dependency closure and kernel acceptance deferred.',
        ['repo/'+f], 'sum(weight[t]*closed_without_unapproved_axioms[t])/sum(weight[t])',
        {'target_weights':'private/targets.json; all weights 1','allowed_axioms':['propext','Classical.choice','Quot.sound']},
        ['frozen_signatures','frozen_imports','kernel_check','axiom_closure','per_target_completion'])
    repo_snapshot('brownian-motion',p/'public/repo',exclude=('Manuscript','verso','blueprint'))
    src=(REPOS/'brownian-motion'/f).read_text(); copy(REPOS/'brownian-motion'/f,p/'private/reference'/f)
    names=['UniformContinuousOn.exists_tendsto','Dense.holderOnWith_extend',
      'IsKolmogorovProcess.measurableSet_holderSet','holderOnWith_of_mem_holderSet','ae_mem_holderSet',
      'IsKolmogorovProcess.tendstoInMeasure','isLimitOfIndicator_holderModification',
      'exists_tendsto_indicatorProcess_holderSet','measurable_holderModification',
      'holderOnWith_holderModification','measurable_pair_holderModification',
      'edist_holderModification_eq_zero','edist_modification_holderModification',
      'exists_modification_holder_aux\'','exists_modification_holder\'\'','exists_modification_holder']
    starts=list(re.finditer(r'(?m)^(?:(?:lemma|theorem|def|end|section|namespace|noncomputable|variable|omit|open)\b|/--|/-!)',src))
    records=[]; edits=[]
    for name in names:
        m=re.search(r'(?m)^(?:lemma|theorem) '+re.escape(name)+r'(?=\s|\{)',src); assert m,name
        end=next((n.start() for n in starts if n.start()>m.start()),len(src))
        block=src[m.start():end]; sep=block.find(':= by')
        if sep<0: sep=block.find(':=\n')
        assert sep>=0,name
        proofstart=m.start()+sep+len(':=')
        edits.append((proofstart,end,' by\n  sorry\n\n'))
        records.append({'name':name,'weight':1,'file':f,'signature':block[:sep].strip(),
                        'original_proof_lines':src[proofstart:end].count('\n'),
                        'original_proof_sha256':hashlib.sha256(src[proofstart:end].encode()).hexdigest()})
    for start,end,repl in sorted(edits,reverse=True): src=src[:start]+repl+src[end:]
    write(p/'public/repo'/f,src); dump(p/'private/targets.json',records)
    dump(p/'public/targets.json',[{k:r[k] for k in ['name','weight','file','signature']} for r in records])
    copy(REPOS/'brownian-motion/blueprint/src/chapters/kolmogorov_chentsov.tex',p/'public/mathematical_background.tex')
    write(p/'public/instruction.md','''# 构造 Hölder 连续修正

在固定版本的 Lean 项目中补全 targets.json 指定的 16 个证明。工作从稠密子集上的一致连续延拓开始，经过可测 Hölder 事件、几乎处处估计和依概率收敛，最终建立随机过程的 Hölder 连续修正。

公开工作区保留全部定理签名、定义和周边支持库；所选证明体为 sorry。可在同一个文件内补充辅助 lemma，但不得改变既有签名、定义、import 或依赖版本，也不得提交新 axiom、unsafe 绕过、外部 oracle 或修改 kernel。只提交这一 Lean 源文件。

评分以 16 个目标各占 1/16 的方式累计。某目标只有在内核接受且传递依赖不包含 sorryAx 或额外公理时才得分：用尚未证明的上游目标推出后续目标不能得分。其余目标的 sorry 可以暂留以支持增量改进；应逐目标检查公理闭包，而非要求第一次提交就全项目无 sorry。参考 mathlib/Lean 版本以 lake-manifest.json、lean-toolchain 为准。
''')
    write(p/'SOURCE_TO_TASK.md','''# 素材 → 题目

来源为 Apache-2.0 的 brownian-motion 项目固定提交，选取 Kolmogorov–Chentsov 连续修正证明链。保留的数学背景来自对应 blueprint。私有完整原文件提供可追溯证明依据，16 个精确签名/权重与证明摘要已记录。

借鉴 DeepSWE 的依赖单元消融和 NL2Repo 的接口冻结；这里的接口是定理类型，不能随机删几行 tactic。目标横跨拓扑、ENNReal 估计、可测性、几乎处处论证及过程修正。训练新颖性来自独立素材和新的证明任务切分，不能声称这些定理从未公开。未执行 Lean 或下载 mathlib；后续需固定离线依赖、检查原文件的依赖闭包，并进行逐目标公理审计和难度校准。
''')
    return p

FORWARD = '''"""Original task generator: finite-duration rectangular source in infinite 3-D ADE.
No MODFLOW binary is invoked. Units: m, day, g/m^3. Public numerical forward model.
"""
from math import erf, sqrt, exp
def concentration(p, x, y, z, t, steps=128):
    end=min(t,p['t_start']+p['duration'])
    if end<=p['t_start']: return 0.0
    dt=(end-p['t_start'])/steps
    total=0.0
    for i in range(steps):
        tau=t-(p['t_start']+(i+.5)*dt)
        factors=[]
        for q,c,h,D,v in [(x,p['cx'],p['hx'],p['Dx'],p['vx']),
                           (y,p['cy'],p['hy'],p['Dy'],0.0),
                           (z,p['cz'],p['hz'],p['Dz'],0.0)]:
            s=sqrt(4*D*tau); q=q-v*tau
            factors.append(.5*(erf((q-c+h)/s)-erf((q-c-h)/s)))
        total+=factors[0]*factors[1]*factors[2]*exp(-p['decay']*tau)
    return p['rate']*dt*total/(8*p['hx']*p['hy']*p['hz'])
'''

def science(out):
    fs=['scripts/ex-gwt-moc3d-p02.py','doc/sections/ex-gwt-moc3d-p02.tex']
    p=base(out,'finite_release_groundwater_inverse','Scientific Problems & ML',
        '稀疏观测下的三维有限时源反演','borden_source_inversion',[source('modflow6-examples',fs)],
        'documented 3-D transport mechanism -> independent finite rectangular-source model -> fixed synthetic observations and held-out query sets',
        'Uses an independently authored infinite-domain ADE solver, not the original Borden forward model or a MODFLOW run. Same physics family, uncalibrated difficulty.',
        ['submission/parameters.json'], '1/(1+mean((log1p(pred/scale)-log1p(truth/scale))**2))',
        {'scale':.01,'quadrature_steps':128,'feedback_denominator':96,'final_denominator':180},
        ['parameter_schema','finite_values','parameter_bounds','well_generalization','future_generalization'])
    for f in fs: copy(REPOS/'modflow6-examples'/f,p/'private/source_reference'/f)
    write(p/'public/forward.py',FORWARD)
    bounds={'cx':[0,12],'cy':[-3,3],'cz':[-1.5,1.5],'hx':[.3,3],'hy':[.2,2],'hz':[.1,1],
            'Dx':[.04,.3],'Dy':[.005,.08],'Dz':[.001,.025],'vx':[.06,.2],
            't_start':[0,35],'duration':[20,100],'rate':[.3,4],'decay':[0,.01]}
    truth={'cx':6.4,'cy':.7,'cz':-.3,'hx':1.8,'hy':.9,'hz':.4,'Dx':.13,'Dy':.024,'Dz':.007,
           'vx':.12,'t_start':14.,'duration':63.,'rate':1.7,'decay':.0023}
    dump(p/'public/parameter_bounds.json',bounds); dump(p/'private/ground_truth.json',truth)
    scope={}; exec(FORWARD,scope); fn=scope['concentration']; rng=random.Random(2026101401)
    splits={}; well_specs={}
    for split,nw,nt in [('public',12,9),('feedback',12,8),('final',18,10)]:
        rows=[]; wells=[]
        for j in range(nw):
            x=rng.uniform(12,55); y=rng.uniform(-4,4); z=rng.uniform(-2,2)
            wells.append({'well_id':f'{split}_{j:02}','x':x,'y':y,'z':z})
            for k in range(nt):
                t=45+k*(35 if split!='final' else 45)+rng.uniform(-4,4)
                clean=fn(truth,x,y,z,t)
                value=max(0,clean*math.exp(rng.gauss(0,.06))) if split=='public' else clean
                rows.append([f'{split}_{j:02}_{k:02}',x,y,z,t,value])
        d=p/('public' if split=='public' else 'private')
        buf=io.StringIO(); w=csv.writer(buf); w.writerow(['id','x','y','z','time_days','concentration_g_m3']); w.writerows(rows)
        write(d/f'{split}_observations.csv',buf.getvalue()); splits[split]=len(rows); well_specs[split]=wells
    dump(p/'private/data_generation.json',{'seed':2026101401,'synthetic':True,'observed_field_data':False,
         'model':'public/forward.py','noise':'public multiplicative exp(N(0,0.06)); private noiseless model targets',
         'counts':splits,'well_specs':well_specs})
    dump(p/'public/submission/parameters.json',{k:(v[0]+v[1])/2 for k,v in bounds.items()})
    write(p/'public/instruction.md','''# 三维有限时污染源反演

一个空间上均匀的长方体源在未知时间开始、持续有限天数后停止排放。溶质随后按三维各向异性平流–扩散–一阶衰减模型传播。使用 12 口井的 108 条带噪观测，估计源的中心、三个半宽、三个扩散系数、流速、起始时间、持续时间、总排放率和衰减率，共 14 个参数。

public_observations.csv 是本任务生成的合成观测，不是真实采样记录。forward.py 定义完整前向模型；无限域、x 方向匀速、常系数，源质量率为 rate g/day，空间源密度为 rate/(8*hx*hy*hz)。积分使用 128 点中点规则。观测乘以 exp(N(0,0.06)) 噪声。参数范围以 parameter_bounds.json 为准，前向模型与测量机制全部公开。

请提交 submission/parameters.json，键名严格对应参数范围。你可以实现多起点反演、灵敏度分析、正则化和全局/局部优化。评分根据参数在新井点和未来时间的浓度预测，使用公开的有界误差公式；不直接奖励参数与隐藏真值逐项相等。反馈与最终集使用不同井位，返回分组误差而非目标浓度。难点是有限释放与源几何、扩散、衰减之间的耦合及稀疏观测下的外推。
''')
    write(p/'SOURCE_TO_TASK.md','''# 素材 → 题目

出题依据来自 MODFLOW 6 Examples 的 MOC3D problem 2：三维稳态流场下的溶质输运、Wexler 解析参照和物理参数。原始 Python/LaTeX 文件仅保留在 private/source_reference，许可证/使用声明尚需核对，不将其作为已清权的训练数据重新分发。

任务代码与观测是本项目独立编写：点源示例启发了三维输运问题，但题目改为有限体积、有限持续时间、带衰减的未知源反演。并未复制 Borden 的 wells、隐藏参数或原 grader。forward.py 是自主定义的新物理模型，不能称为实际 MODFLOW 数值结果，也不能称为与 Borden 完全同分布。

已落盘：108 条公开带噪观测、96 条反馈目标、180 条最终目标、真实生成参数、井位与噪声种子、14 参数范围。生成这些数据属于出题；未调用求解器做题、未测 oracle/nop 或难度。后续重点审查可辨识性、低浓度退化解、积分精度和跨井外推难度；这些不能靠加大数据量替代。
''')
    return p

def optimization(out):
    family={'public':['chair','stool_x10','stepladder'], 'feedback':['adirondack_chair','deer','table'],
            'final':['sofa_structure','knight_armor','knight_body']}
    fs=['src/irregular/local_search.cpp','src/irregular/optimize.cpp']
    fs += [f'data/irregular/opencutlist/{n}.json' for names in family.values() for n in names]
    p=base(out,'industrial_irregular_strip','Combinatorial Optimization',
        '真实切割零件的异形排样求解器优化','jagua_nesting_optimization',[source('packingsolver',fs)],
        'preserve real industrial contours; convert native finite sheets to native OpenDimensionX; engineer solver under fixed per-case budget',
        'C++ PackingSolver replaces Rust jagua-rs. Data-family overlap with the original benchmark not yet exhaustively checked. Some upstream shape families may share motifs.',
        ['repo/src/irregular','repo/include/packingsolver/irregular'],
        'mean(feasible[i]*min(1, total_item_area[i]/(strip_height[i]*used_length[i])))',
        {'case_seconds':120,'case_cpu_threads':1,'geometry_tolerance':1e-7,'seed':4187,'final_denominator':3},
        ['all_items_present','allowed_rotation','no_overlap','inside_strip','budget','utilization'])
    repo_snapshot('packingsolver',p/'public/repo',exclude=('data','test','tests','images','docs','scripts','web'))
    selected=[]
    for split,names in family.items():
        for name in names:
            f=REPOS/f'packingsolver/data/irregular/opencutlist/{name}.json'; d=json.loads(f.read_text())
            height=d['bin_types'][0]['height']; width=0; area=0
            for item in d['item_types']:
                shapes=item.get('shapes',[item])
                vertices=[v for s in shapes for v in s['vertices']]
                itemwidth=max(v['x'] for v in vertices)-min(v['x'] for v in vertices)
                width+=(itemwidth+1)*item.get('copies',1)
                def poly(v): return abs(sum(a['x']*b['y']-b['x']*a['y'] for a,b in zip(v,v[1:]+v[:1])))/2
                ia=0
                for s in shapes:
                    ia+=poly(s['vertices'])
                    for h in s.get('holes',[]): ia-=poly(h['vertices'] if isinstance(h,dict) else h)
                area+=ia*item.get('copies',1)
            original_objective=d['objective']; d['objective']='open-dimension-x'
            d['bin_types']=[{'type':'rectangle','copies':1,'width':width,'height':height}]
            dest=p/('public/cases' if split=='public' else f'private/{split}_cases')/(name+'.json'); dump(dest,d)
            copy(f,p/'private/original_shapes'/(name+'.json'))
            selected.append({'id':name,'split':split,'items':sum(i.get('copies',1) for i in d['item_types']),
              'strip_height':height,'maximum_length':width,'area_lower_bound_length':area/height,
              'total_item_area':area,'original_objective':original_objective,'source_sha256':sha(f),
              'transformed_sha256':sha(dest),'shape_geometry_unchanged':True})
    dump(p/'private/case_manifest.json',selected)
    write(p/'public/instruction.md','''# 改进工业异形零件的条带排样

在给定 PackingSolver 固定版本上改进 irregular 求解器。目标为 open-dimension-x：必须摆放全部零件，在固定条带高度内最小化占用长度。公开三组家具/梯具零件来自真实切割设计，含非凸轮廓与孔洞。保留各 item 的 copies、allowed_rotations 和形状，不允许替换为外接矩形来判断可行性。

可修改 src/irregular 与 include/packingsolver/irregular 下的算法，但必须保持原 CLI、输入格式和 certificate 输出格式；提交这些目录的源码快照。可改初始布局、候选位置、邻域、重启、旋转选择与几何加速。每例单线程 120 秒、固定种子；评分器使用独立冻结的几何可行性检查，不能接受你报告的面积或相交结论。

一个例子的分数是总零件面积/(条带高度*使用长度)，无效排样该例为零。未输出的例子仍占总分分母。公开、反馈、最终按来源设计族分开，不把同一个设计的旋转版或重复版跨集合使用。私有组包含更密集、更不规则的设计；固定预算下必须同时处理可行性和利用率。所有实际常量见 evaluation_contract.draft.json。
''')
    write(p/'SOURCE_TO_TASK.md','''# 素材 → 题目

来源：MIT 的 PackingSolver 求解器以及仓库内 OpenCutList 工业零件轮廓。原 JSON 均已存档，逐例原文件与变换后 SHA 见 private/case_manifest.json。数据的独立授权仍需核对，代码 MIT 不自动替代零件数据权利说明。

只转换容器目标：bin-packing-with-leftovers 改为原引擎支持的 open-dimension-x，固定原高度、一个足够长的矩形条带。保持真实非凸多边形、孔洞、旋转限制、件数。共 9 例按来源设计族分为 3/3/3；knight_body 和 knight_armor 同放最终集，不使用 deer_2、sofa_structure_r180 等明显同源变体跨集。

任务产物是“优化通用求解器”，不是为九份输入逐一提交坐标。借用 ProgramBench 的固定源码与 CLI 契约、DeepSWE 的真实项目工作单元；没有执行它们的构建或 QC。参考实现为完整下载的原始求解器，其性能不是已测基线。尚未运行 CMake、geometry verifier 或排样算法；外部 CMake 依赖需后续补齐以实现离线运行。
''')
    return p

def professional(out):
    zpath=ROOT/'materials/downloads/49_Industry_Portfolios_daily_CSV.zip'
    url='https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_daily_CSV.zip'
    p=base(out,'industry_portfolio_risk_lab','Professional Knowledge Work',
        '跨市场阶段的行业组合风险校准','portfolio_risk_calibration',
        [{'url':url,'sha256':sha(zpath),'acquired':True,'license_status':'not established; local research prototype only'}],
        'real financial panel -> frozen vintage -> chronological split -> rolling risk forecasts for new portfolio mandates',
        'Original task instruction is image-contained and not extracted; anchor similarity based on task metadata only. Data is public and may be memorized.',
        ['submission/risk_model.py','submission/report.md'],
        '1/(1+0.7*mean_QLIKE_divergence+0.3*mean_scaled_pinball)',
        {'variance_floor':1e-8,'pinball_scale':.01,'variance_weight':.7,'quantile_weight':.3,'quantiles':[.01,.05],
         'realized_window_days':21,'forecast_stride_days':21,'warmup_days':756},
        ['history_only','output_schema','finite_forecasts','positive_variance','ordered_quantiles','variance_loss','tail_loss'])
    with zipfile.ZipFile(zpath) as z: raw=z.read(z.namelist()[0]).decode('utf-8-sig')
    lines=raw.splitlines(); header=next(i for i,x in enumerate(lines) if x.startswith(',Agric'))
    names=next(csv.reader([lines[header]]))[1:]; rows=[]
    for row in csv.reader(lines[header+1:]):
        if not row or not re.fullmatch(r'\d{8}',row[0].strip()): break
        date=row[0].strip(); values=[float(x) for x in row[1:]]
        if '19900101'<=date<='20251231': rows.append([date]+['' if x in (-99.99,-999) else f'{x/100:.6f}' for x in values])
    splits={'public': [r for r in rows if r[0]<'20160101'],
            'feedback':[r for r in rows if '20160101'<=r[0]<'20200101'],
            'final':[r for r in rows if r[0]>='20200101']}
    for split,rr in splits.items():
        b=io.StringIO(); w=csv.writer(b);w.writerow(['date']+names);w.writerows(rr)
        write(p/('public' if split=='public' else 'private')/(split+'_returns.csv'),b.getvalue())
    write(p/'private/source_header.txt','\n'.join(lines[:header+1])); copy(zpath,p/'private/raw_source.zip')
    rng=random.Random(2026101402); mandates=[]
    for i in range(8):
        weights=[rng.expovariate(1) if (j+i)%3 else 0 for j in range(49)]; total=sum(weights)
        mandates.append({'id':f'mandate_{i}','weights':{n:x/total for n,x in zip(names,weights)}})
    dump(p/'public/mandates.json',mandates)
    dump(p/'private/split_manifest.json',{'source_vintage':lines[0],'units':'decimal simple returns',
      'missing_sentinels':[-99.99,-999],'missing_policy':'discard date only if any nonzero mandate asset missing; report all discarded dates; never zero-impute',
      'splits':{k:{'rows':len(v),'first':v[0][0],'last':v[-1][0]} for k,v in splits.items()},
      'evaluation':'roll 21-trading-day nonoverlapping windows wholly inside each split; all data earlier than origin may be history, no future rows',
      'history_rule':'verifier supplies at least 756 preceding trading days; model may use all supplied history'})
    write(p/'public/submission/risk_model.py','''"""JSONL stdin: {history: [[r1,...,r49],...], weights: [w1,...,w49]}.
One JSON object per line to stdout: variance_daily, q01_daily, q05_daily.
Naive reference starter; improve the risk methodology. Missing rows prefiltered.
"""
import json,sys,math
def predict(req):
    values=[sum(x*w for x,w in zip(r,req['weights'])) for r in req['history'][-252:]]
    mean=sum(values)/len(values)
    variance=max(1e-8,sum((x-mean)**2 for x in values)/len(values))
    return dict(variance_daily=variance,q01_daily=mean-2.326347874*math.sqrt(variance),q05_daily=mean-1.644853627*math.sqrt(variance))
if __name__=='__main__':
    for line in sys.stdin: print(json.dumps(predict(json.loads(line))))
''')
    copy(p/'public/submission/risk_model.py',p/'private/reference/naive_gaussian.py')
    write(p/'public/submission/report.md','# 方法报告\n\n请记录风险假设、时间切分、缺失值处理、超参数选择和失效情景。\n')
    write(p/'public/instruction.md','''# 行业投资组合风险模型校准

你是风险分析团队的研究工程师。49 个行业的日收益面板、八个不同集中度的固定投资组合已提供。设计可复现的风险预测方法，使波动率和下尾分位数在市场状态变化后仍能校准。此任务评价统计预测，不要求投资建议或买卖操作。

public_returns.csv 为 1990–2015 年公开历史，已从源数据百分数换成小数简单收益。空值是缺失，不能当作零。每个预测时点只能使用之前的历史；输入行按 49 行业固定顺序排列，权重由 mandates.json 指定。程序逐行读取 JSONL 请求，输出日收益方差、1% 和 5% 下尾分位数，具体格式见 submission/risk_model.py。

预测在随后 21 个交易日评价。方差目标 v 为该窗口每日组合收益平方的均值（零均值近似的二阶矩）；QLIKE 散度为 v/h-log(v/h)-1，v 和 h 均以 1e-8 截断。对每个日收益 y，分位损失为 (alpha-I[y<q])*(y-q)，两种 alpha 等权平均，再除以 0.01。最后按 evaluation_contract.draft.json 汇总。方差和分位数必须有限、方差正、q01<=q05。每次进程只见当次历史，状态不跨预测保留；可提交确定性的离线统计方法，不能包含未来日期到答案的查表。

反馈时期是 2016–2019，最终时期为 2020–2025，按 21 交易日不重叠窗口滚动；窗口不能跨分割边界，前序已发生的收益可作为后续预测历史。所有组合、所有完整窗口都占固定分母。无评分的人类主观报告项：report.md 用于方法追踪，分数只由固定统计指标计算。可以从 EWMA、稳健协方差、收缩、尾部模型和状态切换入手。提交整个 risk_model.py 与报告，不能提交预先预测的未来表。
''')
    write(p/'SOURCE_TO_TASK.md','''# 素材 → 题目

已实际下载 Kenneth French 官方 49 Industry Portfolios Daily CSV 压缩包，原始包及 SHA 保留。提取第一段 value-weighted 日收益，固定 202608 CRSP vintage，截取 1990–2025；单位转换与缺失哨兵处理显式记录，不将 equal-weighted 段误拼接进来。

新的工作单元：八份固定组合委托、长历史与两段时间外推、滚动预测接口、方差与下尾联合损失及研究报告。真实收益数据不是本项目合成的；组合委托为固定种子生成。参考 starter 是朴素高斯模型，不是声称最优的 oracle。原 EdgeBench 专业任务的完整镜像题面尚未提取，因此目前只能支持类别/机制相近的设计判断。

下载可用不等于训练再分发授权已确认：此小样仅用于本地构造可行性审阅，进入可分发训练集前须核对 French/底层 CRSP 条款，必要时换成明确授权的源。这里解决了获取和任务化，尚未解决商业分发权利。未运行模型或回测。
''')
    return p

def games(out):
    fs=['src/ai/abstraction/WorkerRush.java','src/rts/GameState.java','maps/16x16/basesWorkers16x16.xml']
    p=base(out,'microrts_resource_frontier','Interactive Games & Simulators',
        '资源竞争与瓶颈地形中的长期策略机器人','wesnoth_tactical_ai',[source('microrts',fs)],
        'fixed real simulator and API -> original symmetric maps -> bot engineering with opponent portfolio and paired seats',
        'microRTS is a different engine from Wesnoth; bot-development mechanism is shared but exact gameplay distribution is not.',
        ['submission/FrontierAI.java'], 'mean(win + 0.5*draw)',
        {'match_cycles':6000,'action_time_ms':100,'paired_seats':True,'seeds':[11,29,47,83],
         'opponents':['WorkerRush','LightRush','RangedRush','HeavyRush'],'final_matches':96},
        ['source_scope','api_compatibility','legal_actions','time_budget','match_result'])
    repo_snapshot('microrts',p/'public/engine',exclude=('maps','test','data'))
    maps=[]
    for si,split in enumerate(['public','feedback','final']):
        for k in range(3):
            n=24+8*k; wall=n//2; terrain=['0']*(n*n)
            # Paired vertical barriers and symmetric gates keep both seats equivalent.
            gates={n//4,n//4+1,n-1-n//4,n-2-n//4}
            for x in [wall-1,wall]:
                for y in range(n):
                    if y not in gates: terrain[y*n+x]='1'
            units=[]
            def u(t,owner,x,y,res=0,hp=1):
                units.append(f'<rts.units.Unit type="{t}" ID="{len(units)}" player="{owner}" x="{x}" y="{y}" resources="{res}" hitpoints="{hp}"/>')
            for owner in [0,1]:
                transform=lambda x,y: (x,y) if owner==0 else (n-1-x,n-1-y)
                for typ,x,y,res,hp in [('Base',3,3,0,10),('Worker',2,3,0,1),('Worker',3,2,0,1),
                    ('Resource',1,1,20+10*si,1),('Resource',1,2,20+10*si,1),
                    ('Resource',wall-3,n//4,70-10*si,1)]:
                    x,y=transform(x,y);u(typ,-1 if typ=='Resource' else owner,x,y,res,hp)
            name=f'frontier_{split}_{n}.xml'
            xml=f'<rts.PhysicalGameState width="{n}" height="{n}"><terrain>'+''.join(terrain)+'</terrain><players><rts.Player ID="0" resources="5"/><rts.Player ID="1" resources="5"/></players><units>'+''.join(units)+'</units></rts.PhysicalGameState>\n'
            write(p/('public/maps' if split=='public' else f'private/{split}_maps')/name,xml)
            maps.append({'id':name,'split':split,'size':n,'new_map':True,'original_map_copied':False,
              'design':'paired chokepoints, scarce home resources, contested expansion resources; 180-degree symmetry'})
    dump(p/'private/map_manifest.json',maps)
    starter='''package submission;
import ai.abstraction.WorkerRush;
import ai.core.AI;
import rts.units.UnitTypeTable;
/** Starter delegates to a fixed rush; replace with a stateful strategy. */
public class FrontierAI extends WorkerRush {
    private final UnitTypeTable table;
    public FrontierAI(UnitTypeTable utt) { super(utt); table=utt; }
    @Override public AI clone() { return new FrontierAI(table); }
}
'''
    write(p/'public/submission/FrontierAI.java',starter)
    write(p/'public/instruction.md','''# 资源边境策略机器人

基于固定 microRTS 引擎实现 submission.FrontierAI。公开地图包含成对瓶颈通道、有限的基地资源与需要争夺的扩张资源。目标是在多种对手和尺度下维持经济、安排兵种、选择进攻时机并打赢完整对局。

继承 AI/AbstractionLayerAI 或保留 WorkerRush 作为基础均可；构造器接受 UnitTypeTable，clone/reset/getAction 行为遵守原 API。提交仅含一个 FrontierAI.java，可使用内部类。评分器在冻结引擎中编译并创建全新实例，不接受修改引擎、地图、对手、随机种子或 match runner；禁止反射、进程/网络/文件访问和改写 GameState。通过合法 PlayerAction 行动。

每局最多 6000 cycles，每次 getAction 最多 100ms；面对 WorkerRush、LightRush、RangedRush、HeavyRush 四种固定对手，每张地图用四个种子和两个座位配对。每组 3 张图，共 96 局；胜 1、平 0.5、负 0，全部比赛等权。违规或超时局按负计并返回具名诊断，基础接口无法运行则本次提交无效。公开/反馈/最终地图在家庭资源与扩张压力上不同，最终表现要求完整策略泛化。

提交源文件快照后，由独立 verifier 重新模拟整个对局；得分不依赖 agent 容器中的活进程或正在进行的游戏。参考模型的运行时间是 3 小时，局内模拟只是单次评分工作负载，二者不要混淆。
''')
    write(p/'SOURCE_TO_TASK.md','''# 素材 → 题目

已下载 microRTS 固定提交的 Java 引擎、AI 接口、策略样例和库文件，GPL-3.0 许可证随源码保留。原地图仅用于理解 XML 格式，九张 frontier 地图由本项目构造，包含 24/32/40 三种尺度；没有复制 Wesnoth 或原 benchmark 地图。

对手源码和原有策略 API 是出题依据。公开 starter 为可编辑 WorkerRush 派生类，求解者需要发展经济、路径、战术和策略。借用 ProgramBench 的固定引擎/接口与 NL2Repo 的受控提交边界。当前地图是三个同设计族压力配置，能作为首个机制小样，尚不能证明原 benchmark 级别的战略多样性。

未运行游戏、编译 Java 或模拟比赛。后续必须审查资源是否可达、两座位公平性、对局时长和局内确定性；Java API 禁止事项需要进程边界/隔离通信实现，文字限制不等于安全隔离。预留的 96 局成本与机器资源要在校准时测量。
''')
    return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    paths=[]
    for builder in [system,formal,science,optimization,professional,games]:
        p=builder(out);paths.append(p);print('constructed',p.name,flush=True)
    summary=[]
    for p in paths:
        records=[{'path':str(f.relative_to(p)),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(p.rglob('*')) if f.is_file()]
        dump(p/'file_manifest.json',records)
        d=json.loads((p/'construction.json').read_text())
        summary.append({'task_id':p.name,'title':d['title'],'category':d['category'],'files':len(records),
                        'status':d['status'],'runtime_verified':False,'accepted':False})
    dump(out/'index.json',summary)
    dump(out/'recipe.json',{'script':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__)),
          'constructors':6,'external_model_runs':0,'runtime_validation_runs':0,'status':'constructed_unverified'})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
