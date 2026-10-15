# 8个软工题包的长程难度与原题尺度审查

结论：**8个题包均不能据现有证据称为合格的6小时持续增长题。RESTler、HTTPX是优先保留和扩大范围的2个方向；OpenAPI、pytest、EdgeKV的3个当前合同偏窄或早饱和风险高；DataFusion、CRoaring的2个性能目标尚未进入奖励；Tree-sitter当前版本不推荐进入长程标定。**

此前“已构造8题”描述文件与构造进度，并不表示8题达到目标难度。特别是DataFusion和CRoaring，已有草稿包，但关键评分部分没有闭合，不能计为可直接训练的完整任务。

## 本次做了什么

只读获取8题的题面、DIFFICULTY、材料说明、作者结果、评分元数据、真实grader、部分参考实现和已执行基线的原始结果。审查材料快照与SHA256在 `frozen-text-evidence.json`、`additional-evidence.json`、`tree-full-reparse-evidence.json`；这不是整个可执行题包的完整冻结副本。

重新读取本地三个factory原始复现规约、EdgeBench公开原题JSON、已取得的Schemathesis镜像层TODO、论文v1的设计说明和官方时间分数表；在线复核官方仓库与论文页面。对性能计分上限、Tree-sitter强基线及引用分数作数值/原始文件核对。未重新运行候选程序、Docker、教师或付费模型，不把作者历史运行描述为本次新实验；本报告是设计/难度评估，不是完整task-qc或交付通过报告。

本轮用户补充：工程任务必须有足够真实工作量，不能只做一个较小扩展后期待6小时增长。该补充已纳入判断，见 [本轮范围要求](../../requirements/software_long_horizon_scope_2026-10-15.md)。

## 原始EdgeBench到底要求做什么

官方论文§2.2明确描述生产级代码和跨模块工作，单题可能涉及数千行变更，最大规模超过十万行。这是原任务的规模描述，不是本批设置的LOC门槛。主参照是实际交付能力，不是仓库总行数。

原题公开范围和设计说明体现五种工作形态：

| 形态 | 原题锚点 | 通俗描述与真实工作范围 | 支撑长程的候选机制 |
|---|---|---|---|
| 多目标产品演进 | Schemathesis datagen/config/reporting | 完成一份产品roadmap，分别含8/6/5项目标；datagen实际TODO涵盖生成策略、hooks、参数化、双向discriminator等 | 多组真正的产品能力逐步落地，加上交互/兼容性修复；单个retry或journal功能不能代替整份roadmap |
| 系统构建 | Arc compiler/runtime | 根据新语言规格补全编译器和运行时；论文说明覆盖词法、解析、类型检查、代码生成 | 多阶段语义和端到端运行，前层成果供后层使用，不能只实现一个parser helper |
| 跨模块实现恢复 | Rust multicrate CAS | 恢复一个内容寻址存储工作区内多个crate的缺失实现 | API契约、数据模型、crate依赖和CLI集成共同扩大完成面；公开JSON没有给出精确缺失函数数 |
| 行为兼容重实现 | Git→Zig | 实现可替代Git的Zig程序，保持命令输出、退出码和仓库状态一致；允许读C参考，禁止编译或包装其二进制 | 命令/对象/持久状态的广泛兼容，覆盖逐步提高；这些限制来自原任务的重实现目标，不能随意搬来禁用所有正常依赖 |
| 正确性约束下性能优化 | ANN、exchange-core、integer codec、swscale、VLIW | 保持召回/功能/无损/数值正确性的同时，优化真实QPS、吞吐、压缩或周期 | 搜索算法、表示、调度、内存和硬件利用率的质量空间；代码改动可以少，实验和优化深度仍可很大 |

前四类最接近用户要求的“大工程量”路线。第五类也属于原分布，但应通过真实可评分优化空间入选，不能只给一个小功能配上复杂仓库背景。

证据层次：公开12题的JSON在 `data/EdgeBench/`；Schemathesis datagen另读了所抽取work镜像层中的TODO；其余仅论文描述的任务不假装已取得完整实现/测试。原题源码、答案或测例只用于尺度审查，不进入新训练任务的公开环境。

### 官方时间曲线也要对照

以下使用同一官方模型GPT-5.5的公布分数，按官方表的0～100展示尺度；不是我们的运行，也不是gpt-6.1-sol的难度保证。

| 原任务（GPT-5.5） | 2h | 6h | 12h |
|---|---:|---:|---:|
| `ann_vector_search_qps` | 22.3 | 35.1 | 40.7 |
| `arc_compiler_runtime` | 55.5 | 60.9 | 72.4 |
| `exchange_core_throughput` | 15.4 | 39.9 | 53.2 |
| `ffmpeg_swscale_reimplementation` | 8.8 | 15.1 | 15.3 |
| `git_rewrite_in_zig` | 16.1 | 17.7 | 18.4 |
| `integer_compression_codec` | 61.1 | 73.9 | 74.4 |
| `juliet_vulnerability_analyzer` | 81.0 | 85.4 | 89.8 |
| `rust_multicrate_reconstruction` | 27.5 | 53.1 | 57.8 |
| `schemathesis_config_modernization` | 79.1 | 82.9 | 84.0 |
| `schemathesis_datagen_pipeline` | 54.6 | 56.7 | 56.7 |
| `schemathesis_reporting_observability` | 76.6 | 76.6 | 77.1 |
| `vliw_kernel_optimization` | 71.6 | 77.1 | 85.6 |

原题也不保证每个任务、每个模型每小时都增长。例如Schemathesis datagen在6～12小时平台；大型工作量降低了快速整体完成的风险，但仍需用本模型验证剩余问题是否可学、反馈是否能指导改进。

## 八题结论总表

| 当前题包 | 当前已测起点/强基线 | 当前可得分上限 | 工程量与原题差距 | 本轮建议 |
|---|---|---:|---|---|
| RESTler recovery | unchanged starter 0.10；加强pickle基线能跑完普通campaign，但崩溃恢复重复2次POST | 1.00 | 真实跨层恢复，但限定单worker、BFS、无GC，核心仍是一项恢复能力 | 保留，作为优先扩成完整恢复执行子系统的素材；中等潜力，未证6h |
| HTTPX execution policy | unchanged starter 0.46746；两种tenacity薄包装均违反dispatch预算 | 1.00 | auth/redirect/replay/cancel交互真实，但实际是一项policy扩展 | 保留，优先扩大为完整客户端执行子系统；中等潜力，未证6h |
| OpenAPI streaming | unchanged starter 0.03；独立薄包装基线0.60 | 1.00 | 流式SDK加认证/请求体交互，仍明显小于原题5～8目标roadmap | 当前低潜力；优先扩成生成器产品里程碑，或作短程训练 |
| pytest fixture trace | 公开hook-only starter 0.50；完整core方案可达1 | 1.00 | 生命周期journal，不是完整测试框架或报告/插件体系 | 当前中低潜力；需先否证内部方法包装捷径，或实质扩大交付范围 |
| Valkey/EdgeKV | Python starter 0.36；Valkey本体能解决常规事务，但不满足新CLOCK/EKV1合同 | 1.00 | 实际提交是有限命令集Python EdgeKV，并非改造整个Valkey引擎 | 当前中低潜力；扩大系统范围前不能按真实数据库工程估计难度 |
| DataFusion sort | starter与参考均0.25 | 0.25 | 真实系统优化素材，但0.75性能权重关闭 | 暂停长程标定；当前奖励下无超过starter的空间 |
| CRoaring kernels | starter与参考均0.40 | 0.40 | 单个三集合统计扩展，0.60性能权重关闭 | 暂停长程标定；当前奖励下无超过starter的空间 |
| Tree-sitter recovery | unchanged starter 0.14091；完整edit等API+全量重解析基线1.00 | 1.00 | 少量核心消融恢复，且增量效率不计分 | 当前版本退出长程池，可保留作短程恢复练习 |

以上“起点”均注明实际内容。pytest作者把未扩展upstream记作nop=0，但解题者拿到的是hook-only starter=0.50；不能拿0当学生真实起点。CRoaring也存在名为nop的缺实现控制0.08，但真实提供的starter已经0.40。

## 逐题证据卡

### 1. RESTler：保留机制，工程范围需扩大

**真实任务：**将持久化请求、原生BFS重放、动态资源ID/UUID、HTTP内部重试与服务端Idempotency-Key边界统一；继续运行真实RESTler驱动和FastAPI/SQLite服务，而非另写一个假客户端。

**已见证据：**直接修复pickle saver不足。加强模块注册后，普通服务运行可完成26次操作；同一普通加强方案在已提交操作后杀进程并恢复，产生28次操作和16个资源，对应2次POST被重复执行。原始记录在 `evidence/02_restler_recovery/evidence/cheap-crash-result.log`。这证明被测持久化方案存在真实语义缺口；不是证明所有常用恢复方案都很难。

**可能的后期路径：**请求intent/result与transport retry共享逻辑身份；UUID重放、journal损坏/尾截断、receipt、配置指纹和所有权。它们能交付可冻结源码并改变具名得分。但当前12项检查存在共同设计依赖：选对response replay之后，多个检查可能一起通过；故障种类多不等于有12个独立大型工程目标。

**范围缺口：**单worker、顺序BFS、无GC与checkers；当前参考证明的是一个窄profile里的恢复扩展。对照Schemathesis多能力roadmap、Vault SDK多目标韧性（后者只读到论文），本题工程广度仍不足以确认长程。

**下一步与否证：**先独立实现合法的最强恢复方案并记录工作量；若常规response replay快速饱和，应降低当前版本的长程优先级。升级方向是在独立新版本中根据真实产品需求构造更完整执行/恢复子系统，包含彼此确实需要集成的状态、调度、资源生命周期和兼容路径；不直接把当前明确不支持的功能当已具备难度。

### 2. HTTPX：交互真实，仍是较窄特性

**真实任务：**一次逻辑send的预算要覆盖认证、重定向与重试，同时保持有界懒惰body replay、跨origin凭据规则、同步/异步取消与资源所有权。

**已见证据：**tenacity==9.1.2的outer和transport两种方案，在budget=2时均发生3次dispatch；原始JSON保存在 `evidence/03_httpx_transport/evidence/cheap-baseline-tenacity.json`。说明简单外层重试不是完整答案，但ContextVar+共享budget+有界tee的完整包装方案尚未独立实现，不能宣布包装路线被否证。

**后期路径：**统一auth再yield/307/部分消费/溢出与Request.read旁路；同步异步取消、close异常、嵌套并发send及trace隔离。七组部分分能区分这些行为，已有真实原生回归。无性能分，全部有限功能做对即结束。

**风险：**真实参考生产新增代码约三百行（作者说明），不是规模门槛或耗时证据，但说明这不是完整HTTP系统的重建。参考派生去缓存上限控制仍达0.98214，去foreign auth规则达0.90476；这些消融不能视为独立模型能快速获得的分数，却显示高分后的功能尾部可能很短。

**决定：**保留为优先扩大范围的素材。应从完整客户端执行层的实际产品需求形成roadmap，并先测最强合法包装方案。当前仅“中等潜力、早饱和风险未消除”，不直接认定够6h。

### 3. OpenAPI：薄包装已吞掉较多空间

**证据：**独立薄包装基线0.60（21/36），已经解决UTF-8分块、空行、末记录、关闭、同步异步及自然背压。剩余parser/template类型、响应所有权和operation认证继承确实有工程价值，但都围绕一个流式功能族。参考改动5个生成器文件，不能用整个仓库规模估计工作量。

**决定：**当前版本低潜力。对照原Schemathesis datagen的8目标、config的6目标，本题缺少相应产品广度。升级应以真实schema→类型/引用模型→序列化→生成代码→sync/async客户端兼容为完整里程碑，需求与测试都覆盖相应能力；具体目标须重新从素材挖掘，不能把这张建议当已造好的题。

**最便宜否证：**继续完善已存在的合法模板/配置包装，验证剩余要求是否很快饱和；不能因其0.60高而事后删分或禁用模板机制。

### 4. pytest：真实状态语义，产品范围偏小

**证据：**公开starter已经0.50。24项检查按六组计分，另有6个native回归门控；这些是检查结构，不是24项大型实现。解析身份/实例、两层缓存、依赖失效、异常cleanup和observer重入都真实。原始core参考改4个生产文件；两个gold派生消融均为0.91667。

**后期路径：**保留缓存比较次数的身份/依赖追踪；贯通失效原因、所有finalizer、异常组与插件通知次序。它们仍属于同一个fixture journal子系统，未独立检验包装内部方法路线。

**决定：**当前中低潜力；先做合法内部包装的强基线否证。若面向长程，应构造更完整测试执行/扩展/诊断能力roadmap，而不是把更多事件字段或重复用例充当工程量。原Schemathesis reporting同时涉及多格式writer、hook、pytest集成和example生成；这才是更接近的规模参照。

### 5. EdgeKV：数据库语义不等于大型数据库工程

**证据：**原题面要求只提交Python源码，标准库运行，starter已提供协议、socket、类型store、逻辑时间和简易持久化；学生补事务与EKV1日志。共29个固定场景（5/4/5/5/5/5），分成六组。真实Valkey服务器强基线通过常规事务/WATCH，但没有CLOCK和指定日志；这一探针不是可提交完整wrapper的分数。

**后期路径：**per-client队列、WATCH版本/逻辑过期/错误分类；事务效果WAL、fsync-before-reply、尾截断与损坏拒绝。确定性状态与多客户端场景值得保留，但顺序事件、有限命令集、无吞吐目标和已有协议骨架显著缩小工作量。

**决定：**当前中低潜力，不能称真实Valkey大规模改造。可作为较短系统实现训练；若继续长程路线，应先从真实完整数据库/协议子系统获得更大需求面和可信参考，采用NL2Repo/DeepSWE式完整范围，再设计分层验收。原Postgres-wire-on-SQLite是协议服务器、查询、类型与事务集成的规模参照，但本轮只获得它的论文设计说明。

### 6. DataFusion：当前奖励没有优化空间

**直接证据：**`task/authoring/score-spec.json`中performance.enabled=false，实际grader也只计算语义和native分，权重合计0.25。作者原始starter=0.25，reference五次均0.25。性能改进不可能让当前分数超过0.25。

**素材潜力：**TopK/merge/spill/内存池是大型系统的真实交叉点。但现参考主要是identity permutation零拷贝；合法排序元数据API已让同类已知有序输入跳过排序，10次进程重放全部正确。不能用未声明sortedness的弱路径人为放大收益。

**决定：**当前不跑6h。需要新版本里先找到最强调参/metadata基线之上仍有广泛稳定收益的瓶颈，完成真实性能评分与独立计时。工程范围可以是多分区排序/外排执行链的整体优化，不要求为了行数人为重写。若只剩一个小有序快路径，应淘汰该性能合同。

### 7. CRoaring：先验证算法包络，再谈长程

**直接证据：**四组语义分合计0.40，performance.enabled=false，保留的0.60没有公式或锚点；打包starter和参考原始score.json均0.40。当前没有奖励区分算法优化。

**素材信号：**同一主机三轮配对，融合参考相对已优化普通API基线：dense约18.91倍、sparse约0.70倍、run约0.40倍、mixed约1.56倍、window约4.44倍。该主机未独占或锁核，不能当稳定奖励锚点。跨表示存在真实取舍，也可能被简单按容器类型选路快速解决。

**决定：**当前不跑6h；先做简单混合dispatch/独立iterator等强基线，对代表性工作负载配对重放。若仍有充分空间，才能在新版本启用性能目标。若需要扩大工程量，应来自真实批查询/表示/架构兼容需求，不能堆更多三元组输入。

### 8. Tree-sitter：当前版本退出长程候选

**关键区分：**只给受损starter加“忽略old_tree”改动，得0.46861；而保留完整edit/changed-ranges等API的全量重解析方案，原始结果为valid=true、score=1.00、pass_rate=1.00，见 `evidence/14_tree_sitter_incremental/evidence/full_reparse_complete_apis/score.json`。前者不是后者，不能混报。

**含义：**当前检查不足以把增量复用质量与完整正确性区分开；原题在45场景和198检查下仍可由无需高效复用的方案满分。并非“输入少”或“评分小数不够”的问题。原上游恢复也是潜在捷径；未声称这份强基线由不知道参考的模型快速写出。

**决定：**不再用此版本验证6h持续增长；可留作短程恢复练习。若另选增量解析服务级任务，需要从真实任务需求重新设计，不能简单禁止全量解析或增加计数硬门槛来保住这道题。

## 对后续pipeline的具体改变

1. **先选交付物大小。** 素材卡先写“完整产品/完整子系统/产品版本roadmap/完整兼容实现”，列出真正缺失的能力，再让作者构造。单个参数、一个journal、一个retry等默认进入短程池，除非有充分优化深度证据。
2. **正确复用factory。** NL2Repo从可运行项目抽出足以重建的规格；ProgramBench覆盖真实CLI/状态行为；DeepSWE选择完整行为包或产品新需求。不能只借它们的hash、补丁和Oracle包装，却把求解任务压成小功能。
3. **任务工程图。** 交付需求→模块/API/状态→集成场景→局部可冻结成果→计分组。已有库允许正常使用；合法捷径要实际测，若一次合理包装就做完则换任务范围。
4. **原题尺度对照。** 每个候选固定至少一个确实相似的原EdgeBench锚点，指出继承了何种工程范围/优化深度，哪些仍明显较小。不是同仓库名或同“系统”领域就算同等规模。
5. **最强调试基线先行。** 记录真实starter、公开普通工具、配置扫描与wrapper基线；gold mutation只检验评分区分，不能当独立求解难度证据。
6. **奖励闭合再标定。** 禁用性能分、starter已达有效上限、普通基线满分的题不进入6h队列。0～1是表示形式，真实增量必须来自功能质量或性能；当前不存在授权改写旧奖励。
7. **长程最终靠轨迹。** 候选工作量大也可能快速平台或因全零无法学习。按同一冻结任务观察1/2/6h、提交次数、成果变化和重评分；当前没有给这8题补写任何未运行的模型分数。

本次没有改动远端原题、原始参考、任何运行中作者/教师、旧评分或共享配置。新一批6个仍在构造的候选不在本次8题完成范围中，也不能因为项目名称大就自动入选。

## 主要来源

- [EdgeBench论文v1：§2.2、G.4、G.6](https://arxiv.org/html/2607.05155v1)，本地 `research/sources/edgebench-paper.html`。
- [官方任务时间分数表](https://github.com/ByteDance-Seed/EdgeBench#leaderboard)；本地固定提取版本见 `research/software-engineering-2026-10-15/official-software-time-scores.csv`，harness commit `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`。本轮网页表中所用行与本地提取一致。
- 原始公开JSON：`data/EdgeBench/*.json`，HF定义固定版本 `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`。
- 原Schemathesis datagen镜像层TODO：`research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md`；仅层抽取，未声称还原/运行完整原镜像。
- 原factory规约：`upstream/swe-factory/nl2repo.md`、`programbench.md`、`deepswe.md`。它们是用户所给参考副本中的复现规约，不冒充三篇原论文的全部官方实现。
- 开发机出题规范：`/ws/users/wcgu/skills/edgebench-task-authoring/SKILL.md`及source-selection/material-and-scoring/growth-judgement。使用任务自身证据，没有继承其他人的运行结果作为我们的测量。
