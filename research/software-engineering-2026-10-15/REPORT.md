# EdgeBench 软件工程任务：素材、机制与造题路线

**建议先做“真实仓库的跨模块功能演进”，同时保留一条“正确性约束的性能优化”路线。** 三个参考 factory 可以复用出题闭环，但需要新增连续评分、任务语义去重和长时校准。源码规模、需求数量、Oracle=1 和六小时超时设置都不能单独证明题目有六小时价值。

本轮完成的是原题研究、现有小样审查、四个候选来源固定和构造设计；不是新的完整任务交付。原始参考仓库保持只读，未启动新的教师运行；此前科学和金融运行不属于本报告的实验。

## 1. 先确定原题在测什么

固定官方 harness `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`，论文 `2607.05155v1`，HF 定义 `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`。全部 **36 道**软工题都读到论文逐题设计说明；其中 **12 道**有公开任务 JSON，1 道还取得实际镜像层 TODO。其余细节仍未知，不能把论文的一段简介当完整题面。[原题逐项证据](original-software-tasks.md) / [36 题映射 CSV](software-task-map.csv) / [官方论文附录](https://arxiv.org/html/2607.05155v1#A7.T7)。

以下五种改造机制是本次人工归纳，不是官方子类：

| 机制 | 全部 / 公开 | 原题锚点 | 新题的关键材料 |
|---|---:|---|---|
| 多目标工程演进 | 13 / 3 | Schemathesis、Litestar、PocketBase、Zstd | 冻结仓库、关联需求、兼容性合同、跨功能测试 |
| 从规格构建系统能力 | 12 / 2 | Arc 编译器、类型检查器、协议系统、CPU | 完整语义/状态机、可执行参考、分层骨架与集成场景 |
| 正确性约束的性能优化 | 6 / 5 | ANN、exchange-core、整数压缩、VLIW | baseline、独立正确性 oracle、工作负载与计时规则 |
| 缺失或退化实现恢复 | 3 / 1 | Rust 多 crate、Codeflash、regex-automata | 完整参考版本、受控缺口、保留契约和跨模块回归 |
| 行为等价重实现/移植 | 2 / 1 | Git→Zig、libexpat→汇编 | CLI/ABI/持久状态合同、参考程序、差分输入与骨架 |

公开子集明显偏向性能题：它公开了 6 道性能题中的 5 道，而前两种机制共 25 道仅公开 5 道。不能从公开题比例反推完整 benchmark 分布，也不能把所有 SWE 都转成“删函数→补回来”。

Schemathesis datagen 的实际 TODO 有八个目标，涉及协议感知生成、hook 执行顺序、多 schema 参数化、discriminator 的生成与验证、重试和诊断等。交付物是框架改造，不是一批测试输入。Juliet 交付的是分析器；本次未找到明确仅以测试套件或 fuzz corpus 为最终交付物的原题。[实际 TODO](../comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md)

## 2. 什么证据才能说明“值得给六小时”

从固定 README 提取的 12 道公开软工题有 60 个任务—模型组合，59 个具有有效 2h/6h 公布值。其中 3 个组合的 2h 与 6h 四舍五入公布分相同，8 个组合的 4h 与 6h 相同；2→6h 增幅中位数是官方分数尺度上的 4.4 分。这只是公布汇总值的描述，不是独立样本显著性检验，也不是我们用 gpt-6.1-sol 跑出的曲线。[提取 CSV](official-software-time-scores.csv) / [汇总](official-software-time-score-summary.json) / [官方时间表](https://github.com/ByteDance-Seed/EdgeBench#leaderboard)

例如官方 GPT-5.5 的 Rust 重建从 27.5（2h）到 53.1（6h），Schemathesis datagen 从 54.6 到 56.7。原题内部也存在不同的改进节奏；不应要求每个十分钟窗口都涨分。模型、资源和评分不同，不能直接拿这些分数与我们的 RESTler 分数做能力比较。

应寻找能提供几条真实改进路径的任务：早期能做成一个有用部分，中期暴露跨模块交互问题，后期还能改善兼容性、边界行为或性能。把编译、安装、等待和同一搜索脚本持续运行单独记录。最终用固定合同下的真实提交判断“早满、持续改进、晚期突破、全程无进展”，不在本次研究中凭空新增最低增长阈值。

当前 RESTler 样例的专项审查见 [restler-audit.md](restler-audit.md)。其历史运行约 14 分钟达到当时评分满分，此后平台错误中断；早满和平台中断是两个不同问题。另对本地 `long-horizon-built-007` 的 grader 审计确认，它遍历指定代表用例，以注入 transport/clock 的函数 probe 为主，没有运行 RESTler 原生回归和完整端到端 campaign；该设计的满分证明范围比完整工程路线窄。启动脚本和历史失败项可以关联这份素材与运行，但尚无完整 hash 绑定，不能把本地每一处缺陷都归因到当时运行。首个满分快照的模型补丁本轮未取得，不能据此断言模型已完成全部生产改造或利用了某种绕过。这个样例可以支持运行机制研究，不能作为六小时难度已验证的新题。

## 3. 已经找到了哪些真实素材

本轮下载了以下固定 revision 的完整文件树清单，以及选读文档、许可证和部分测试/实现文件；没有完整 clone 或 build。每个来源都有 URL、commit 和逐文件 SHA-256。[机器清单](source-candidates.json)

| 来源 | 已固定版本 | 可以形成什么题 | 当前判断 |
|---|---|---|---|
| openapi-python-client | `0a283fe21eea` | 复杂 schema 从解析到生成客户端执行的一致性改造 | 第一优先；有真实关联 issue 和可执行端到端测试基础，尚未复现缺陷 |
| Apache DataFusion | `91cd7ffb927b` | 固定内存下的排序/Top-K 优化 | 第二条路线；已有正确性集、排序负载和计量材料，优化空间未测 |
| Apache Polaris | `f838a62e20e7` | 提供真实 API 资源、角色授权与生命周期序列 | 先作状态服务素材；尚不是一道定义完成的新题 |
| jq | `6b53f8031161` | 行为等价的 JSON 流处理工具重建 | 备选；规模裁剪与现成替代实现风险尚未解决 |

具体题目合同草案、已读文件、来源 URL、评分思路和退选条件见 [candidate-designs.md](candidate-designs.md)。

**第一优先的关键是改造生成器，而不是手写某个示例客户端。** 实际线索包括 [内联联合对象 #1428](https://github.com/openapi-generators/openapi-python-client/issues/1428)、[嵌套组合类型 #1328](https://github.com/openapi-generators/openapi-python-client/issues/1328)、[组合字段丢失 #1392](https://github.com/openapi-generators/openapi-python-client/issues/1392)。作者需要追踪 schema 图→内部类型→模板/模块→序列化→端点调用，设计一个共享语义的需求包。单个 issue 可能只是小修复，不能靠把几个标题合并便宣布是难题。

这里的真值不能只是作者或 issue 报告者的期望。例如 [OAS 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) 基于 JSON Schema 2020-12；`default` 在验证中不自动补值，SDK 如何使用它要在应用合同中明确。[JSON Schema 注解说明](https://json-schema.org/understanding-json-schema/reference/annotations) 同理，模糊或重叠的 union 不应随意用某个实现的选择当规范。

DataFusion 路线的关键则是先定位实际瓶颈，再选择一个完整子系统与固定 workload。官方已经有 [排序/Top-K benchmark](https://github.com/apache/datafusion/tree/91cd7ffb927b5a4f9fee1907db50a9610759de5b/benchmarks)，存在这些工具不等于还存在足够性能空间。结果错误、偷用预计算、只换不公平编译选项或噪声中的微小变化都不能算优化成功。

## 4. 三个 factory 应怎样组合

固定本地参考 `upstream/swe-factory` 的 `661d5b978a30e6d3517ad8232451353bb5e81ce1`；代码与历史实验状态分开核对，三个原始规范未修改。详见 [源码对照](factory-methods.md)。

| 工厂 | 最值得沿用 | 当前缺口 |
|---|---|---|
| DeepSWE | C 路线的新需求→失败测试→critic→参考解；A/B 的受控恢复与机制迁移 | 原生二元完成判断不能直接充当本任务书的连续主分 |
| ProgramBench | 真实 binary 构建、行为观察、差分输入、dummy/gold 对照和重建 QC | 构造 R1/R2 不是六小时解题 R3；还缺任务级连续 scorer |
| NL2Repo | 从实现/测试/fixture 提取行为规格，检验可见合同的充分性 | 自己的 reference 能回放不证明题面充分；文本计数评分不宜直接移植 |

作者需要真正操作仓库：读源码、理解行为、复现问题、实现新参考分支、执行并诊断跨模块失败。这些适合具备文件/命令工具循环的 CLI agent。规则脚本负责固定来源、复制工作树、缓存依赖、生成已定义输入、回放和打包；普通 LLM 调用可做候选筛选或文案初稿，不能代替真实执行证据。

```mermaid
flowchart LR
    A[真实项目/规范/需求] --> B[脚本固定来源和版本]
    B --> C[作者理解机制并定义关联需求]
    C --> D[作者构造 starter/reference/行为测试]
    D --> E[独立验题与错误实现对照]
    E --> F[固定连续评分与 Harbor 双环境]
    F --> G[首条六小时轨迹校准]
    G --> H[通过后补轨迹并按题族扩量]
```

**可以合需求，也值得让 CLI 作者来合。** 合理的产品 roadmap 可以包含相对独立的目标，不要求任意两项都互相依赖。作者的实际工作是把目标放进同一冻结版本，处理接口、兼容与实现冲突，交付完整参考分支和可分阶段验收的行为。共享抽象和交互是增加设计深度的一种来源；自然的工程工作量也可以构成长程任务，但两者都要通过轨迹确认，不能用 issue 数量代替证据。“批量”应该发生在语义模板和验题合同稳定之后。参数生成器增加的是 case，新的语义目标组合、材料分布、目标子系统或约束才可能形成新实例。

## 5. 任务包应该留下哪些东西

作者阶段至少留下来源清单、requirement_graph、明确题面、starter、reference、需求→行为组→测试 ID 映射、原生回归、部分/错误实现对照、评分公式与常量、资源和提交路径。随后适配 Harbor 的 task.toml，不能用原 factory 的另一种 YAML 格式代替。

正式评分遵循既有任务书：agent/verifier 分开、运行禁网、文件快照、无状态 verifier、总分/有效性/具名 checks、明确 bounded_continuous 主分、机器可读归一化与原始指标、运行全部提交 best-of-run。内部可以保留二元完成诊断；作者可另设质量审计保留集，两者都不能悄悄改变正式取分规则。

训练来源还应与原题记录源码谱系、目标实现、补丁、测试语义和工作负载重叠。换仓库能降低直接复用风险，但不能证明分布相同或训练有效。此次优先候选覆盖功能演进和性能机制；从规格构建系统能力等其他机制，本轮只完成原题来源路径研究，没有冒充已有同等成熟的新素材包。

建议接下来先对 openapi-python-client 做一个真正的作者构造闭环：复现候选→定合同→参考实现→独立行为测试→判定是否存在简单完成路径。若这些检查显示它只是几个小修复，就退选或换真实子系统。只有完成这个闭环，才值得用既定 gpt-6.1-sol 启动首条六小时校准；先一条符合要求再补另外两条。
