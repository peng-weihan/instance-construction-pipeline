"""Assemble complete source-level task packages. Never builds/runs their environments.

Six task-specific implementations are maintained as ordinary files in components/.
This command copies sources, applies author patches and writes isolated build contexts.
"""
import argparse,ast,hashlib,json,re,shutil,subprocess,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];HERE=Path(__file__).resolve().parent
BASE=ROOT/'samples/long-horizon-candidates-001';PARTS=HERE/'components'
TASKS={
 'restler_resilient_execution':'software','layered_aquifer_source_lab':'science',
 'industrial_nesting_improvement':'packing','brownian_multibranch_proofs':'formal',
 'cross_asset_adaptive_allocator':'finance','wesnoth_frontier_campaign_ai':'game'}
SUBMIT={'software':'repo/restler','science':'submission','packing':'repo','formal':'repo','finance':'submission','game':'submission'}

def write(p,text):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def dump(p,data):write(p,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):
    b.parent.mkdir(parents=True,exist_ok=True)
    if a.is_dir():shutil.copytree(a,b,ignore=shutil.ignore_patterns('__pycache__','.git'))
    else:shutil.copy2(a,b)

def software(p):
    ref=p/'solution/reference';src=p/'public/repo/restler'
    files={'execution_policy.py':'engine/core/execution_policy.py','resilient_workflow.py':'engine/core/resilient_workflow.py','replay_execution.py':'engine/tools/replay_execution.py'}
    for f,dst in files.items():cp(PARTS/'software'/f,ref/dst)
    write(ref/'engine/tools/__init__.py','')
    for f,needle,hook in [
      ('engine/core/request_utilities.py','def send_request_data(rendered_data, req_timeout_sec=None, reconnect=None, http_sock=None):\n',
       '    if getattr(Settings(), "execution_policy", None) is not None:\n        from engine.core.execution_policy import send_from_restler\n        return send_from_restler(rendered_data, req_timeout_sec, reconnect, http_sock)\n'),
      ('engine/core/async_request_utilities.py','def try_async_poll(request_data, response, max_async_wait_time, poll_delete_status=False):\n',
       '    if getattr(Settings(), "execution_policy", None) is not None:\n        from engine.core.execution_policy import poll_from_restler\n        return poll_from_restler(request_data, response, max_async_wait_time, poll_delete_status)\n')]:
        s=(src/f).read_text();assert s.count(needle)==1;write(ref/f,s.replace(needle,needle+hook))
    f='restler_settings.py';s=(src/f).read_text();needle='        def convert_wildcards_to_regex(str_value):'
    assert s.count(needle)==1
    hook='        self.execution_policy = None\n        if "execution_policy" in user_args:\n            from engine.core.execution_policy import validate_policy\n            self.execution_policy = validate_policy(user_args["execution_policy"])\n\n'
    write(ref/f,s.replace(needle,hook+needle))
    cp(PARTS/'software/probe.py',p/'public/probe.py')
    generation=runpy.run_path(str(PARTS/'software/cases.py'));feedback=generation['cases']();audit=generation['audit_cases']()
    practice=[]
    for group in ['policy','retry','idempotency','async','leases','trace','replay']:
        practice.append(next(x for x in feedback if x['group']==group))
    dump(p/'private/behavior_cases.json',{'public':practice,'feedback':feedback,'audit':audit})
    dump(p/'public/practice_cases.json',practice)
    write(p/'solution/solve.py','''import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--public',required=True);p.add_argument('--output',required=True);a=p.parse_args()
out=Path(a.output);shutil.copytree(Path(a.public)/'repo/restler',out,dirs_exist_ok=True)
shutil.copytree(Path(__file__).parent/'reference',out,dirs_exist_ok=True)
''')
    write(p/'public/instruction.md',SOFTWARE_INSTRUCTION)
    return ['grader.py','probe.py']

SOFTWARE_INSTRUCTION='''# RESTler 可恢复执行与资源生命周期

在完整 RESTler 引擎中实现 roadmap.json 七组需求，目标预算 6 小时。旧功能保持可用；只有显式配置 execution_policy 时启用新行为。配置键、重试时间、截止边界和清理规则见 interface.md。不是只写一个不被真实引擎调用的 helper。

实现以下公开接口：
- engine.core.execution_policy：validate_policy(config)、resolve(config,method,path)、Context(policy,clock=None,rng=None,cancelled=None)、CURRENT ContextVar、LeaseGraph(resources)。
- Context 提供 policy、clock、rng、deadline、events、terminal；clock 有 monotonic()/wall()/sleep(seconds)。terminal 为 succeeded/failed/timed_out/cancelled。
- LeaseGraph：created(id,refs=1)、acquire(id)、release(id)、cleanup(delete,context)。delete(id,remaining_seconds) 返回布尔成功；cleanup 返回 (deleted_ids,retained_ids)。资源规格为 id、parents 列表。
- engine.core.resilient_workflow.execute_workflow(spec,context=None)：按依赖顺序用真实 request_utilities.send_request_data/try_async_poll 创建资源，登记 dependencies.set_variable_no_gc，失败时回收已创建资源，返回 completed/failed/deleted/retained/events。
- workflow 的每个资源有 id、parents、request、delete_request，可选 value 和 leases。一个 workflow 持有一个 lease；结束时释放自己的 lease，外部 lease 保留。
- engine.tools.replay_execution.replay(records,policy)，以及既定 CLI。每条 record 有 request、responses（raw/success/elapsed）、wall、seed；返回规范化事件列表。输入可以包含认证头，输出事件必须脱敏。

接入 RestlerSettings 的 execution_policy 配置与原有 send_request_data、try_async_poll 调用路径。每个发起请求生成上下文，并通过 response._execution_context 传给轮询；CURRENT 显式指定时复用它。创建请求、轮询与最终 GET 共享 deadline。取消后仍允许独立清理预算。示例探针见 probe.py；注入的 transport 是替代外部服务，真实引擎调用链仍须经过。

提交 /workspace/repo/restler 的目录快照，根目录直接包含 restler_settings.py 和 engine/。七组权重依次为 .10/.15/.15/.15/.20/.10/.15。每组按行为检查通过比例计分；评分器在外侧记录真实 transport 调用与等待，返回具名失败项。
'''

def science(p):
    cp(PARTS/'science/solve.py',p/'solution/solve.py');cp(PARTS/'science/forward.py',p/'solution/forward.py')
    physics=(p/'public/physics.md').read_text()
    physics+='''
Numerical observation convention: the grid origin is the lower cell-face corner, so centre i is origin+(i+0.5)*spacing. Layer bounds use z_min <= centre_z < z_max. Start from C=0 at t=0. The data-generating time discretization is explicit forward Euler at the fixed time_step_days; all transport/decay terms use the previous state. For step k=1,2,..., enable the source when t_start <= (k-0.5)*dt < t_start+duration, then record the updated state at k*dt. Observation days are integer multiples of dt. Do not round source start/end to grid points before this midpoint test. Source contribution is fractional overlap volume times rate/source_volume/porosity, divided by the cell-layer retardation R along with all other terms. There are no hidden fitted transport coefficients.
'''
    write(p/'public/physics.md',physics)
    s=(p/'public/instruction.md').read_text();s+='\n提交目录根必须含 answer.json；推断源码仅供审阅，评分不会执行它。JSON 键必须恰为 source_bounds.json 的十个键。公共套件对检测限记录使用区间违约误差；正式反馈/审计使用冻结无噪标签。评分公式及常量见 score_design.json。\n'
    write(p/'public/instruction.md',s)
    return ['grader.py','forward.py']

def packing(p):
    write(p/'solution/solve.py','''"""Reference restores the real frozen solver; its quality is not assumed optimal."""
import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--public',required=True);p.add_argument('--output',required=True);a=p.parse_args()
for rel in ['src/irregular','include/packingsolver/irregular']:
    shutil.copytree(Path(a.public)/'repo'/rel,Path(a.output)/rel,dirs_exist_ok=True)
''')
    write(p/'solution/README.md','''参考解是冻结上游真实求解器源码，执行时实际搜索并输出布局，不是空操作文件。它与比较基线同源，因此预计只能提供可行性端点，不能冒称高分 oracle；具体分值未测。更强参考实现和六小时曲线属于后续难度校准，不影响本包提交/计分链的源代码完整性。\n''')
    s=(p/'public/instruction.md').read_text().replace('单线程 20 秒，固定种子','固定单核亲和性下 20 秒（线程共享同一核）');s+='\n提交目录根含 src/irregular 与 include/packingsolver/irregular。其余构建文件由评分器恢复，新增 CMake 规则不接受。基线长度在 verifier 镜像构建时使用冻结源码每例运行 20 秒，独立检查后写入 reference_lengths.json；每次提交不会重新估计基线。seed 参数在当前上游 CLI 标为 not used，不能作为确定性保证；最终固定的是保存的参考布局。独立检查器支持本批全部 polygon/holes 输入，几何容差见 scoring_metadata.json。\n'
    s+='\n求解器统一附带 --item-item-minimum-spacing 0.1；参考布局和提交使用相同间距，严格几何验证容差保持不变。\n'
    write(p/'public/instruction.md',s)
    return ['grader.py','geometry.py','build.py','prepare_reference.py']

def formal(p):
    cp(HERE/'formal_source_audit.json',p/'private/formal_source_audit.json')
    targets=json.loads((p/'public/targets.json').read_text());ref=p/'solution/reference'
    for f in sorted({x['file'] for x in targets}):
        masked=(p/'public/repo'/f).read_text();original=(p/'private/reference'/f).read_text()
        local=[x for x in targets if x['file']==f]
        for t in local:
            sig=t['signature'];marker1='/- BEGIN TASK PROOF '+t['name']+' -/';marker2='/- END TASK PROOF '+t['name']+' -/'
            needle=sig+' := by\n  sorry'
            # Preserve whitespace between the type and := exactly.
            m=re.search(re.escape(sig)+r'\s*:= by\n  sorry',masked);assert m,t['name']
            # Keep `by` on the declaration/field line. A column-zero `by`
            # breaks nested structure fields even when a top-level lemma works.
            final_line=sig.rsplit('\n',1)[-1]
            indent=' '*(len(final_line)-len(final_line.lstrip())+2)
            t['masked_body']=' by\n'+indent+'sorry\n'
            masked=masked[:m.start()]+sig+' := '+marker1+t['masked_body']+marker2+masked[m.end():]
            start=original.index(sig);sep=original.index(':=',start+len(sig));body_start=sep+2
            boundary=re.search(r'(?m)^(?:(?:lemma|theorem|def|end|section|namespace|noncomputable|variable|omit|open|include|nonrec|attribute)\b|@\[|/--|/-!)',original[body_start:])
            body_end=body_start+boundary.start() if boundary else len(original);body=original[body_start:body_end].strip()
            # Construct the reference using the same frozen template and marked body.
            t['reference_body']=body
            namespace=''
            if '/Gaussian/' in f:namespace='ProbabilityTheory.'
            elif 'KolmogorovChentsov' in f and t['name'] not in ['UniformContinuousOn.exists_tendsto','Dense.holderOnWith_extend']:namespace='ProbabilityTheory.'
            t['full_name']=namespace+t['name']
        reference=masked
        for t in local:
            reference=reference.replace('/- BEGIN TASK PROOF '+t['name']+' -/'+t['masked_body']+'/- END TASK PROOF '+t['name']+' -/',
                '/- BEGIN TASK PROOF '+t['name']+' -/ '+t['reference_body']+'\n/- END TASK PROOF '+t['name']+' -/')
        write(p/'public/repo'/f,masked);write(ref/f,reference)
    for t in targets:
        del t['reference_body']
        del t['masked_body']
    dump(p/'public/targets.json',targets)
    write(p/'solution/solve.py','''import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
shutil.copytree(Path(__file__).parent/'reference',a.output,dirs_exist_ok=True)
''')
    write(p/'public/instruction.md','''# 布朗运动多分支形式化证明

在固定 Lean/BrownianMotion 工程中补全 targets.json 的 31 个证明，目标预算 6 小时。五个文件覆盖协方差、覆盖数、高斯矩、过程性质和连续修正。允许从任一分支开始，未完成目标保留 sorry。

只修改 BEGIN TASK PROOF / END TASK PROOF 注释之间的证明体，允许在证明内使用 have/let 等辅助构造；其余文件内容、类型签名、定义、import、依赖版本严格冻结。提交目录根含 targets.json 中的五个相对路径，无需提交依赖库。

不能加入 axiom/unsafe/opaque、运行 IO 的命令、宏/elaborator、run_tac 或关闭检查的选项。评分器重新构建固定项目，按目标实际声明的传递公理闭包计分，只允许 propext、Classical.choice、Quot.sound；sorryAx 不得计分。编译失败会反馈错误摘要。

组权重：协方差 .20，覆盖数 .20，高斯矩与过程性质合计 .20，连续修正 .40；每组内按完整证明目标比例给分。参考原证明仅在作者 solution 中，不在 agent 镜像。
''')
    return ['grader.py']

def finance(p):
    cp(PARTS/'finance/reference_policy.py',p/'solution/policy.py')
    starter=(p/'public/submission/policy.py').read_text().replace('q05_daily and rebalance_reason.','q05_daily, rebalance (bool) and rebalance_reason.')
    write(p/'public/submission/policy.py',starter)
    write(p/'public/policy_interface.md','''# 策略协议

提交目录根为 policy.py，可带自己的 Python 模块和参数文件。评分器只调用 initialize(metadata) 与 decide(history,state)。

- initialize 每次评分调用一次，metadata 包含 assets 和 mandate；返回值成为首个 state.user_state。初始化异常属于无效提交。
- decide 每个评分交易日调用一次，必须返回一个 dict，包含 weights、risk_scale、variance_daily、q05_daily、rebalance、rebalance_reason。weights 的键必须恰为 assets；rebalance 必须是真正的 bool。
- 可选 user_state 字段会成为下一日的 state.user_state；省略时沿用上次状态。状态仅在同次评分中保留，不跨提交。策略不能修改可信账本状态。
- history.assets 给出 prices 每行的列顺序；dates 与 prices 等长。最多 253 行，最后一行是执行交易所用的前一收盘价。当天收益在决策之后才进入可信账本。
- state.day_index 从该评分区间的 0 开始，不是整个训练集的行号。其他字段为 weights、cash_weight、nav、last_rebalance_index、mandatory_rebalance、recent_forecasts、user_state。
- recent_forecasts 最多包含最近 20 个已完成时点的 date、return、variance_daily、q05_daily。不存在当前或未来收益。初始持仓为全现金；首次决策必须修复最低风险资产敞口要求。
- 无调仓时 weights 必须等于输入的漂移权重；风险缩放仍在范围内，预测仍必须有限。risk_scale 不会自动重新缩放权重。

约束、成本和风险目标以 mandate.json 为准，记账顺序见 accounting.md。评分公共区间使用 dev，训练数据只提供历史上下文；隐藏反馈和审计使用各自时间区间。stdout 会被适配器重定向到 stderr，不作为评分结果。
''')
    s=(p/'public/instruction.md').read_text().replace('基本接口、约束与记账测试提供部分分；主要分来自相对固定基线的净风险调整表现及风险校准。','完整回测满足接口与约束获得 0.25 基础分，额外最多 0.60 来自相对固定基线的净风险调整改进、0.15 来自尾部校准；任一非法决策使本次提交无效并记零。');s+='''
执行接口补充：policy.initialize(metadata) 返回 user_state；policy.decide(history,state) 可返回新的 user_state。必须返回 weights、risk_scale、variance_daily、q05_daily、rebalance（布尔）、rebalance_reason。history 为 assets、dates、prices，最多包含至前一收盘的 253 行；state 包含漂移权重、现金、NAV、上次调仓日、是否必须修复约束和过去预测结果。
正常调仓为每 20 日审查或距上次至少 5 日；如果漂移后违反权重约束，必须立即修复。无调仓时返回漂移权重。调仓后，基于公开历史最近最多 252 个日收益的总体协方差计算的年化风险不得超过 1.2*(0.10/risk_scale)。全部时点均满足接口与约束才能得到有效回测，任一不可解析/非法决策使本次提交无效并反馈原因。
评分使用完整开发、反馈或审计时段，独立账本逐日记账；训练区间不计分。基线是机器可读元数据中的固定配置及相同执行规则。提交目录根含 policy.py 和所需本地模块。单次决策 2 秒，上下文初始化 20 秒；整次策略调用还受总评分预算约束。
'''
    write(p/'public/instruction.md',s)
    return ['grader.py','ledger.py','policy_worker.py']

def game(p):
    cp(PARTS/'game/reference_policy.lua',p/'solution/policy.lua')
    write(p/'public/submission/policy.lua','return {decide=function(state) return nil end}\n')
    # Retire the earlier arbitrary WML entrypoint. The wrapper is immutable now.
    (p/'public/submission/my_custom_ai.cfg').unlink()
    base=(ROOT/'materials/repos/wesnoth-1.18.0/data/ai/ais/ai_default_rca.cfg').read_text()
    ca='''        [candidate_action]
            engine=lua
            id=edge_planner
            name=edge_planner
            location="~add-ons/EdgeCandidate/adapter.lua"
        [/candidate_action]
'''
    write(p/'verifier/custom_ai.cfg',base.replace('id=ai_default_rca\n','id=edge_custom_ai\n',1).replace('        {AI_CA_GOTO}',ca+'        {AI_CA_GOTO}',1))
    cp(PARTS/'game/adapter.lua',p/'public/adapter.lua')
    write(p/'public/policy_interface.md','''# 合法动作策略接口

policy.lua 返回 {decide=function(state) ... end}。actions、units、villages、terrain 都是从 1 开始的 Lua 数组；actions 每次重新枚举，index 不能跨调用缓存。

decide 返回 nil 时放弃本次候选动作，默认 AI 可接管；返回 {index=i,priority=p} 时与其他候选动作按优先级竞争，并不保证本次一定执行。策略不应把一次 evaluation 调用当作已经执行了一步。p 默认为 110000，须在 [1,250000] 内。

- move：unit_id、x、y、moves_left、chance_to_be_hit。后者是百分数，越小越安全；由 100-defense_on(terrain) 计算。moves_left 是 find_reach 路径查询的剩余移动力，实际执行使用 checked_move_full，会结束该单位的移动，不承诺保留此余量。
- attack：unit_id、目标移动位置 x/y、target_id、tx/ty、expected_own_hp、expected_enemy_hp、kill_probability。HP 是引擎单次战斗模拟的平均值；kill_probability 在 [0,1]。执行经 robust_move_and_attack，合法性仍由引擎确认。
- recruit：unit_type、x/y、cost。引擎仅枚举当前阵营可招募且位置合法的动作。

units 包含双方当前地图单位的普通字段；villages.owner=0 表示无人占领。time_of_day 包含 id、lawful_bonus。state 是数据副本，修改它不会更改游戏状态。完整字段及允许的 Lua 基础函数见 adapter.lua。模块内状态可跨回合保留，每局重新初始化。无法 require 其他模块、读取文件、调用引擎或控制 RNG。
''')
    c=json.loads((p/'public/match_contract.json').read_text());c['timeout_policy']='whole-game wall-time budget exceeded: forfeit, score zero; sandbox/engine result protocol failure: verifier_error'
    c['candidate_interface']='pure Lua planner selects immutable legal action IDs; trusted CA executes';c['faction_ids_checked_in_source']=True
    dump(p/'public/match_contract.json',c)
    write(p/'public/instruction.md','''# Wesnoth 多地形经济与战术策略

目标预算 6 小时，在 Wesnoth 1.18.0 上开发跨地图、阵营和座位的策略。三种新地形族为河道、森林和开阔经济区；公开三张地图，固定反馈使用另外三张地图，共 12 局。审计另有三张地图和三个种子，共 36 局。

提交目录仅需 policy.lua。它返回含 decide(state) 的 Lua table。state 包含 side、turn、gold、time_of_day、units、villages、terrain、actions；每个 action 都由真实引擎枚举，分为 move、attack（含移动后攻击）、recruit。移动动作含目标位置的受击概率，攻击动作含模拟战斗统计。返回 {index=动作序号, priority=1..250000}，或 nil 交给默认 CA。可以保留 Lua 模块内的策略状态进行多回合规划。实现细节和完整字段见公开 adapter.lua。

这是相对上一版的接口收紧：使用固定可信 Lua CA 包装器加载纯策略。policy 仅得到普通数据副本和基础数学/字符串/table 函数；不提供引擎对象、WML、文件、网络、系统调用或 RNG 控制。所有行动由包装器检查与执行。无需提交或修改 WML 配置，地图、包装器和默认对手不可修改。

招募、占村、移动与集火由你的动作选择影响。可以从选择性攻击或占村开始，再加入经济规划、阵营兵种配合、领袖保护、撤退及获胜速度优化。决定不覆盖默认 CA 时返回 nil。

分数为每局 0.8*win + 0.2*win*(45-turns_to_win)/44 的平均，回合数截到 [1,45]，平局/败局 0。单局总墙钟限 40 秒，超时弃权；引擎结果协议或沙箱启动失败作为 verifier_error。反馈包含每局是否完成、胜负和总胜率。完整运行取同一固定反馈集合上的历次最佳有效提交。
''')
    return ['grader.py','adapter.lua']

APT='python3 python3-venv python3-pip bubblewrap git curl ca-certificates build-essential cmake ninja-build pkg-config'
PIP='numpy==2.2.6 scipy==1.15.3 shapely==2.1.1 applicationinsights==0.11.10 requests==2.32.4 pytest==8.4.1 cmake==3.31.6'

def dockerfile(kind,judge,digest,game_commit):
    lines=[f'FROM ubuntu@{digest}', 'ENV DEBIAN_FRONTEND=noninteractive',
      f'RUN apt-get update && apt-get install -y --no-install-recommends {APT} && rm -rf /var/lib/apt/lists/*',
      'RUN python3 -m venv /opt/runtime/venv', 'ENV PATH="/opt/runtime/venv/bin:/opt/runtime/elan/bin:${PATH}"',
      f'RUN python -m pip install --no-cache-dir {PIP}', 'COPY public /opt/public',
      'COPY capture_build.py /opt/capture_build.py']
    if kind=='formal':
        lines += ['RUN apt-get update && apt-get install -y --no-install-recommends elan zstd && rm -rf /var/lib/apt/lists/*',
          'ENV ELAN_HOME=/opt/runtime/elan',
          'RUN elan toolchain install leanprover/lean4:v4.33.0-rc1 && elan default leanprover/lean4:v4.33.0-rc1',
          'RUN cp -a /opt/public/repo /opt/runtime/lean-project',
          'WORKDIR /opt/runtime/lean-project', 'RUN lake exe cache get && lake build BrownianMotion.Gaussian.BrownianMotion BrownianMotion.Continuity.CoveringNumber']
    elif kind=='packing':
        lines += ['RUN cp -a /opt/public/repo /opt/runtime/packing',
          'RUN cmake -S /opt/runtime/packing -B /opt/runtime/packing-build -DCMAKE_BUILD_TYPE=Release -DPACKINGSOLVER_BUILD_TEST=OFF -DPACKINGSOLVER_USE_CLP=OFF -DPACKINGSOLVER_USE_HIGHS=ON',
          'RUN cmake --build /opt/runtime/packing-build --target PackingSolver_irregular_main -j 2',
          'COPY lock_packing_dependencies.py /opt/lock_packing_dependencies.py',
          'RUN python /opt/lock_packing_dependencies.py']
    elif kind=='game':
        deps='libboost-all-dev libssl-dev libicu-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libcurl4-openssl-dev libvorbis-dev libfontconfig-dev libcairo2-dev libpango1.0-dev libreadline-dev gettext libdbus-1-dev'
        lines += [f'RUN apt-get update && apt-get install -y --no-install-recommends {deps} && rm -rf /var/lib/apt/lists/*',
          f'RUN git clone https://github.com/wesnoth/wesnoth.git /opt/runtime/wesnoth-source && git -C /opt/runtime/wesnoth-source checkout {game_commit} && git -C /opt/runtime/wesnoth-source submodule update --init --recursive',
          'RUN cmake -S /opt/runtime/wesnoth-source -B /opt/runtime/wesnoth-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/runtime/wesnoth -DENABLE_SERVER=OFF -DENABLE_CAMPAIGN_SERVER=OFF -DENABLE_TESTS=OFF -DENABLE_NLS=OFF -DENABLE_NOTIFICATIONS=OFF',
          'RUN cmake --build /opt/runtime/wesnoth-build -j 2 && cmake --install /opt/runtime/wesnoth-build']
    lines += ['RUN python /opt/capture_build.py']
    if judge:
        lines += ['COPY public /judge/public','COPY private /judge/private','COPY verifier /judge/verifier',
                  'WORKDIR /judge/verifier']
        if kind=='packing':lines += ['RUN python prepare_reference.py']
        lines += ['ENTRYPOINT ["/opt/runtime/venv/bin/python", "/judge/verifier/entry.py"]']
    else:
        lines += ['RUN mkdir /workspace && cp -a /opt/public/. /workspace/']
        if kind=='formal':lines += ['RUN cp -a /opt/runtime/lean-project/.lake /workspace/repo/.lake']
        lines += ['WORKDIR /workspace','CMD ["/bin/bash"]']
    return '\n'.join(lines)+'\n'

LOCK_PACKING='''import json
from pathlib import Path
root=Path('/opt/runtime/packing-build');mapping={}
for p in root.rglob('*-src'):
    if p.is_dir():mapping[p.name[:-4]]=str(p)
Path('/opt/runtime/packing-dependencies.json').write_text(json.dumps(mapping,indent=2)+'\\n')
'''

def metadata(p,kind):
    score=json.loads((p/'public/score_design.json').read_text())
    constants={
      'software':{'group_weights':{'policy':.1,'retry':.15,'idempotency':.15,'async':.15,'leases':.2,'trace':.1,'replay':.15},'rpc_limit':200,'reply_timeout_seconds':5},
      'science':{'relative_rmse_floor':1e-6,'log_scale':.0003,'relative_mse_weight':.5,'log_mse_weight':.5,'negative_prediction_tolerance':1e-12},
      'packing':{'solver_clearance':.1,'validity_weight':.2,'improvement_weight':.8,'per_case_seconds':20,'wall_seconds':25,'boundary_tolerance_factor':1e-7,'intersection_area_tolerance_factor':1e-9,'rotation_tolerance_degrees':1e-8,'epsilon_absolute':1e-9,'epsilon_reference_fraction':1e-6},
      'formal':{'group_weights':{'covariance':.2,'covering':.2,'moment_and_process':.2,'continuity':.4},'allowed_axioms':['propext','Classical.choice','Quot.sound']},
      'finance':{'functional_weight':.25,'utility_weight':.60,'calibration_weight':.15,'utility_scale':.10,'pinball_scale':.01,'quantile':.05,'annual_days':252,'volatility_penalty':.5,'drawdown_penalty':1.,'risk_budget_tolerance':1.2,'constraint_tolerance':1e-8,'hold_weight_tolerance':1e-7,'cost':.0005,'borrow':.03,'financing':.05,'baseline_weights':{'SPY':.10,'IWM':.05,'EFA':.10,'EEM':.05,'TLT':.40,'GLD':.05,'VNQ':.05,'DBC':.05}},
      'game':{'win_weight':.8,'efficiency_weight':.2,'turn_cap':45,'earliest_turn':1,'wall_seconds':40,'loss_draw_forfeit':0}}
    if kind=='finance':
        constants[kind].update(baseline_variance_floor=1e-10,baseline_tail_z=-1.645,initialize_seconds=20,
          decision_seconds=2,breach_rate_tolerance=.03,history_rows=253,forecast_history_rows=20,
          insufficient_history_variance=1e-4)
        score['formula']='valid*(0.25+0.60*clip((U-U_ref)/0.10,0,1)+0.15/(1+scaled_pinball))'
        score['validity']='Every decision must satisfy the published interface and constraints; any illegal decision invalidates the complete submission.'
    if kind=='packing':
        score['constants'].pop('seed',None);score['constants'].pop('threads',None);score['constants']['cpu_affinity_cores']=1
        score['reference_lengths_pending']=True;score['reference_materialization']='implemented, executes during explicit judge image build'
    if kind=='software':score['fixed_checks_pending']=False
    if kind=='science':score['reference_numerics_pending']=True
    # Both human design notes and executable graders share these same constants.
    constants[kind]={**score.get('constants',{}),**constants[kind]}
    score['constants']=constants[kind]
    dump(p/'public/score_design.json',score)
    dump(p/'public/scoring_metadata.json',{'direction':'higher_is_better','range':[0,1],'formula':score.get('formula',score.get('aggregation')),
        'constants':constants[kind],'endpoint_mechanism':'declared_algorithmic_reference_plus_theoretical_upper_bound',
        'baseline':{'implementation':'solution/ and verifier; see endpoint_notes.md','measured_score':None},
        'upper':{'value':1,'meaning':'formula bound, not a demonstrated attainable score'},'oracle_score':None,'nop_score':None,'model_three_run_mean':None})
    budgets={'software':900,'science':300,'packing':1800,'formal':1800,'finance':2400,'game':1800}
    write(p/'task.toml',f'''# LOCAL AUTHORING CONTRACT. Map to the contractor's Harbor schema when supplied.
schema = "edgebench.local-task.v2"
task_id = "{p.name}"
instruction = "instruction.md"
submission_root = "{SUBMIT[kind]}"

[agent]
timeout_seconds = 21600
network = "none"
build_context = "environment/agent"
dockerfile = "Dockerfile"

[verifier]
timeout_seconds = {budgets[kind]}
network = "none"
build_context = "environment/verifier"
dockerfile = "Dockerfile"
command = "python /judge/verifier/entry.py --submission /submission --suite feedback"
stateless = true
snapshot_only = true

[build]
network = "public"
open_internet_justification = "Acquire pinned upstream compiler, libraries and engine sources during image construction. Runtime is offline."
platforms = ["linux/amd64", "linux/arm64"]

[score]
kind = "local_bounded_continuous"
direction = "higher_is_better"
minimum = 0.0
maximum = 1.0
aggregation = "best_valid_submission_on_fixed_feedback_suite"
metadata = "public/scoring_metadata.json"
result_schema = "feedback_schema.json"

[resources]
cpus = 2
memory_mb = 12288
gpu = false

[evidence]
status = "constructed_unverified"
runtime_runs = 0
model_runs = 0
official_harbor_schema_mapped = false
''')
    dump(p/'feedback_schema.json',{'status':'scored | verifier_error','scored':{'score':'finite [0,1]','valid':'boolean','checks':[{'name':'string','pass':'boolean','summary':'string'}],'raw_metrics':'object','summary':'string'},
        'invalid_submission':'status=scored, score=0, valid=false','infrastructure_failure':'status=verifier_error, no numeric reward, process exits 2'})
    dump(p/'evidence.json',{'construction':'source_complete_runtime_unverified','runtime_runs':0,'model_runs':0,'six_hour_curve':None,'oracle_score':None,
      'nop_score':None,'source_review':'static syntax, references, package boundaries only',
      'delivery_gates':['runtime correctness and isolation verification','dependency/image reproducibility and both architectures','difficulty calibration','official Harbor contract mapping']+
        (['market-data redistribution rights'] if kind=='finance' else ['industrial-data redistribution rights'] if kind=='packing' else [] )})
    contract=json.loads((p/'public/contract.draft.json').read_text())
    contract['submission']='Directory content of /workspace/'+SUBMIT[kind]+'; see instruction.md'
    contract['pending_delivery']=['official Harbor schema mapping','built image digests and offline closure evidence','runtime correctness/isolation evidence','long-horizon calibration']
    contract['implementation_status']='reference and verifier source implemented, execution unverified'
    dump(p/'public/contract.draft.json',contract)
    if kind in ['packing','finance']:
        lineage={'upstream':json.loads((p/'source_provenance.json').read_text())['sources'],
                 'use_scope':'local task construction and review; not cleared for training redistribution',
                 'note':'Code license does not establish underlying third-party dataset redistribution rights.'}
        dump(p/'public/DATA_PROVENANCE.json',lineage)
    write(p/'endpoint_notes.md','''归一化公式和常量在 public/scoring_metadata.json。整批统一区分“参考算法”和“理论上界”：上界 1 是公式边界，不是已知可达分数。参考实现位于 solution；没有填写任何未运行的 oracle/nop/model 分数。排样的参考布局将在构建 judge 时生成并冻结；其余参考程序随源码交付。实际端点与难度须在后续验证阶段测量。\n''')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    lock=json.loads((HERE/'base_image.lock.json').read_text());digest=lock['manifest_list_digest'];assert re.fullmatch(r'sha256:[a-f0-9]{64}',digest)
    game_commit=subprocess.check_output(['git','-C',str(ROOT/'materials/repos/wesnoth-1.18.0'),'rev-parse','HEAD'],text=True).strip()
    index=[]
    for task,kind in TASKS.items():
        p=out/task;p.mkdir();cp(BASE/task/'public',p/'public');cp(BASE/task/'private',p/'private');cp(BASE/task/'candidate.json',p/'source_provenance.json')
        (p/'verifier').mkdir();(p/'solution').mkdir()
        for name in ['runtime.py','entry.py']:cp(PARTS/'common'/name,p/'verifier'/name)
        if kind=='formal':
            runtime=p/'verifier/runtime.py'
            text=runtime.read_text().replace('def limits(cpu=1200,memory_gb=8','def limits(cpu=1200,memory_gb=64')
            text=text.replace("'--setenv','OMP_NUM_THREADS','1'","'--setenv','LEAN_NUM_THREADS','1','--setenv','OMP_NUM_THREADS','1'")
            write(runtime,text)
        files=globals()[kind](p)
        if (p/'public/policy_interface.md').exists():
            write(p/'public/instruction.md',(p/'public/instruction.md').read_text()+'\n完整策略调用和状态语义见 policy_interface.md。\n')
        for name in files:cp(PARTS/kind/name,p/'verifier'/name)
        metadata(p,kind);cp(p/'public/instruction.md',p/'instruction.md');cp(PARTS/'common/submit.py',p/'tools/submit.py');cp(PARTS/'common/start_run.py',p/'tools/start_run.py')
        for side in ['agent','verifier']:
            ctx=p/'environment'/side;cp(p/'public',ctx/'public');cp(PARTS/'common/capture_build.py',ctx/'capture_build.py')
            if side=='verifier':cp(p/'private',ctx/'private');cp(p/'verifier',ctx/'verifier')
            if kind=='packing':write(ctx/'lock_packing_dependencies.py',LOCK_PACKING)
            write(ctx/'Dockerfile',dockerfile(kind,side=='verifier',digest,game_commit))
            write(ctx/'.dockerignore','**/__pycache__\n**/.DS_Store\n**/.git\n')
        cp(HERE/'base_image.lock.json',p/'base_image.lock.json')
        write(p/'README.md',f'''# {task}

状态：构造源码齐备，未运行验证。阅读 [题面](instruction.md)、[评分契约](public/scoring_metadata.json)、[参考解说明](endpoint_notes.md) 和 [证据状态](evidence.json)。

- public/：agent 可见材料；solution/：作者参考解，不能放入 agent 环境。
- verifier/：可信评分控制器；private/：隐藏标签/参考资产。
- environment/agent 与 environment/verifier 是两个真实、独立的 Docker 构建上下文。agent 上下文不包含 private、verifier 或 solution。
- task.toml 是明确标注的本地契约；合同的 Harbor schema 尚未提供，未冒充正式兼容。

后续显式验证时构建：`docker build -t {task}-agent environment/agent` 和 `docker build -t {task}-judge environment/verifier`。构建会联网获取依赖，Lean 会构建库，排样会生成冻结参考布局；本轮没有执行这些命令。

agent 运行必须加 `--network none`。开始工作之前运行 `python tools/start_run.py --run-state run/state.json` 固定计时起点。提交 {SUBMIT[kind]} 目录的内容，例如 `python tools/submit.py --judge-image IMAGE_DIGEST --submission SNAPSHOT --run-state run/state.json --record run/curve.jsonl`。启动器冻结提交副本和实际 judge image ID，每次创建新的离线 judge。启动器明确为 bubblewrap 内层 worker 提供命名空间所需的容器权限，未提供 unsandboxed fallback。没有 Docker socket 挂载。

参考解入口：{('solution/solve.py' if kind in ['software','science','packing','formal'] else 'solution/policy.py' if kind=='finance' else 'solution/policy.lua')}。参考解的输出/源码按相同提交契约交给 grader，不直接写分数。镜像构建过程将记录真实依赖版本；构建前不能声称已经取得这些版本的双架构可运行证据。
''')
        index.append({'task_id':task,'category':kind,'status':'source_complete_runtime_unverified','task_toml':task+'/task.toml','instruction':task+'/instruction.md'})
        dump(p/'files.sha256.json',[{'path':str(f.relative_to(p)),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(p.rglob('*')) if f.is_file()])
        print('assembled',task,flush=True)
    dump(out/'index.json',index)
    dump(out/'construction_recipe.json',{'script':'task_factory/assemble.py','sha256':sha(Path(__file__)),'source_candidates':str(BASE.relative_to(ROOT)),
          'component_files':{str(f.relative_to(HERE)):sha(f) for f in sorted(PARTS.rglob('*')) if f.is_file()},'runtime_runs':0,'model_runs':0})
    print('All six source packages assembled. No runtime validation performed.')
if __name__=='__main__':main()
