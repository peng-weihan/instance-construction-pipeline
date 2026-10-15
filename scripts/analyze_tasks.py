#!/usr/bin/env python3
"""Reproduce the 51-task taxonomy from upstream JSON plus explicit research annotations.

Only stdlib is required. This reads task definitions, never executes judge commands.
Mechanism, generation axes, difficulty and feasibility are research judgments,
not labels claimed by EdgeBench. Run from any working directory.
"""

from collections import Counter
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/EdgeBench"
OUT = ROOT / "research"
MECHANISMS = {
    "build": "软件功能构建", "perf": "性能优化", "solve": "算法与策略求解",
    "learn": "学习与科学拟合", "proof": "形式证明", "deliver": "专业交付物",
    "game": "直接环境交互",
}

ANNOTATIONS = """\
ad_placement_optimization|solve|几何布局|solution.cpp通用求解器|矩形合法性与面积满意度总分；公开seed generator/tester|anchor密度/分布;目标面积;grid尺度;公开/隐藏种子|高密度冲突;目标面积差异;局部最优;时间限制|高：已有生成器接口；仍需取镜像或重建源码
apple_incremental_game|solve|序贯决策;游戏机制|solution.py通用策略|50个固定case分数和；公开gen/tester|机器成本/产能;投资时程;资源;种子|长程复利;短长收益冲突;预算/时程|高：可生case；改经济规则需新task契约
equivalence_class_divide_and_conquer|solve|算法课程式迁移|T1.cpp至T6.cpp|六题权重5/5/10/15/25/40；部分通过仅半原分|等价类问题族;约束梯度;六题能力依赖图|后续变体与先前技巧距离;规模;子任务结构|中：case易；有迁移关系的六题组需设计
grid_turing_robot|solve|程序合成;游戏机制|solution.py输出颜色/状态转移规则|50固定case成本和最小化；公开gen/tester|网格拓扑/障碍;目标轨迹;颜色/状态代价;种子|规则压缩;路径复杂度;状态复用;规模|高：生成器已有；规则族变化需新checker
jagua_nesting_optimization|solve|几何优化;系统实现|Rust lbf/jagua源码|16隐藏strip packing case；独立几何合法性；参考改进|多边形族/凹度;数量;条带宽度;旋转约束|几何复杂度;空隙密度;局部最优;20秒限时|高：几何case易；高质量参考与独立验证关键
molecular_self_assembly|solve|时序调度|solution.py通用调度器|50固定case分数和；公开gen/tester|粒子坐标/轨迹;目标分子数;时间窗;种子|空间/时间耦合;连接可行性;动作排程|高：case可生；新物理/约束族需新task
order_addition_permutation_optimization|solve|单实例黑盒搜索|final_result.txt排列/成本/调用数及搜索源码|重算排列成本；cost比值立方×调用数比值平方根；静态规则检查|隐藏目标函数参数/交互阶数;排列长度;oracle预算|维数;交互阶数;局部最优;查询预算|中：可生目标；需可信oracle调用计数与参考优化
smt_solver|solve|软件功能构建;符号推理|build.sh、solve、src/|4类logic正确率；sat模型验证；超时/unknown/invalid_model反馈|logic混合;公式结构;变量数;可满足比例;语义保持扰动|理论组合;布尔骨架;算术规模;证明/求解预算|高：可生成公式；unsat真值与质量校准需可信参考
treant_forest|solve|序贯博弈;路径规划|solution.py通用策略|50固定case分数和；公开gen/tester|迷宫拓扑;起终点;障碍预算/机制;种子|通道结构;可观测性;规划深度;堵路风险|高：case可生；改变交互规则才是新task族
tree_block_partitioning|solve|算法课程式迁移|T1.cpp至T6.cpp|六题权重5/5/10/15/25/40；部分通过仅半原分|树族;块约束;规模梯度;六题间知识依赖|树形状;约束耦合;渐进复杂度;迁移跨度|中：普通case易；六题递进结构难自动保证
triangulation_coloring_optimization|solve|图/几何联合优化|solution.py|10隐藏N=512；G=X·C+Y·F+U²；仅3公开固定case|三角剖分族;初始染色;X/Y权重;规模|重染/翻边耦合;二次惩罚;局部最优|高：研究模板可生成；原task明确禁止本地随机生成
vehicle_routing_time_windows|solve|运筹优化|C++17 CVRPTW solver源码|逐case可行性、车数NV/路程TD、BKS差距；编译/超时状态|客户分布;容量;时间窗;车队;服务时间;case集合|时间窗紧度;客户规模;路线耦合;时间预算|高：生成可行路线反推输入；必须重算参考标尺
vibrating_path_graph_coloring|solve|图优化|solution.py|50固定case目标和最小化；公开gen/tester|图族/密度;颜色数;删边/同色惩罚;种子|染色冲突;代价不平衡;规模;局部最优|高：图与权重可生；需防分布同质化
warehouse_forklift_routing|solve|动作规划;仿真|solution.py生成叉车动作串|动作合法性与指令长度归一成本；公开gen/tester|R/C布局;入库排列;出库约束;初始占用|密集占用;取放阻塞;重排深度;规划预算|高：序列和布局易生；保证可行及checker独立
wireless_electricity_layout|solve|几何布局;连通约束|solution.cpp输出每根导线平移|50隐藏case传输与移动平方成本；无短路合法性|城市簇;导线位置/长度;源板几何;数量|连通与距离权衡;短路避让;几何规模|高：合成布局易；约束与可信合法基线需联生
college_english_exam_bank|deliver|教育;文档排版|5套试卷及答案DOCX/PDF共20件+2个XLSX|grade_with_codex.py入口；蓝图/重复约束；完整rubric未见|教材语料;课程目标;难度蓝图;套数;重复率约束|覆盖/难度均衡;跨卷低重复;答案一致性;格式|中：内容可生成；专业正确性与稳定rubric成本高
cta_risk_budget_optimization|deliver|算法与策略求解;软件构建|交易系统源码+净值/信号/持仓/成交/风险配置与多份报告|scoring/score.py；完整规则和权重留在镜像|策略集合;资产/币种;市场时间段;成本;风险政策|模块依赖;多币种对齐;成本/风险约束;报告可复现性|中：可参数化业务包；数据真实性/评分耦合需专家
k12_math_recommendation|learn|专业教育;算法构建|train.py、infer.py、models、submission.json|元数据：准确率/掌握度校准/学习增益/教学约束；score.py内部未见|知识图谱;学生群体;交互时序;缺失率;教学约束|冷启动;稀疏日志;分布偏移;多目标|中高：结构化数据可扩；学习增益oracle须明确
portfolio_risk_calibration|solve|专业金融;学习校准|portfolio_optimizer.py和backtest_results.json|元数据：样本外风险调整收益；score.py内部未见|ETF universe;市场时段;风险预算;成本/换手/再平衡限制|非平稳性;风险估计误差;约束冲突;成本|中：资产/时段可批量；独立回测与数据质量关键
"""
# task_id | primary | secondary | artifact | judge/feedback | generation axes | difficulty | feasibility
ANNOTATIONS += """\
bipedalwalker_locomotion_rl|learn|游戏控制;性能约束|policy.pth及可选policy.py/train.py|冻结checkpoint的标准/Hardcore回合回报；aggregate-only奖励摘要|地形与环境参数;训练/隐藏episode种子;正常/Hardcore混合|地形难度;CPU训练预算;稀疏奖励;泛化偏移|高：环境可参数化；需校准训练预算
borden_source_inversion|learn|黑盒逆问题;参数优化|answer.json源参数及复现脚本；judge只读answer.json|隐藏井位和未来时间的预测误差；质量门控与分段封顶|有限矩形源位置/尺度/起止时间;井网;噪声/删失;水文参数|观测稀疏度;可辨识性;噪声;模型失配|高：有可信前向模型后可合成；需剔除不可辨识题
dabic_gravity_inversion|learn|科学复现;专业交付|DABIC指令、两套运行脚本、results.json、report.md|隐藏eval_dabic_v2入口；任务要求L0/L1及D-ABIC/Cooling/L-curve比较；具体权重未公开|合成密度场;测线/网格;噪声;正则范数;实测区域|病态程度;网格规模;算法移植跨度;计算预算|中：合成场易扩展；新实测题与评价需专家
graph_node_classification|learn|算法构建|solution/solution.py|隐藏judge_eval；0..1分数；元数据称未见图节点分类|图生成族;规模;同配性;特征信噪比;标签率;跨图划分|低标签率;异配;分布偏移;CPU/内存限制|高：图/划分可生成；需避免仅换同图测试节点
ann_vector_search_qps|perf|近似算法;约束优化|custom模块和config.yml|Recall@10≥0.95硬门槛后最大QPS；本地QPS/recall|向量分布;维数;数据量;距离度量;召回门槛;硬件配额|高召回门槛;索引内存;查询量;分布偏移|高：workload批量易；需独立计时和硬件固定
arc_compiler_runtime|build|编译器;算法实现|compiler/src/ TypeScript源码|隐藏语义测试的raw/weighted通过数和总分；公共smoke tests|语言特性组合;类型系统;语法;运行时契约;挖空模块|特性相互作用;跨阶段依赖;错误语义;模块数|中：须参考解释器与同步生成spec/测试
exchange_core_throughput|perf|系统工程|Java引擎源码、pom.xml和JVM配置|功能断言通过后Average MT/s；benchmark日志|交易负载;symbol/account数;热点/倾斜;线程/CPU配额|争用;尾部热点;吞吐资源上限;正确性约束|高：负载可生成；须固定测量环境
ffmpeg_swscale_reimplementation|perf|软件重实现;数值兼容|Rust源码编译libswscale_candidate.so|全hidden correctness过门后几何平均speedup；失效类别反馈|像素格式对;缩放比例/算法;分辨率;stride;输入内容|兼容路径数;舍入精度;向量化机会;内存带宽|高：case可大规模生成；任务变体须处理API/基线
git_rewrite_in_zig|build|差分语义兼容|Zig源码与git二进制构建工程|私有测试比较CLI输出/退出码/仓库状态；pytest适配|Git功能子集;仓库历史拓扑;缺失模块;边界场景|功能覆盖广度;状态持久化;CLI兼容;协议细节|中：参考git易作oracle；大功能任务需人工设计
integer_compression_codec|perf|压缩算法;多目标|C++ codec源码与固定ABI|精确round-trip门槛；压缩率与解码吞吐；隐藏runner|整数分布/熵;单调性;重复/异常比例;block长度|分布混合;压缩吞吐权衡;内存带宽;短序列开销|高：可合成且可验证；性能测量需校准
juliet_vulnerability_analyzer|build|程序分析|analyzer.py与辅助源码|隐藏Juliet facts评分及状态；六类CWE；细项公式未见|CWE组合;facts控制流/数据流;跨过程深度;安全负样本|别名;跨过程推理;路径敏感度;误报漏报权衡|中：需已知漏洞真值与语义保持变换
rust_multicrate_reconstruction|build|仓库重建|agent-start/ Rust workspace|public/hidden测试；按layer/crate返回通过数和加权分|仓库/子图;缺失实现集合;API契约;依赖深度|跨crate耦合;状态语义;挖空比例;集成依赖|高：有完整可测试仓库后可自动挖空并校准
schemathesis_config_modernization|build|存量软件演进|Schemathesis仓库改动|分phase通过比例与权重；完整TODO和测试留在镜像|TOML配置/自动发现/API迁移目标包;兼容要求|目标数量;配置覆盖顺序;跨模块迁移;兼容跨度|中：从真实提交/roadmap构建；需求测试对齐昂贵
schemathesis_datagen_pipeline|build|存量软件演进;数据生成|Schemathesis仓库改动|分phase通过比例与权重；完整TODO和测试留在镜像|header策略;coverage hooks;discriminator规则;目标包|schema组合复杂度;生成/验证一致性;目标依赖|中：真实特性组合可扩；须确认组合可实现
schemathesis_reporting_observability|build|存量软件演进|Schemathesis仓库改动|分phase通过比例与权重；完整TODO和测试留在镜像|报告格式;hook位置;pytest集成;例子生成分支|事件顺序;格式兼容;跨工具集成;目标依赖|中：可模块化组装；需真实语义回归测试
vliw_kernel_optimization|perf|编译调度;算法优化|solution.py内KernelBuilder.build_kernel|所有case正确后周期数；返回case周期/阈值；越低越好|kernel计算图;输入形状;向量宽度;issue slots;延迟|依赖链;寄存器压力;访存;可并行度|高：模拟器可控；架构变体需更新公开契约
"""

ANNOTATIONS += """\
carleson_formalization|proof|分析学|Lean工程proof bodies|lake build＋传递axiom检查；声明签名固定；证明完成率|已证工程中的proof-hole子图;依赖层级;辅助引理集合|依赖深度;分析工具跨度;孔洞密度;库检索|中高：有完整证明可挖空；组合难度须编译校准
combinatorial_games_formalization|proof|组合游戏理论|Lean工程proof bodies|lake build＋eval_lean/ListDeclAxiom；声明签名固定|游戏算术/超实数/Sprague-Grundy相关证明子图|归纳嵌套;抽象层数;引理依赖;孔洞数量|中高：真实证明工程可生；非仅改符号名字
flt_regular_formalization|proof|数论|Lean工程proof bodies|传递axiom检查；weighted proof score；依赖未证则上层不计|regular prime相关证明目标;依赖闭包;目标权重|基础数论依赖;跨文件耦合;闭包完成门槛|中高：保留完整参考证明后可批量挖空
lean_analysis_proofs|proof|分析学|Lean工程proof bodies|lake build＋eval_lean/ListDeclAxiom；元数据明确传递依赖|实/泛函分析定理族;proof-hole集合;辅助定义|库跨度;目标依赖;自动化可达性;孔洞密度|中高：参考证明和checker已具备时可做
new_foundations_consistency|proof|集合论|Lean ConNF工程proof bodies|lake build＋传递axiom检查；依赖未证不计|置换模型/类型理论模块;proof-hole子图|深层依赖;新定义理解;基础缺口;类型复杂度|中：任务规模大；子图要保证可解与知识完整
ordinal_notation_well_foundedness|proof|序数算术|Coq源码证明目标|隐藏Coq evaluator；85为rescale上界；具体rubric未见|已证序数记号系统;良基关系;归纳目标;proof holes|序数表示复杂度;嵌套归纳;依赖数量|中：需完整Coq工程与可靠命题/axiom检查
pfr_formalization|proof|加性组合学|Lean PFR工程proof bodies|lake build＋传递axiom检查；声明签名固定|熵/Ruzsa距离/子群覆盖证明子图|数学跨度;目标依赖;库搜索;孔洞层级|中高：可从有证明库抽取依赖闭包
sphere_eversion_formalization|proof|微分拓扑|Lean工程proof bodies|lake build＋eval_lean/ListDeclAxiom；声明签名固定|浸入/jet bundles/凸积分证明子图|抽象几何层数;类型推断;依赖深度|中：可挖空；校准高阶几何任务难度较贵
anchorhead_text_adventure|game|原生在线行动;文本谜题|HTTP命令序列；无文件提交|game_mode；隐藏ROM服务器中的游戏分数|房间/物品/谜题依赖图;剧情分支;ROM或场景|长程记忆;不可逆选择;依赖链;部分可观测|低中：需可控且可验证新world；改名非新题
dcss_dungeon_ai|solve|游戏策略;可提交策略程序|Lua bot rc文件|5固定隐藏seed、每局900s并行、morgue分数均值；本地死亡日志|地下城种子;角色装备;怪物分布;预算;规则场景|生存/收益权衡;提示状态机;策略泛化;动作速度|中高：seed可生；新角色/规则场景需重新校准
nethack_dungeon_agent|solve|游戏策略;可提交策略程序|agent.py的get_action策略|NLE多局游戏分数；本地obs/message/stat反馈|地下城种子;角色/装备;任务目标;观测接口|部分可观测;库存状态;长期风险;分布泛化|中高：程序化地图可生；新目标需judge设计
openrct2_theme_park_ai|solve|游戏策略;可提交策略程序;经营优化|ES5 my_plugin.js|3场景真实company value；约4年；活动/反作弊门控|初始公园;设施/地形;资金/贷款;客流;目标|经营反馈延迟;建设/API依赖;资源约束;场景规模|中：场景包需可行策略与经济基线
openttd_transport_ai|solve|游戏策略;可提交策略程序;网络优化|Squirrel my_ai脚本|5地图seed、20游戏年company value；本地模拟|地图/行业分布;交通模式;成本/经济;初始资源|建设约束;网络收益延迟;扩张时机;规模|中高：地图易生；任务场景差异须超过seed
trinity_text_adventure|game|原生在线行动;文本谜题|HTTP命令序列；无文件提交|game_mode；ROM服务器游戏分数|谜题/道具/房间依赖图;时空线索;ROM或场景|线索整合;精准物件操作;长依赖链|低中：需可验证剧情状态机与可解性oracle
tryst_text_adventure|game|原生在线行动;文本谜题|HTTP命令序列；无文件提交|game_mode；ROM服务器游戏分数；上界350|剧情分支图;关键资源;不可逆选择;结局|长期信用分配;死路;部分可观测;分支数|低中：需可验证新世界；自由文本生成不够
wesnoth_tactical_ai|solve|游戏策略;可提交策略程序;对抗策略|WML配置与Lua策略|3图×seed×repeat；80×胜率+20×胜局效率|地图/阵营;单位/地形;对手策略;初始资源|战术组合;行动顺序;风险;对手多样性|中高：对局可生；新地图/对手分布需固定评测
"""

CASE_VS_TASK = {
    "build": ("固定需求下更换测试输入/仓库状态", "更换缺失模块或功能需求组合并同步规格和测试"),
    "perf": ("固定接口目标下更换负载样本/seed", "更换负载分布族、资源约束或API任务并重标定基线"),
    "solve": ("固定问题定义下更换数值/图/seed", "更换约束族、目标权衡或整套分布/预算并重新校准"),
    "learn": ("固定学习问题下更换split/episode或观测样本", "更换生成过程/科学场景/预测对象及训练和隐藏分布"),
    "proof": ("固定定理仅改名/排列通常不构成新题", "更换证明目标子图及缺失依赖，保留命题与可信参考证明"),
    "deliver": ("固定业务规范仅替换姓名/数字/文件样式", "更换业务资料、目标与约束组合，并同步机器检查和专家rubric"),
    "game": ("固定规则/目标更换地图seed或重开一局", "更换可控场景/目标/规则或知识依赖结构，校准策略与奖励"),
}


def main():
    metadata = [json.loads(line) for line in (DATA / "tasks.jsonl").read_text().splitlines()]
    annotations = {}
    for line in ANNOTATIONS.splitlines():
        parts = line.split("|")
        if len(parts) != 8:
            raise ValueError(f"Expected eight fields: {line}")
        task_id, *values = parts
        if task_id in annotations:
            raise ValueError(f"Duplicate annotation: {task_id}")
        annotations[task_id] = values
    assert {r['task_id'] for r in metadata} == set(annotations)
    rows, coverage = [], []
    for index, item in enumerate(metadata, 1):
        task_id = item["task_id"]
        file = DATA / f"{task_id}.json"
        raw = file.read_text()
        task = json.loads(raw)
        assert task["task_id"] == task_id and task["category"] == item["category"]
        code, secondary, artifact, judge_feedback, axes, difficulty, feasibility = annotations[task_id]
        lines = raw.splitlines()
        line_of = lambda key: next(i for i, s in enumerate(lines, 1) if f'"{key}"' in s)
        inline_wrapper = "import " in task["judge"]["eval_cmd"]
        availability = "本地有JSON定义和镜像tag；未取得镜像内task材料、数据与完整evaluator源码"
        if inline_wrapper:
            availability += "；eval_cmd公开部分执行/聚合包装代码"
        if task.get("game_mode"):
            availability += "；仅有game_server启动入口与ROM路径"
        rows.append({
            "task_id": task_id,
            "official_category": item["category"],
            "mechanism_primary_research": MECHANISMS[code],
            "mechanism_secondary_research": secondary,
            "description_official": item["description"],
            "deliverable": artifact,
            "submit_paths": ";".join(task["submit_paths"]),
            "judge_and_feedback_observed": judge_feedback,
            "parser": task["judge"]["parser"],
            "score_direction_explicit": task["judge"].get("score_direction", "未显式设置"),
            "rescale": json.dumps(task["judge"].get("rescale", {}), ensure_ascii=False),
            "eval_timeout_sec": task["judge"]["eval_timeout"],
            "game_mode": bool(task.get("game_mode")),
            "internet": task["internet"],
            "candidate_generation_axes_research": axes,
            "difficulty_axes_research": difficulty,
            "batch_generation_feasibility_research": feasibility,
            "case_change_research": CASE_VS_TASK[code][0],
            "task_change_research": CASE_VS_TASK[code][1],
            "availability_at_local_snapshot": availability,
            "evidence": f"data/EdgeBench/tasks.jsonl:{index};data/EdgeBench/{task_id}.json:{line_of('submit_paths')} (submit_paths);{line_of('agent_query')} (work.agent_query);{line_of('eval_cmd')} (judge.eval_cmd)",
        })
        coverage.append({"file": str(file.relative_to(ROOT)), "total_lines": len(lines), "read_lines": len(lines)})
    OUT.mkdir(exist_ok=True)
    with (OUT / "task_taxonomy.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    extra = [DATA / f for f in ("tasks.jsonl", "README.md", "BENCHMARK.yaml")]
    for file in extra:
        n = len(file.read_text().splitlines())
        coverage.append({"file": str(file.relative_to(ROOT)), "total_lines": n, "read_lines": n})
    stats = {
        "snapshot": "6cc5a7f1b3288ce52484ad828177b8cc86b05b75",
        "tasks": len(rows),
        "official_categories": dict(Counter(r["official_category"] for r in rows)),
        "research_mechanisms": dict(Counter(r["mechanism_primary_research"] for r in rows)),
        "parser": dict(Counter(r["parser"] for r in rows)),
        "internet_true": sum(r["internet"] for r in rows),
        "game_mode_true": sum(r["game_mode"] for r in rows),
        "work_judge_task_pairs": len(rows),
        "image_tag_references": sum(bool(json.loads((DATA / f"{r['task_id']}.json").read_text())[side].get("image_tag")) for r in rows for side in ("work", "judge")),
        "inline_eval_wrappers": sum("公开部分" in r["availability_at_local_snapshot"] for r in rows),
        "coverage": coverage,
        "coverage_note": "Coverage records full manual review of physical JSON/document lines, not container contents. Escaped multiline fields were reviewed as text.",
    }
    (OUT / "task_taxonomy_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "coverage"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
