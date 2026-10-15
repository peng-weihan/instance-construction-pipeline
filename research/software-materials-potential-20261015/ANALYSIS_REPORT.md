# 50 项软件工程素材的高难题潜力评估

评估日期：2026-10-15。固定版本来源见[原素材登记](../software-materials-expansion-20261015/candidates.json)。

**有潜力，但当前适合优先投入的是其中14项。** 对50项逐一复评后，A优先细化14项、B条件保留23项、C重设范围13项、D当前搁置0项。这里判断的是给定合理范围后能否形成实质工程，以及作者下一步值得投入什么；没有把项目复杂度换算为模型完成小时数。

[50项完整评估表](ALL_50.md) · [CSV](assessments.csv) · [完整逐项JSON](assessments.json) · [判据](RUBRIC.md) · [核验结果](validation.json)

## 什么样的素材值得做高难题

本次把三个问题分开：系统语义有没有高难上限；拟交付范围在正常依赖允许时还剩多少实质工作；作者能否用稳定健康参考和独立判据做成可评测题。只有第一个成立，不足以进入优先组。

判断承接[全部36道原软工题的合同层分析](../software-difficulty-design-20261015/ANALYSIS_REPORT.md)，覆盖完整产品版本、规格系统、性能优化、关联恢复和兼容重实现。产品版本可以有多个独立但合理的目标；小内核也可以很难；不要求所有素材都靠跨模块强耦合。

尤其关注初步可用之后还剩什么：下一种合法组合是否需要修改共享表示，下一次操作是否消费了先前状态，旧接口是否限制新实现，以及正确性约束是否留下真实资源取舍。普通配置/包装/全量重算若完整满足合同，应接受并下调难度判断。

## 分档与素材池的实际强弱

| 原库存路线 | A 优先细化 | B 条件保留 | C 重设范围 | 主要判断 |
|---|---:|---:|---:|---|
| M1 产品演进 | 3 | 3 | 4 | 有完整产品目标的候选；必须先排查原生插件已覆盖 |
| M2 系统能力 | 2 | 1 | 7 | 其中A两项及B一项实际更适合恢复路线，纯规格系统方向仍薄弱 |
| M3 性能优化 | 0 | 10 | 0 | 全部等待强基线后的实测剩余空间 |
| M4 实现恢复 | 5 | 4 | 1 | 状态与语义链最具体，但缺口构造和参考回填风险必须另验 |
| M5 行为兼容 | 4 | 5 | 1 | 多步工作流有价值，成熟库适配是首要对照 |
| 合计 | **14** | **23** | **13** | D为0；未判任何整个项目永久无价值 |

**这批素材在恢复与兼容方向更强，在纯规格系统构建方向还不均衡。** 五类各10个只是数量覆盖。Thrift、Cap’n Proto、Flecs的现有推荐范围实质是实现恢复，建议调整构题路线；本次保留原登记标签以便追溯。

A表示值得先构造样题与验证基线，并非已经达到EdgeBench相近难度。B可能很难，但存在足以使整个方向失效的未知。C评价当前拟题边界；有合理真实宿主或新产物边界后可以重新进入评估。逐项potential字段只记录技术上限，不能加总成高难题数量或成题概率。

## 最建议先细化的8项

以下排序同时考虑语义深度、范围可收敛性和作者成本，不是预计模型成功率的排序。前6项作者成本相对适中，后2项同样有潜力但参考与工具链投入较大。

| 素材 / 交付 | 高难潜力来自哪里 | 最先排除的简单方案 |
|---|---|---|
| [helix-editor/helix](../software-materials-expansion-20261015/cards/69_helix.md) / [固定源码](https://github.com/helix-editor/helix/blob/ba40e547426b0f9896c8bdc699a4ab11f2b37dbc/helix-core/src/transaction.rs#L163)：多选择区编辑内核 | 编辑组合/反演、Unicode坐标、撤销后分叉及跨分支历史相互约束；文本正确之后仍需恢复选区和历史。 | 快照+标准diff能否完整满足公开Transaction/Selection合同 |
| [pallets/jinja](../software-materials-expansion-20261015/cards/68_jinja.md) / [固定源码](https://github.com/pallets/jinja/blob/5ef70112a1ff19c05324ff889dd30405b1002044/src/jinja2/compiler.py#L945)：多模板编译与执行恢复 | 继承、super、局部作用域、macro及同步/异步关闭共享Context；单模板渲染成功远非完整交付。 | 健康模板引擎包装或旧编译缓存能否全解 |
| [sqlalchemy/alembic](../software-materials-expansion-20261015/cards/28_alembic.md) / [固定源码](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/alembic/autogenerate/compare/tables.py#L83)：保数据的数据库重构版本 | 对象身份必须贯穿metadata差异、依赖顺序、脚本渲染和升级/降级；可做产品里程碑。 | 原生Rewriter/插件能否完成关联rename加属性变化的往返 |
| [go-task/task](../software-materials-expansion-20261015/cards/47_task.md) / [固定源码](https://github.com/go-task/task/blob/ad2782e1709f0bcf8fbbe0d8e00c2d239141e099/internal/fingerprint/sources_checksum.go#L31)：本地工件缓存产品 | 调用身份、依赖、产物恢复、成功发布和失败/取消属于同一生命周期；hash helper只是起点。 | sha256+tar和成熟缓存适配能否覆盖整个生命周期 |
| [mikefarah/yq](../software-materials-expansion-20261015/cards/72_yq.md) / [固定源码](https://github.com/mikefarah/yq/blob/a814ff5166040ec745a96bddd79ee31c3a548e83/pkg/yqlib/operator_assign.go#L32)：保结构的配置更新兼容 | 选择上下文、相对赋值、alias与多文档回写相互影响，不能只做JSON值变换。 | round-trip YAML AST加查询库能否全部完成 |
| [johnkerl/miller](../software-materials-expansion-20261015/cards/76_miller.md) / [固定源码](https://github.com/johnkerl/miller/blob/3fa2b291fc7bd93f491c93c2453e7d50a18d645d/pkg/transformers/join.go#L18)：带跨记录状态的数据流工具 | 类型、DSL作用域、begin/main/end、重复键join和流结束相互作用，基本filter后仍有自然里程碑。 | 关系引擎或awk加薄DSL转换是否足够 |
| [pydantic/pydantic](../software-materials-expansion-20261015/cards/70_pydantic_core.md) / [固定源码](https://github.com/pydantic/pydantic/blob/8cd3bec6c7e1d360d92193841613465d30f63955/pydantic-core/src/validators/union.rs#L103)：校验到模型序列化的关联恢复 | strict/lax、union分支状态、模型实例身份、结构化错误及serializer形成跨表示语义链。 | 普通校验器适配是否足够；健康同版wheel是否直接泄漏参考 |
| [quickwit-oss/tantivy](../software-materials-expansion-20261015/cards/38_tantivy.md) / [固定源码](https://github.com/quickwit-oss/tantivy/blob/8a4cfc40f5b7446c0700471aa50290dbb7f8ea97/src/reader/mod.rs#L15)：索引提交与视图生命周期恢复 | 提交/删除、显式reload、旧searcher和失败提交后的重开必须一致；单次检索不足。 | 全量重建+视图快照能否薄适配全部公开语义 |

另外6个A候选是 **mitmproxy、SQLFluff、rsync、Cap’n Proto、Flecs、Nushell**。mitmproxy需要把变量作用域与回放失败/取消真正做成完整场景产品；SQLFluff需要模板源映射和多轮修复而非几条格式规则；rsync需要过滤/保护/删除/链接跨次一致性；Cap’n Proto、Flecs、Nushell需要选出健康可起步、自然关联的恢复边界。

这些方向都不能靠现有实现的内部复杂性保证难度。例如Helix的快照历史可能比原实现简单且仍满足合同；Flecs的普通命令队列加全扫描也可能足够。若这些方案薄适配即可全解，应承认当前范围偏容易，不追加无产品根据的性能阈值或私有布局要求。

## 有上限，但暂时不优先构题的23项

- 性能10项：DuckDB、simdjson、libvips、LZ4、Lucene、RE2、fast_float、libjxl、LMDB、oneTBB。优先测DuckDB/libvips/LZ4/Lucene；后续再考虑simdjson/RE2/libjxl，以及验证成本更高或余量更不明确的LMDB/oneTBB/fast_float。小范围不是fast_float后置的原因，精确舍入有足够技术深度，未知在于成熟基线之后还剩多少可测空间。
- 恢复与前端5项：Tokio、Rustls、Thrift、Ruff、syn。前两者先解决可确定评分的调度/对端与健康参考；后三者要证明工作覆盖完整消费链，不只剩parser helper。
- 其它8项：tox、Celery、APISIX、curl、cmark-gfm、Pandoc、restic、Wireshark。分别先排查锁/记录包装、broker故障模型、配置版本判据、成熟库/整工具适配、仓库格式及离线重组工具链。

性能路线的现有能力并不弱：DuckDB已支持并行外排聚合；oneTBB已有grain/partitioner控制；libjxl已有effort取舍。这些正常路径都应进入强基线，而不是被关闭制造收益。[DuckDB官方设计](https://duckdb.org/2024/03/29/external-aggregation)、[oneTBB官方文档](https://uxlfoundation.github.io/oneTBB/main/tbb_userguide/Controlling_Chunking_os.html)、[libjxl官方说明](https://github.com/libjxl/libjxl/blob/main/doc/encode_effort.md)。本次没有测量任何收益。

从profile看到热点还不够：作者应先做出一项保持完整语义、超出配置且跨独立负载族稳定有效的改进，再冻结性能奖励端点。I/O、JIT、CPU架构和精度/耐久合同都需保持可比。

## 当前需要重设范围的13项

**Sphinx、Hatch、Fastify、dbt、fd、petgraph，以及Mosquitto、BMv2、Avro、NATS、GraphQL.js、CEL-Go、FlatBuffers。**

前6项当前范围较容易缩成事件插件、依赖工件归集、并发控制、归档、遍历适配或局部容器不变量。后7项的系统语义可以很深，但当前库存没有给出足够具体的starter、真实宿主和产物边界，使这些语义确实成为求解者工作。通用服务/CLI若只是成熟库的接口复述，难度通常没有来源代码看起来那么大。

不能因为存在完整上游工具就否定素材；同样也不能直接把上游全部实现量算到求解者身上。可以保留真实宿主对象、事务存储、解析执行或新语言后端等方向，但约束要来自用户产物需求，先给可起步参考，再试普通依赖。不要临时引入语言禁令或私有ABI只为挡简单解法。逐项具体重开方向已保存在JSON。

## 从潜力进入高难题的最小验证顺序

```mermaid
flowchart LR
    A[明确完整交付与starter剩余工作] --> B[强正常基线尝试]
    B --> C[健康参考与独立判据]
    C --> D[证明初步可用后仍有自然里程碑]
    D --> E[冻结范围和阶段反馈]
    E --> F[真实求解轨迹校准难度]
```

建议先用Helix、Jinja、Alembic、Task、yq、Miller做六个低成本范围探针，再投入Pydantic Core和Tantivy。它们代表编辑状态、模板执行、数据库演进、缓存产品、树更新和记录流，能较快淘汰当前设计中的简单路径。性能方向并行安排的是作者基线测量，不直接发布优化题。

恢复题另有一项共同前提：不能让健康同版wheel/完整二进制、旧生成缓存或原版参考源码成为直接回填通道。公开源码重用、近重复记忆和普通替代库分别检查；允许正常依赖，不以禁止依赖替代题目设计。随机删除更多函数也不能证明长程，必须说明关联缺口的用户语义与阶段成果。

最终长程校准要记录同一冻结快照的能力组表现、失败原因和实际改进轨迹。“一开始很难”和“更多交互仍能改善”分别检验，不把长预算或环境等待当作长程工作。

## 证据与复核范围

本次覆盖全部50项，每项重读至少一处实现和一处原生测试/规格；libjxl选读的是官方effort规格，尚未复核其原生正确性测试。各组记录实际行范围，没有宣称达到全仓架构审计覆盖率。根分析额外抽查Alembic重命名边界、Task指纹与执行生命周期、SQLFluff模板空渲染修复、Cap’n Proto旧handle升级、Flecs observer重入、yq children-first/alias、Jinja super与关闭、Helix选择区/分支历史，以及Tantivy显式reload/失败提交。

抽查也纠正了一个证据边界：Miller名为mixed-format的0001 fixture实际是两个JSON输入，不能据目录名声称已运行CSV+JSON跨格式互通。跨格式仍是待验证的拟题交付。Thrift当前选读测试只支持词法/字符串常量AST，不证明跨include/service的完整回归已闭合。

本次没有构造新题、运行健康参考/强基线或执行模型求解。全部分档均可被下一步探针推翻，六小时或同等难度尚未验证。原始素材登记及其初筛优先级未修改，复评结果单独保存。

细节与实际阅读范围见[drafts/product-cli.md](drafts/product-cli.md)、[drafts/system-state.md](drafts/system-state.md)、[drafts/restoration.md](drafts/restoration.md)、[drafts/performance.md](drafts/performance.md)；根抽查行范围见[root-cross-checks.json](drafts/root-cross-checks.json)。[在线官方交叉核对](official-cross-checks.json)只补充强基线背景，逐项设计结论绑定材料commit。

运行本目录compile_assessment.py可以复核50项集合、字段、证据/阅读行位置和本地链接；该检查不等于语义或难度验收。
