# 以原EdgeBench规模为锚点的软工出题流水线v2

本轮将“找一个仓库→补一个特性→希望能跑6h”改为“选择真实任务形态和足够范围→找完整素材→先否证捷径→构造完整参考/题包→独立审查→再标定”。新脚本不会把作者自报的constructed、Oracle或静态通过当作长程验收。

## 5条路线

这5类是本项目对论文中全部36道软工题的研究分类，不是官方新增标签；其中12道有公开JSON。完整逐题归类在 [taxonomy.json](taxonomy.json)，来源与hash一并保存。

| 类别 | 原题数量 | 原题参照 | 找什么素材 | 工程量/难度怎样提高 |
|---|---:|---|---|---|
| M1 产品级多目标演进 | 13 | Schemathesis、Copier、Litestar等 | 完整产品roadmap、跨版本需求、生产接口和集成回归 | 扩大真实产品能力与兼容面；完成多组目标及其集成，不限于一个特性 |
| M2 按规格构建系统 | 12 | Arc、类型检查器、协议服务器等 | 可运行完整参考项目、规范、API、状态与错误语义 | 构建完整库/引擎/大型子系统；工程广度与核心算法共同提高 |
| M3 正确性约束性能优化 | 6 | ANN、exchange-core、codec、VLIW等 | 真实workload/profile/回归、最强普通配置 | 深化算法、表示、并行与资源取舍；不要求人为增加文件数 |
| M4 跨模块恢复 | 3 | Rust multicrate、regex-automata等 | 完整健康gold、生产依赖图、行为包 | 恢复多个生产模块/层次及其协作，不能只删几个条件 |
| M5 行为兼容重实现 | 2 | Git→Zig、libexpat汇编等 | 完整CLI/ABI核心行为、状态与参考程序 | 扩大真正兼容面、文件格式和多步行为；不是几个flag |

素材查找按此分类分流，而不是对所有仓库运行同一删函数模板。细节见 [路线配置](../../task_factory/swe_routes.json)。原题的事实依据见[原题研究](../software-engineering-2026-10-15/original-software-tasks.md)和[论文G.4](https://arxiv.org/html/2607.05155v1#A7.T7)。

## 每条路线当前的真实尝试

| 路线 | 当前来源 | 构造意图，尚非已实现任务 |
|---|---|---|
| M1 | scrapy/scrapy | 选择并实现完整crawler产品里程碑，覆盖多个生产能力和端到端流程 |
| M2 | lark-parser/lark | 从真实完整参考抽取解析工具库/引擎规格，构造grammar→lexer→parser→tree/transformer链 |
| M3 | apache/datafusion | 在强配置/metadata基线之上寻找执行链瓶颈，必须闭合真实性能奖励 |
| M4 | BurntSushi/ripgrep | 根据matcher/searcher/ignore/CLI等生产依赖构造大范围多crate恢复 |
| M5 | ninja-build/ninja | 构造Rust替代实现的完整核心行为契约，覆盖解析、依赖、增量状态和多步构建 |

版本均在 [source-registry.json](source-registry.json)固定。Scrapy、Lark、ripgrep、Ninja的HEAD在开发机通过git实际解析为40位SHA；DataFusion继续用已冻结版本，不能把新HEAD与旧测量混合。来源选择只说明候选方向；当前缺口/可构造范围由作者读取固定源码和真实探针后决定。

5条原生gpt-6.1-sol作者的独立目录为 `/ws/users/raymone/edgebench/swe-route-authoring-005-20261015-r3/jobs/`。启动收据与实时核验保存在 `runs/swe-route-authoring-005-20261015-r3/`，不以存在计划文件代替启动证据。原先22个候选及所有rollout保持原版本。

## 新的完整工作链

1. **规则脚本收集素材线索。** 冻结源码tree、公开issue/PR线索、URL、观察时间和SHA；当前issue状态不证明固定版本缺功能。下载失败保留错误，不以空文件冒充素材。
2. **CLI作者筛选范围。** 每份来源至少比较三个有依据的完整候选范围；一项窄提案被包装否证后继续检查其他范围。写 `MATERIAL_MINING.json`，包括实际读取/探针和选择理由。
3. **CLI作者写工程规格。** `SCOPE_CARD.json`列已有能力、真正缺失交付、需求→模块/API/状态→场景→成果→计分关系；`REQUIREMENTS.json`固定合同。原始工程量以此描述，LOC/文件数只是信号。
4. **参考与强基线。** 构造完整可运行参考；实际跑student starter、最强普通配置/库/包装、适当partial。独立基线、参考消融、空提交和starter分开。纯探针标probe_only，不填不存在的完整分数。
5. **任务实现和打包。** 独立agent/verifier上下文，公开契约与开发反馈，私有权威评分/参考，普通依赖正常保留。分别适配DeepSWE、NL2Repo或ProgramBench构造机制。
6. **静态阻塞检查。** 校验内部authoring card、实际报告文件与hash/score一致性；拦截starter或独立基线饱和、性能分禁用、缺报告/包文件、把gold mutation当独立基线等情况。没有数值报告不填0。
7. **独立设计/运行审查。** 在原题尺度下审查作者的工程范围和便宜捷径，再用实际task-qc/原生与周期入口完成运行检查。这一步没有因静态脚本通过而自动完成。
8. **真实6h标定。** 技术闭环及用户指定后端容量允许时，先打一条；有增长潜力后补另外两条。保留原分、检查成果变化和重评分稳定性，再按正式口径判断。此版本pipeline不自动启动付费教师或云实例。

## 可执行入口

```sh
# 分类全部36道原题
python -m edge_factory swe catalog --output /tmp/swe-taxonomy.json

# 收集所选来源的固定tree和当前公开issue/PR线索，输出必须是新目录
python -m edge_factory swe harvest \
  --sources research/swe-pipeline-v2-20261015/source-registry.json \
  --output /tmp/swe-primary-leads-NEW

# 生成类别专用作者任务，不运行模型
python -m edge_factory swe plan \
  --sources research/swe-pipeline-v2-20261015/source-registry.json \
  --output /tmp/swe-author-plan-NEW \
  --remote-root /ws/users/raymone/edgebench/swe-author-plan-NEW

# 只校验已返回作者job的材料/报告/包一致性
python -m edge_factory swe gate --job /path/to/returned-author-job \
  --output /tmp/swe-static-admission.json
```

SCOPE_CARD模板见 [scope-card.schema-example.json](scope-card.schema-example.json)。它是内部出题材料，不是Harbor扩展字段。模板包含占位符和示意，不是合格实例，不能直接用于评分。gate即使全部结构检查通过也只输出 `needs_independent_scope_and_runtime_review`，`runtime_verified`与`six_hour_verified`始终为false。它不证明磁盘上的报告真实执行过，也不能自动识别作者声称的工程量是否充分。

原有 `edge_factory run` 仍是早期routing prototype，未被冒充软件任务生成器。新的软件入口明确为 `edge_factory swe`。

## 旧候选如何处置

最初16条全部返回：8 constructed草稿、3 held、5 rejected；8题的独立难度意见以[审查报告](../swe-difficulty-review-20261015/REPORT.md)为准。其后6条是旧范围下的构造，返回也必须经过同一范围审查，不能因项目很大而自动合格。新5条按类别构造，允许失败/hold，但不能用窄小题凑数量。

我们只新增本地代码、指导副本与自己名下新job；未修改共享skill/原始factory、旧作者进程、原题、旧评分或轨迹。账户使用新4/5/6，单账号实际观察加本批租约保持在既有工程上限10以内；这不是供应商官方配额声明。

验证见 `tests/test_swe_pipeline.py`，覆盖已观察的错误准入模式。测试不调用模型、Docker或云平台，也不证明任务难度。
