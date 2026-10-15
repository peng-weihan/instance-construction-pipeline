# 原版 EdgeBench 软工题：结构性难度证据草稿

本稿只分析原版题面、公开评分包装器、选定镜像层里的一个 TODO，以及本地冻结的论文和官方时间分数表。未读新候选源码，未运行模型或容器。本地官方材料没有联网刷新。

## 核心判断

要复制的是一个真实软件交付中不断暴露的新工作：理解现有系统、让若干能力协同、维持已有契约，再借助诊断找到下一处瓶颈。原版既有产品发行级 roadmap，也有完整能力链的恢复、行为兼容重实现，以及正确性约束下的性能搜索。不能统一改写为“更多 TODO + 更多边界 case”。

论文把软工困难描述为生产级代码、跨模块依赖，以及正确性与性能要求（`research/sources/edgebench-paper.html:391`）；这是总体设计说明，不证明每一道题都有这些属性。论文明确要求持续学习的工作流和足够高的天花板（同文件 `381`），又把本地调试与外部 judge 分开（`427–436`）。长预算只是实验条件，是否难、是否能在后期继续学习，应看实际轨迹。

## 8 个证据锚点

| 锚点 | 实际交付与难度来源 | 可迁移规则 | 证据强度与边界 |
|---|---|---|---|
| 1. Schemathesis 完整发行迭代 | 一个 API 测试框架发行中同时增加结构化 headers、coverage hooks、多 schema pytest、双向 discriminator、503 retry、多错误报告、regex AST 变换；原有公共 API 继续可用。难在理解框架扩展点，并让新行为进入已有用户流程。 | 选真实用户目标，提出一组足以形成完整版本交付的能力；每项要能从公开入口使用，原有集成仍能工作。 | 实际 TODO 全读：`research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md:5–26,170–177`。仅选定镜像层，非最终 OCI 文件系统复原。 |
| 2. 同一语义贯穿多处管线 | Discriminator 在请求生成时反向解析 mapping、恢复 bundled ref 的原 URI、向组合分支注入 const；在响应验证时把显式 mapping 与隐式 schema 名一起识别。不是新增一个独立函数就完成。 | 让一个真实概念穿过解析/归一化、生成或执行、验证和报告；分别定义每个边界，并检查同一输入经过整条路径的结果。 | 同一 TODO `88–120`。注意两端语义并非简单一套规则复用：响应检查始终合并两种已知值，请求生成还区分 `is_response_schema`。 |
| 3. 兼容组合及作用域隔离 | Coverage hook 既要 filter 再 map，又要遵守 global→schema→per-test 顺序和既有 skip 逻辑；多 schema decorator 支持 sync/async，并保证重复装饰同一个 base function 不串状态。 | 从产品已有能力推导组合：模式、作用域、生命周期、可重入性；新能力必须与这些机制共同工作。 | 同一 TODO `56–84`。可以确认真实目标组合，尚未读源码和 hidden tests，不能确认评分到底覆盖了哪些交互。 |
| 4. Arc / Rust CAS 的依赖链交付 | Arc 要 lexer→parser→type checker→codegen 完整编译管线；Rust CAS 要恢复多 crate 内容寻址存储。修复下层后才有条件发现上层语义问题，反馈应定位到能力层。 | 选择有自然先后关系的完整能力链；恢复一个可运行的纵向切片，再扩展语义，避免把独立函数随机删空。 | 论文 `4983,4992`；`data/EdgeBench/arc_compiler_runtime.json:24,28` 与 `rust_multicrate_reconstruction.json:25,29`。Rust wrapper 明确有 layer/crate 公共、隐藏反馈；未取得实际 crate 清单、规格及删除范围，不能替它编造依赖图。 |
| 5. Git 的历史状态与外部行为兼容 | 交付可替代 `git` 的 Zig 二进制，输出、退出码及仓库状态与 C reference 一致。状态是多次命令之间持续积累的，某条命令的局部成功不代表下一条能消费其结果。 | 为另一范围明确的工具设计真实工作流：创建→修改→查询→重新打开；让多个命令共享同一持久格式，检查输出和副作用。 | `data/EdgeBench/git_rewrite_in_zig.json:24,28`；论文 `5055`。持久状态的工作流设计是据契约推导的构题建议；未读 hidden 命令覆盖，不声称原版已测 Git 全部语义。 |
| 6. FFmpeg：兼容已成立后仍有优化空间 | 固定 C ABI 的 create/process/destroy，10 种格式、3 种缩放算法、stride、色度抽样、定点舍入与边界系数；保持质量门槛后优化速度。题面最后的 Current Scaffold Baseline 已称 Rust scaffold 30/30 正确，主目标变成性能。 | 提供正确但慢的可运行起点，让性能工作发生在真实语义约束内；每次优化有精确兼容回归和独立计时。 | `data/EdgeBench/ffmpeg_swscale_reimplementation.json:21,25`；论文 `5046`。题面同时保留旧 26/30、四个失败指导与末尾 30/30 段；以末段理解当前意图，实际镜像未验证，不能把描述中的 30/30 当本地实测。 |
| 7. ANN / exchange-core / integer codec / VLIW：不同优化深度 | ANN 可直接使用 FAISS，围绕 Recall@10≥0.95 最大化 QPS；exchange-core 可改线程拓扑、批处理、orderbook/JVM，但 ringBuffer 已被测试固定；codec 同时追求压缩率和解码吞吐且精确 round-trip；VLIW 只改一个 solution.py 仍能搜索生成指令与 cycle 数。 | 给能测量的真实目标和资源环境，允许正常依赖；让算法、数据布局、调度等结构改进仍有收益，而不是只靠参数扫描。规模不是 LOC，单文件也可能很深。 | `ann_vector_search_qps.json:15,19–28`；`exchange_core_throughput.json:20,24–33`；`integer_compression_codec.json:23,27–36`；`vliw_kernel_optimization.json:24,28–37`。ANN 与 exchange 详细 judge 不在 JSON；codec 组合公式未取得。 |
| 8. 协议映射、状态机与生命周期 | 论文中的 PostgreSQL-on-SQLite 同时有认证、simple/extended query、类型、事务、catalog；TLS trace checker 有状态转移、key schedule、消息验证；Vault SDK 有公平调度、token 持久缓存、hooks。 | 用一个实际端到端场景牵引状态、失败和恢复；每一新增机制应有产品意义，且前一次操作影响下一次。 | 仅论文设计说明：`edgebench-paper.html:5181,5244,5253`。不知道实际规格、起点与评分，不宜据此断言它们已有 crash recovery、并发竞争或特定攻击序列。 |

## 不能照搬的解释与反例

1. **“八项 roadmap 一定都是强耦合”不成立。** Schemathesis TODO `15` 明说若干 independent improvements。原版有两个可共存的来源：发行完整度带来的工作宽度，以及共享管线带来的语义深度。构题可同时用这两者，但不需要把每项强行串成一个人工依赖链。
2. **“禁止库才足够难”不成立。** ANN 的公开题面直接允许预装 FAISS，并列出 IVF/HNSW/PQ 等方向（JSON `15`）。禁止包装 reference 可以保护重实现目标；普遍禁依赖不是可迁移难度规律。
3. **“越大越 long-horizon”不成立。** VLIW 提交只有 `solution.py`（JSON `9–10,24`），官方表里 GPT-5.5 仍从 2h 71.6 增至 12h 85.6；而范围极大的 Git 有明显低分平台。文件数与 LOC 不能代替算法深度和反馈收益。
4. **“持续运行就持续进步”不成立。** 官方聚合表中 Schemathesis datagen 的 GPT-5.4 从 2h 到 12h 均为 56.6（CSV `49`）；Opus 4.8 从 4h 到 12h 均为 70.2（`47`）；Git Opus 4.8 在 4h、6h、8h 都为 22.8（`22`）。这可能是能力瓶颈、反馈不足或局部策略停滞，不能单凭平台判断原题不难，但也不能拿它证明长时学习有效。

## 官方时间分数：可用来设校准问题，不能直接转成验收阈值

来源：`research/software-engineering-2026-10-15/official-software-time-scores.csv:1–61`，共 12 题×5 模型 = 60 行；Rust/Opus 缺值（`37`），故有效 2h/6h 对是 59。已独立用 CSV 重算：2h→6h 中位增益 4.4 分，3 对无增益；4h→6h 有 8 对无增益，与 summary.json 一致。每行标注官方四舍五入聚合、源 commit `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`；不是本地轨迹、不是 gpt-6.1-sol 实测，也不能把跨模型/任务的 59 对当独立样本做显著性结论。

有利于观察长期优化的例子：ANN Opus 4.8 为 26.2→57.0→58.6（2/4/6h，`2`）；exchange-core GPT-5.5 为 15.4→37.2→39.9→53.2（2/4/6/12h，`13`）；Rust GPT-5.5 为 27.5→42.6→53.1→57.8（`38`）；VLIW GPT-5.5 为 71.6→75.7→77.1→85.6（`58`）。不同题的原始分与归一化不同，不能把 50 分理解成相同完成比例。论文 `6537` 说明聚合预定三次独立运行但部分单元不足三次；CSV 不含完整单次轨迹和方差，无法解释每次进步发生了什么。

因此新题试跑除了终分，应保存每次可构建产物、分层得分、失败类型、优化决策及时间：早期是否能形成可运行纵向切片；中期是否需要跨模块修订；后期新增时间是否带来有意义的新能力或效率收益；停滞究竟来自技术困难还是等待、工具失败、规格缺失。不要为了追求持续增益而人为拖慢 build 或加重复任务。

## 从证据迁移到构题的规则

- **先写真实交付验收，再找难度。** 用户能用什么新工作流、原有能力必须保留什么、怎样检查失败和资源释放；技术点来自交付需求。
- **至少有一个会贯穿多层的核心概念。** 例如 schema tag、事务状态、持久格式、调度依赖。只加一个 facade，下面仍是现成库代理，难度通常不足；但允许正常依赖。
- **宽度有产品边界，深度有语义来源。** 用一组共同服务一个版本目标的功能形成宽度；用模式、作用域、生命周期、历史状态和性能约束形成深度，不列笛卡尔积式人为组合。
- **保留有意义的起点和可观测中间进展。** 从真实可构建版本出发；阶段反馈对齐能力，而不是给 LOC 或静态标记计分。正确性恢复与性能优化可采用不同的反馈/计分逻辑。
- **只把有证据的自然约束设成硬门槛。** ABI、文件格式、协议、正确性是产品约束；通用禁库、指定手写、无理由限制实现属于另外的测量目标，需单独说明，不能默认用它们补难度。
- **同难度只能通过运行校准。** 题面分析得到“有这些结构性难点”，不能得到“已达到原版六小时/十二小时难度”；应对比相同模型、工具、预算和资源下的完成路径与平台原因。

## 已读文件与覆盖明细

- `research/software-engineering-2026-10-15/software-task-map.csv`：完整 37 行，36 个软工任务的索引、材料缺口和原有研究标签。标签是本地研究整理，不当成官方分类原文。
- `data/EdgeBench/` 下以下 12 个公开软工 JSON：`ann_vector_search_qps`、`arc_compiler_runtime`、`rust_multicrate_reconstruction`、`exchange_core_throughput`、`ffmpeg_swscale_reimplementation`、`git_rewrite_in_zig`、`integer_compression_codec`、`juliet_vulnerability_analyzer`、`schemathesis_datagen_pipeline`、`schemathesis_reporting_observability`、`schemathesis_config_modernization`、`vliw_kernel_optimization`。完整读各自 agent_query、提交路径、评分元数据及 eval_cmd；三份 Schemathesis wrapper 的 SHA256 相同，完整读一份并比较其余两份。只读公开定义与包装器，没有实际隐藏评分器/源码。
- `research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md`：完整 177 行；这是选定层材料。
- `research/sources/edgebench-paper.html`：抽取并完整读 §§2.1–2.3（350–436）、软工 36 题设计说明表（4950–5292）、G.6 聚合说明（6534–6537）；其他正文只通过定向检索定位，不宣称论文全文阅读。
- `research/software-engineering-2026-10-15/official-software-time-scores.csv`：完整 61 行；`official-software-time-score-summary.json`：全文；重算三项摘要计数。
- Memory 仅用作证据边界提醒：`/Users/raymone/.codex/memories/MEMORY.md:18`（离线隔离与 snapshot 评分）。上面所有原题判断均以当前读取的本地文件为准。

未覆盖：其余 24 题完整题面、原版完整镜像文件系统、实际 TODO/SPEC 之外的生产源码、隐藏测试/权重、完整单次轨迹；没有宣称全仓覆盖或任何新候选的难度验收。
