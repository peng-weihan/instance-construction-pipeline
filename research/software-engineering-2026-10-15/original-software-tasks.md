# EdgeBench 原始软工任务：机制分类与新实例来源

本次研究覆盖官方 **Systems & Software Engineering 全部 36 题，其中 12 题有公开 JSON 定义**。最有用的分类轴是“把软件从什么状态改造成什么状态”：多目标工程演进 13 题、从规格构建系统能力 12 题、正确性约束下性能优化 6 题、缺失或退化实现恢复 3 题、行为等价重实现与移植 2 题。这些是本次研究标签，官方并未发布这五个子类；逐题依据、未知项和构造建议见 [software-task-map.csv](software-task-map.csv)。原始清单与描述见[论文附录 G.4 / Table 7](https://arxiv.org/html/2607.05155v1#A7.T7)，本地对应 [paper HTML](/Users/raymone/Desktop/edgebench/research/sources/edgebench-paper.html:4966)。

## 证据范围

固定版本为 harness `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`、HF 定义 `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`，论文 `2607.05155v1`。本次没有运行模型、Docker、SSH，也没有验证任何原题或新实例的分数、耗时与学习曲线。

|证据层|覆盖|能支持的结论|仍缺什么|
|---|---:|---|---|
|论文逐题设计说明|36/36|交付能力范围，以及部分明确写出的评分指标|完整题面、精确 API、起始源码、判分细则|
|公开 task JSON|12/36|`submit_paths`、agent_query、work/judge 镜像引用、评分入口和部分 wrapper|镜像内部被引用的规格、实现、测试、参考解|
|实际镜像层题面|1/36|Schemathesis datagen 的 177 行 TODO，完整八目标与完成条件|没有还原完整 OCI 文件系统；未执行镜像，未读隐藏测试|
|本地历史对比记录|RESTler 样例 1 个|之前作者如何设计样例，以及与原题已识别的差距|没有运行验收，也不能证明训练收益或长时难度|

“公开”在这里专指这个固定 HF 快照有任务定义，不能读作完整题材和评测源码均已下载。README 也把“下载 task definitions”和“拉取预构建镜像”列为两步。[README:189](/Users/raymone/Desktop/edgebench/upstream/EdgeBench/README.md:189) 取得的 datagen TODO 来自 work 镜像 `b52953fc6612` 的 layer 8，SHA-256 `3cf8492eacc5b49379f239ea1bb11933dd88f7382bb5cf77f045a4256e06fb82` 已复核；抽取记录明确说明未应用 whiteout、未执行镜像。[抽取记录:5](/Users/raymone/Desktop/edgebench/research/comparison-2026-10-14/original_image_metadata/schemathesis_datagen_pipeline.extraction.json:5)

## 五种机制应产生五种构造流程

|主机制|总数/公开数|原生例子|构造器真正需要做的工作|
|---|---:|---|---|
|M1 多目标工程演进|13 / 3|Schemathesis、Copier、Litestar、PocketBase、Zstd|从冻结仓库和一组相互关联的新需求，构造完整参考分支、需求到判据矩阵、独立功能组与集成检查|
|M2 从规格构建系统能力|12 / 2|Arc、依赖类型检查器、Postgres-on-SQLite、QUIC、CPU|先写完可执行的语义/协议契约和参考系统，再制作骨架、分层正确性检查与端到端场景|
|M3 正确性约束下性能优化|6 / 5|ANN、exchange-core、swscale、整数/Notebook 压缩、VLIW|提供可运行 baseline，构造独立正确性 oracle、代表性 workload、资源/计时规则与连续性能分数|
|M4 缺失或退化实现恢复|3 / 1|Rust multicrate、Codeflash、regex-automata|从验证过的完整实现出发，选择关联的缺失/退化点，保留可观察契约并检验跨模块恢复|
|M5 行为等价重实现与移植|2 / 1|Git→Zig、libexpat→x86-64 汇编|冻结参考行为和实现限制，提供脚手架，构造 CLI/ABI 差分调用、错误路径与状态检查|

M1 与 M2 的边界是改造已有产品的一组能力，还是按规格建出一项系统能力。Arc 的 JSON 虽然也写“missing modules”，论文明确描述为新语言编译器流水线，因此归 M2；Rust CAS 明确是既有多 crate 契约的实现重建，归 M4。[Arc JSON:24](/Users/raymone/Desktop/edgebench/data/EdgeBench/arc_compiler_runtime.json:24) [Rust JSON:25](/Users/raymone/Desktop/edgebench/data/EdgeBench/rust_multicrate_reconstruction.json:25)

名称不能决定分类。swscale 题名是 reimplementation，但论文说明提供正确性通过的 scaffold，JSON 末尾也把当前优先级写为性能改进，因此归 M3，并保留移植属性。JSON 前段仍有 26/30 的旧指示，末段称当前 30/30；这里记录文本冲突，不把后者当成本次运行结果。[swscale JSON:21](/Users/raymone/Desktop/edgebench/data/EdgeBench/ffmpeg_swscale_reimplementation.json:21) 同理，`high_performance_object_mapper` 的论文段落没有给性能评分公式，`zstd_api_modernization` 描述的是五项 API 演进，不能仅凭名称或压缩领域把它们算成性能题。[论文:5057](/Users/raymone/Desktop/edgebench/research/sources/edgebench-paper.html:5057) [论文:5273](/Users/raymone/Desktop/edgebench/research/sources/edgebench-paper.html:5273)

产物子族作为第二轴保留：编译器/语言工具、协议状态机、测试与模糊测试框架、静态分析器、压缩编码、并发引擎、硬件集成等。这样能分别回答“需要哪种构造流程”和“需要哪些领域材料”。例如压缩领域同时有 M1 的 Zstd API 演进、M2 的 cfzip 完整引擎、M3 的整数与 Notebook 压缩；直接按领域选择同一种删函数模板会丢失这些差异。[论文 Table 7](https://arxiv.org/html/2607.05155v1#A7.T7)

公开子集也不能代表完整分布：M3 有 **5/6** 公开，M1 为 **3/13**，M2 为 **2/12**；Postgres、QUIC、TLS 三个协议子族均只有论文说明。本报告对 24 个未公开任务只给“论文明确写出的交付能力”，具体提交路径与未公开公式均标为未知。

## 测试生成与模糊测试：要先分清最终交付物

实际 datagen TODO 的产品是 property-based HTTP API 测试框架；需要 agent 改进的生产功能是协议感知的生成与验证。它不是让 agent 交出一批 OpenAPI 测试用例，也不是按发现漏洞数评分的 fuzz campaign。[TODO:5](/Users/raymone/Desktop/edgebench/research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md:5)

八个目标包括：结构化 header 生成；coverage 中应用 hooks；多 schema pytest 参数化；discriminator 响应验证；discriminator 请求生成；503 重试；全部不同的 schema 错误；regex AST 量词转换。隐藏评分入口会报告 phase 结果和加权分数，但实际 `/tests/test.sh` 与权重没有下载。[TODO:19](/Users/raymone/Desktop/edgebench/research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md:19) [JSON:28](/Users/raymone/Desktop/edgebench/data/EdgeBench/schemathesis_datagen_pipeline.json:28)

其中有真正需要跨功能推理的条件：header 正模式只生成合法语法，负模式混合合法、近合法和随机值；coverage hook 依 global→schema→per-test 顺序，先 filter 再 map；discriminator 生成与验证需要在 explicit mapping、implicit `$ref` 和 bundled ref 上保持语义一致。[TODO:36](/Users/raymone/Desktop/edgebench/research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md:36) [TODO:64](/Users/raymone/Desktop/edgebench/research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md:64) [TODO:96](/Users/raymone/Desktop/edgebench/research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md:96)

因此复用 RESTler 等测试工具作材料时，CLI 构造 agent 应完成一条新的功能路线：协议/配置解析 → 状态与依赖生成 → 异步执行/恢复 → 报告与诊断，并实现私有参考分支和跨功能 judge。原有 `restler_resource_lifecycle` 样例删了 3 个文件中的 9 个函数，属于恢复机制；历史对比已经指出，9 个函数不能替代原题 8 个 roadmap 目标，24 条计划检查也不是可执行 verifier。[comparison.json:22](/Users/raymone/Desktop/edgebench/research/comparison-2026-10-14/comparison.json:22)

另两道 Schemathesis 题的五/六目标范围来自论文，公开 JSON 只要求读镜像内 TODO，本地没有其实际 TODO。Juliet 则要求交 `analyzer.py`，对结构化程序 facts 报告六类 CWE；它是静态分析器构建，不能改写成“修漏洞”或“交 fuzz corpus”。[reporting JSON:24](/Users/raymone/Desktop/edgebench/data/EdgeBench/schemathesis_reporting_observability.json:24) [config JSON:24](/Users/raymone/Desktop/edgebench/data/EdgeBench/schemathesis_config_modernization.json:24) [Juliet JSON:22](/Users/raymone/Desktop/edgebench/data/EdgeBench/juliet_vulnerability_analyzer.json:22)

通读 36 条设计说明和 12 个公开定义后，未识别出明确以“仅提交测试套件或 fuzz corpus”为最终交付物的原题。这个方向可以另立新子族，但需要独立定义有效性、覆盖/缺陷发现目标、参考 agent 和难度校准，不能直接宣称已复现上述原题分布。

## 适合批量构造的具体变化

以下均为设计建议，不是已经生成或验收的实例。每个新实例至少应固定任务契约、起始材料、参考实现、judge 与反馈，才能区分它和单个评测 case。

|锚点|可形成新任务实例的变化|只是 case 的变化|CLI 构造器须交付|
|---|---|---|---|
|Schemathesis / M1|在另一冻结框架上设计协议、生命周期、诊断相互关联的新能力组合|更换一条 header 或一个 schema 的名字|新 TODO、完整参考分支、功能依赖图、分组判据和跨组测试；验证兼容性|
|Arc / M2|原创语言的类型规则、模块系统或运行时能力及配套骨架|同一语法生成更多表达式/变量名|可执行语义、参考解释器、源码骨架、语法/类型/运行时负例和端到端 judge|
|Postgres/TLS / M2|一个范围明确的协议子集或不同后端适配语义|同协议的一条新握手 trace|状态模型、reference、合法/非法会话生成器、状态推进/错误恢复/互操作测试；原题细节未公开，按原创规格构造|
|ANN / M3|更换检索材料的分布、距离/资源约束并重新校准 baseline 与评分|在已冻结查询集里换 seed 或重排 query|授权数据与精确近邻 oracle、baseline 插件、开发/隐藏负载、独立计时器；原题是 Recall@10≥0.95 后最大 QPS|
|VLIW / M3|新计算 kernel、ISA 资源模型或依赖结构，带可信模拟器与 baseline|只更换同一 kernel 的输入数组|reference 结果、指令模拟器、周期模型、朴素生成器和防特化的输入覆盖；文件少仍可能有深优化空间|
|Rust CAS / M4|另一完整多 crate 产品中跨层行为的受控缺失组合|重复删除同一函数、只换符号名|验证过的完整版本、可解释 ablation、公共契约、跨 crate 参考与集成测试|
|Git→Zig / M5|另一 CLI/ABI 工具的独立行为契约与实现语言限制|同命令的另一参数值/文件名|范围清单、只读 reference、构建骨架、输出/退出码/持久状态差分 judge|

ANN 的原题明确约束修改目录并使用独立计时与 ground truth；VLIW 的 wrapper 以 `all_correct` 和 `score_cycles` 为准，分数越低越好。[ANN JSON:15](/Users/raymone/Desktop/edgebench/data/EdgeBench/ann_vector_search_qps.json:15) [VLIW JSON:28](/Users/raymone/Desktop/edgebench/data/EdgeBench/vliw_kernel_optimization.json:28) 字典训练、图片尺寸或查询 seed 也可以成为参数，但“批量抽 case”本身不能证明生成了不同的任务难点；应记录语义变化、材料分布和参考解工作量。

## 对普通 issue repair 来源的判断

修复任务在原生分布中确实存在：Codeflash 是故意退化模块的修复，并同时考察性能；regex-automata 涉及 NFA、DFA、Unicode、capture 和 hybrid engine；Rust CAS 是跨 crate 重建。[论文:4994](/Users/raymone/Desktop/edgebench/research/sources/edgebench-paper.html:4994) [论文:5192](/Users/raymone/Desktop/edgebench/research/sources/edgebench-paper.html:5192) 因此可以从可授权仓库的真实问题、版本差异或可解释退化取得材料，但应按 M4 的契约筛选，不能因为题面是软件代码就默认所有题都由单个 issue/patch 生成。

一个普通 issue 是否适合扩展成 EdgeBench 式任务，需要检查：是否存在多步诊断或跨组件依赖；是否能形成分阶段可观察进展；正确性之外是否有需要继续优化的目标；测试是否覆盖新的行为契约；允许 agent 修改的范围是否足以完成任务。目标数量、文件数、LOC 和超时时间只能描述规模，不能证明长时间持续改进。原始 README 的设计是反复提交、获得细粒度反馈并取最佳提交；实例构造阶段应产出支撑这种闭环的判据，随后才用实际运行校准。[README:180](/Users/raymone/Desktop/edgebench/upstream/EdgeBench/README.md:180)

CSV 的 `new_task_source_proposal` 和 `cli_constructor_work_proposal` 逐题列出材料来源类型与作者工作，均标为 research proposal。没有声称已解决源码许可、与隐藏原题的重叠或难度校准；这些待实例作者拿到候选材料后逐项验证。

官方发布的 2/4/6 小时结果属于官方运行汇总；本研究没有产生同模型、同预算、同硬件的曲线。它们可说明官方设置下的进展，不能拿不同模型或不同协议的原始分数直接与新样例比较，也不能据此给未运行的新题盖上“长时已校准”的标签。[README 结果表说明:108](/Users/raymone/Desktop/edgebench/upstream/EdgeBench/README.md:108)

## 36 题清单

以下“交付物/评分”是论文与已读定义支持的范围；“仅论文”表示未看到该题实际题面或提交协议。所有精确路径、证据位置、未知项在 CSV，不能把这一列概述当作可直接执行的任务说明。

|任务 ID|公开定义|主机制|真正交付能力与评分目标|
|---|---|---|---|
|`ann_vector_search_qps`|JSON|M3|Custom ANN插件及config.yml；SIFT-1M上fit/query实现；Recall@10≥0.95后的最高QPS|
|`arc_compiler_runtime`|JSON|M2|新语言Arc的TypeScript编译器/运行时；lexer到codegen；隐藏脚本SCORE并返回原始/加权通过数|
|`rust_multicrate_reconstruction`|JSON|M4|跨crate CAS工作区缺失Rust实现；总分与layer/crate公共和隐藏测试反馈；权重由外部评分器决定|
|`codeflash_repair_performance`|仅论文|M4|修复Python代码优化工具中故意退化的CST、profiling、test-harness模块；论文明确功能正确性和运行性能；组合公式未知|
|`copier_modular_refactor`|仅论文|M1|Copier六目标：异常、模板、版本兼容、渲染、worker、用户数据；论文仅列功能目标；实际计分未知|
|`dependent_type_checker`|仅论文|M2|Rust依赖类型检查器：universes、Pi/Sigma、归纳类型正性、宇宙多态；论文明确正确性与normalization吞吐；公式未知|
|`entt_graph_module`|仅论文|M1|EnTT七目标；图邻接矩阵、task graph/transitive reduction、DOT和工具扩展；论文仅列功能目标；实际计分未知|
|`exchange_core_throughput`|JSON|M3|Java matching engine源码及Maven/JVM配置；功能断言通过且解析MT/s；raw=int(round(Average_MT_s*1000))|
|`ffmpeg_swscale_reimplementation`|JSON|M3|Rust源码编译libswscale_candidate.so；create/process/destroy接口；任一隐藏正确性失败得0；否则基线/候选耗时比的几何平均|
|`git_rewrite_in_zig`|JSON|M5|Zig源码生成git二进制；CLI输出/退出码/仓库状态等价；行为等价测试；wrapper调用外部test.sh，实际聚合未知|
|`high_performance_object_mapper`|仅论文|M2|.NET映射库；expression trees/IL，嵌套、集合、转换器、nullable、继承；论文未说明计分；名称high_performance不足以推出吞吐指标|
|`integer_compression_codec`|JSON|M3|C++源码构建libintcompress.so，保留ic_* ABI；uint32精确round-trip；改善压缩率和解码吞吐；组合式未公开|
|`juliet_vulnerability_analyzer`|JSON|M2|agent-start/analyzer.py：读取结构化facts，报告六类CWE；外部hidden_score给SCORE；不是wrapper中0/1 pass_rate；未见F1等精确式|
|`libexpat_x86_assembly`|仅论文|M5|全x86-64汇编的libexpat ABI兼容共享库；论文只说明ABI/解析兼容目标；实际计分未知|
|`odata_query_service`|仅论文|M2|.NET OData解析、LINQ过滤、排序分页投影和ASP.NET中间件；论文仅列功能范围；实际计分未知|
|`litestar_infra_refactor`|仅论文|M1|五个async基础设施：过期KV、event bus、WebSocket、DTO、channels；论文仅列功能目标；实际计分未知|
|`lua_native_compiler`|仅论文|M2|Lua5.4源码到真实x86-64 ELF的AOT编译器；输出与解释器逐字节一致；禁止C API序列/bytecode dispatch；计分未知|
|`mimesis_modular_refactor`|仅论文|M1|七目标：声明式schema、随机enum元类及五类data provider；论文仅列功能目标；实际计分未知|
|`nlohmann_json_modularization`|仅论文|M1|五目标：UBJSON、Merge Patch、Grisu2、range迭代、metadata macros；论文仅列功能目标；实际计分未知|
|`notebook_lossless_compression`|仅论文|M3|notebook字典训练和逐文件压缩/解压pipeline；字节级无损硬约束；总压缩率|
|`packer_plugin_datasources`|仅论文|M1|Packer Go插件生态六目标；地址、发现校验、HCL2、敏感值、模板函数；论文仅列功能目标；实际计分未知|
|`pocketbase_backend_architecture`|仅论文|M1|四目标：链式hook、带中间件router、OAuth2注册表、regex随机串；论文仅列功能目标；实际计分未知|
|`pocketbase_tools_extensions`|仅论文|M1|四个Go工具包：字段挑选JSON、zip、时区cron、SQL索引parser/builder；论文仅列功能目标；实际计分未知|
|`postgres_wire_on_sqlite`|仅论文|M2|SQLite后端的PostgreSQL v3协议服务器；论文明确PostgreSQL自身测试套件通过率|
|`quic_transport_stack`|仅论文|M2|RFC9000子集：连接、TLS1.3派生、AEAD、packet number/header protection和frames；论文仅列协议目标；实际计分未知|
|`regex_automata_repair`|仅论文|M4|恢复Rust regex-automata的NFA/DFA、Unicode、captures、hybrid实现；论文说明修复跨模块错误；实际计分未知|
|`schemathesis_datagen_pipeline`|JSON + 实际TODO|M1|增强框架生产代码：headers、coverage hooks、多schema pytest、双向discriminator、503retry、多错误、regex AST八目标；外部roadmap分阶段测试及加权score；具体phase权重未知|
|`schemathesis_reporting_observability`|JSON|M1|Schemathesis五目标：validation hook、VCR/HAR/JUnit/NDJSON报告、pytest、schema分支example生成；外部roadmap分阶段测试及加权score；具体phase权重未知|
|`schemathesis_config_modernization`|JSON|M1|Schemathesis六目标：TOML/autodiscovery、API重组、metrics、transport/response、checks注册；外部roadmap分阶段测试及加权score；具体phase权重未知|
|`stream_processing_engine`|仅论文|M2|Rust JSON流引擎：窗口聚合、过滤、投影、有状态算子；论文明确正确性、畸形输入稳健性与吞吐；组合式未知|
|`tls13_handshake_state_machine`|仅论文|M2|Python TLS1.3 handshake trace处理：状态转移、key schedule、消息验证；论文只列协议语义目标；实际计分未知|
|`vault_sdk_resilience`|仅论文|M1|Vault Go SDK五目标：模板、公平调度、token持久缓存、证书工具、API hooks；论文仅列功能目标；实际计分未知|
|`vliw_kernel_optimization`|JSON|M3|solution.py的KernelBuilder.build_kernel生成VLIW/SIMD指令；all_correct为有效性门槛；最小化score_cycles|
|`cpu_full_flow`|仅论文|M2|RISC-V ISA emulator、HAL、Verilog CPU、Verilator SoC集成；论文仅说明完整课程范围；实际评分阶段/指标未知|
|`zstd_api_modernization`|仅论文|M1|Zstandard五目标：struct/查询、参数化压缩、静态分配、字典、内存估算；论文仅列API演进目标；不能从压缩领域推断按压缩率评分|
|`cfzip_compression_engine`|仅论文|M2|C++17从头实现压缩引擎：archive、streaming CLI、字典训练/使用、integrity；论文明确压缩率、速度、内存、正确性；组合式未知|

## 核对记录

分析范围是任务契约与机制，不是 task 镜像内生产源码的实现审计。36 条论文设计说明全部读过；12 个公开 JSON 的 `submit_paths`、`work.agent_query`、`judge.eval_cmd` 全部核对；实际 datagen TODO 177/177 行、抽取记录 88/88 行均读过。对应核心任务记录覆盖 36/36；实际原始题面覆盖只能报 1/36，不能把前者称为后者。README 已读结果说明与 harness/材料获取相关段；历史 comparison 只使用软件记录第 22–70 行，其他类别不作本报告证据。

CSV 已用脚本检查：任务 ID 与全量 inventory 的软工子集完全一致、无重复；公开标记与固定数据目录中 JSON 是否存在一致；36 行证据引用均能定位到对应 Table 7 行；实际 TODO 的 SHA-256 与抽取记录一致。分类是人工判读，数量由 `csv.DictReader` 与 `Counter` 计算。可在仓库根目录复算：

```python
import csv
from collections import Counter
rows = list(csv.DictReader(open("research/software-engineering-2026-10-15/software-task-map.csv", encoding="utf-8-sig")))
assert len(rows) == len({r["task_id"] for r in rows}) == 36
assert sum(r["public_definition"] == "True" for r in rows) == 12
print(Counter(r["mechanism_primary"] for r in rows))
```
