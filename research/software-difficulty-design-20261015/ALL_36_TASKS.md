# EdgeBench 全部 36 道软工题：逐题难度与构题迁移

覆盖基准是 `research/software-engineering-2026-10-15/software-task-map.csv` 的全部 36 个 task_id。完整读该 CSV 与论文的全部 36 道软工设计说明（`research/sources/edgebench-paper.html:4950–5292`）；12 道另读完整公开 JSON 题面、评分包装器及元数据；Schemathesis datagen 另读选定镜像层完整 TODO。其余 24 道只有论文概述。**这是全题目材料覆盖，不是全题目源码深审、隐藏测试审计或难度实测。**

证据类型：E1＝实际 TODO（选定镜像层，非完整 OCI）；E2＝公开 JSON 题面/包装器；E3＝论文设计概述；E4＝本地研究索引。E2 不代表读过外部 hidden judge；E3 不能确认具体 API、起始缺口和评分组合。

所有“难点”和“扩展点”均为基于已知交付的**设计推断/建议**，不是原题隐藏要求。扩展按新题真实用户目标选择，不应机械地把三项全部叠加。廉价路径是应检查的可能性，未运行证明这些路径成立。以下路径均相对仓库根目录；逐题表绑定本地材料，官方仓库和论文的在线复核见主报告。

P＝`research/sources/edgebench-paper.html`；M＝`research/software-engineering-2026-10-15/software-task-map.csv`；J＝`data/EdgeBench/<task_id>.json`。J 的第一个行号是题面，第二个是评分包装器。M 各行同时列出该题未知项。

| # / task_id | 已知交付范围 | 结构性难点（设计推断） | 可迁移扩展点（2–3 项设计建议） | 廉价路径 / 不确定性 | 证据类型及行号 |
|---|---|---|---|---|---|
| 01 `ann_vector_search_qps` | ANN 插件与配置；SIFT-1M 上 Recall@10≥0.95 后最大化 QPS | 索引、候选路由、扫描量、线程之间存在召回/吞吐折中，需测量后修订策略 | 用真实分布差异驱动索引适应；开放索引布局与精排；给召回 oracle 和瓶颈 profile | 合法 FAISS/HNSW 配置可能低成本高分；题面明确允许 FAISS，不宜以禁库补难度。实际计时/隐藏查询未知 | E2+E3+E4；P:4974；M:2；J:15,19 |
| 02 `arc_compiler_runtime` | TypeScript 实现新语言编译器与 runtime；lexer→parser→type checker→codegen | 阶段表示和语义约束依赖，局部通过不保证组合程序正确 | 原创语义的函数/作用域/复合值组合；良构执行与错误诊断共用表示；独立解释器和程序生成器检查端到端 | 若只有浅例子可模板拼接；语言规格、smoke、隐藏权重未得，不能从名称推出完整语言深度 | E2+E3+E4；P:4983；M:3；J:24,28 |
| 03 `rust_multicrate_reconstruction` | 恢复多 crate 内容寻址存储实现；公开类型/API 契约；layer/crate 反馈 | 底层表示与上层组合/CLI 的约定需一致；修好下层才能暴露上层问题，但实际依赖图未知 | 选择自然行为层恢复；用写入→引用→读取→重开的真实纵向流程；分层反馈加跨 crate 集成 | 随机删独立函数可能机械填空；无规格会变猜测。crate 清单、删改范围及实际存储语义未得 | E2+E3+E4；P:4992；M:4；J:25,29 |
| 04 `codeflash_repair_performance` | 修复 Python 优化工具中 CST、profiling、test harness 退化；功能与性能评分 | 被改写程序、测量器和验证器各有正确性边界；慢因可能跨模块传播 | 围绕候选改写→测量→验证/回滚构造因果退化；行为 oracle 配可信 profile；真实 fixtures/参数化测试集成 | 几处明显 panic/TODO 可能很快修完；关验证提速不能完成产品目标。具体退化、基线、计分未知 | E3+E4；P:5001；M:5 |
| 05 `copier_modular_refactor` | 六目标：异常、模板、版本兼容、渲染、worker、用户数据 | 一次脚手架库发行的工作宽度；生命周期、配置与渲染错误可形成深度，不必六项全耦合 | 用创建后升级模板旅程牵引兼容；统一 worker/渲染的数据和错误契约；已有项目 fixtures 回归 | 可能六个独立小功能；不能编造 merge 冲突或交互细节。完整目标、起点和权重未知 | E3+E4；P:5010；M:6 |
| 06 `dependent_type_checker` | Rust checker；累积 universes、Pi/Sigma、一般归纳类型正性、宇宙多态；正确性+normalization 吞吐 | 替换/归约影响类型等价和宇宙约束；正确 cache/归约策略与吞吐互相限制 | 明确小型理论语义并组合类型；良构/病态 term 生成器；正确解释式起点下优化归约/cache | 浅层例子可模式匹配；不公开规则会变猜 evaluator。语法、归约策略、负载和公式未知 | E3+E4；P:5019；M:7 |
| 07 `entt_graph_module` | EnTT 七目标；邻接矩阵、task graph、传递约简、DOT、工具扩展 | 图表示、约简和导出共享顶点/边语义，还需接入既有 C++ API | 用真实任务依赖的构建→修改→约简→可视化流程；与既有容器/迭代接口组合；图不变量和成本诊断 | 小 DAG 可标准算法快速完成；不能把 task graph 自动扩成执行调度器。七目标完整清单/API 未知 | E3+E4；P:5028；M:8 |
| 08 `exchange_core_throughput` | Java 撮合引擎/JVM 配置；正确断言通过后最大化 MT/s | 拓扑、batching、orderbook、分配互相影响；并行优化受交易语义约束 | 用实际访问结构不同的交易负载；提供队列/分配 profile；固定资源重复测量，允许深入布局优化 | 题面已有改线程数的大收益示例；先试正常配置基线。ringBuffer 被测试固定；实际计时控制未知 | E2+E3+E4；P:5037；M:9；J:20,24 |
| 09 `ffmpeg_swscale_reimplementation` | 固定 C ABI 的格式转换/缩放库；正确 scaffold 下性能优化 | 格式/抽样/stride/定点舍入/边界系数约束 SIMD 与内存优化，改共享 helper 易回归 | 正确但慢的另一图像算子 ABI 起点；真实格式/layout 组合；独立兼容 oracle 加热点向量化/内存诊断 | 旧段 26/30 与末段 Current Scaffold 30/30 并存；末段/论文指向性能任务，实际镜像未核验，不能当从零修四错 | E2+E3+E4；P:5046；M:10；J:21,25 |
| 10 `git_rewrite_in_zig` | 可替代 git 的 Zig 二进制；输出、退出码、仓库状态等价 | 多命令共享持久状态；前一步写出的格式要被后续正确消费，兼容覆盖可能很宽 | 冻结另一 CLI 的支持范围；创建→修改→查询→重开旅程；reference 差分输出与持久副作用 | 独立输出测试可能允许硬拼 CLI；无限全 Git 目标可能只有低分平台。隐藏命令/格式覆盖与公式未知 | E2+E3+E4；P:5055；M:11；J:24,28 |
| 11 `high_performance_object_mapper` | .NET expression trees/IL mapper；嵌套、集合、转换器、nullable、继承 | 多种类型规则在同一对象图组合；映射计划的生成、复用与运行边界可能很深 | 真实 DTO↔领域模型旅程；嵌套集合+继承+转换器组合；若确需性能则分首次编译与复用吞吐 | 平面拷贝可轻量 reflection；名称不证明按性能打分，循环/引用保留也未提。完整 API 与指标未知 | E3+E4；P:5064；M:12 |
| 12 `integer_compression_codec` | 保持 ic_* ABI 的 uint32 codec；精确 round-trip，提升压缩率/解码吞吐 | block/mode/delta/位宽/SIMD 存在大小与速度折中，编码端选择约束解码端 | 真实顺序/重复/稀疏分布驱动自适应；开放块布局与 decode pipeline；分别反馈大小、热点与极值正确性 | 单一成熟 codec 或少量阈值可能已高分；先测合法基线。scoring_scheme.md 和两指标权重未得 | E2+E3+E4；P:5073；M:13；J:23,27 |
| 13 `juliet_vulnerability_analyzer` | 从结构化 program facts 报六类 CWE 的确定性 analyzer | 若 schema 有真实流信息，多步传播/生命周期可形成深度；目前不能确认这一前提 | 公开原创 facts/分析语义；真实跨语句/调用结构驱动分析；误报、漏报和诊断反馈 | 若 facts 已近似给标签可规则匹配；须读 schema 才知难度。不是修漏洞；wrapper 的 0/1 pass_rate 非完整评分 | E2+E3+E4；P:5082；M:14；J:22,26 |
| 14 `libexpat_x86_assembly` | 全 x86-64 汇编的 ABI 兼容 XML 解析共享库；仅 assembler/linker/libc | 解析状态与回调/错误语义加上调用约定、指针/资源管理；实际 API 子集决定深度 | 明确小解析库的 ABI；reference 差分分段输入/回调序列；调用侧 ABI 和内存生命周期检查 | 纯汇编是原题目标，不能普遍靠禁 C 加难；少量字面语料可特判。API/计分/平台细节未知 | E3+E4；P:5091；M:15 |
| 15 `odata_query_service` | OData 解析、LINQ 过滤、多字段排序、分页、投影、ASP.NET 中间件 | 解析→类型/表达式→执行→HTTP 完整链；操作顺序和类型在组合时暴露问题 | 冻结协议子集及类型规则；同一请求组合过滤/排序/分页/嵌套投影；独立解释器核验结果和错误响应 | 简单字符串拆分+LINQ 或已给 helper 可快速完成；版本、运算符、null/排序规则及 judge 未知 | E3+E4；P:5100；M:16 |
| 16 `litestar_infra_refactor` | async 五子系统：过期 KV、event bus、WebSocket、DTO、channels | 各有生命周期；取消/关闭、数据适配与订阅一致性可能形成集成深度，非已知原要求 | 真实异步应用旅程；明确到期/取消/关闭语义配可控时钟；与旧插件及 sync/async 调用组合 | 进程内 queue 可能已够；不可默认 backpressure、durability 或竞态范围。完整目标与并发契约未知 | E3+E4；P:5109；M:17 |
| 17 `lua_native_compiler` | Lua5.4 源码→真实 x86-64 ELF；逐字节匹配解释器，非 C API 序列/bytecode dispatch | 语言语义、调用约定与机器码生成协同；支持语义范围决定长期工作 | 明确另一语言语义子集和系统 ABI；自然调用/复合数据组合贯穿前后端；reference+生成程序检查独立执行产物 | 表达式/print 子集即使发机器码也可能很短；不能把完整 Lua 当已测。scaffold/子集/权重未知 | E3+E4；P:5118；M:18 |
| 18 `mimesis_modular_refactor` | 声明式 schema、随机 enum 元类与五类 provider，共七目标 | 发行工作宽度；schema 组合/随机实例/provider 格式可能形成共享语义，不由 provider 数量自动推出 | 真实合成数据表驱动嵌套 schema；公开种子/实例隔离契约；有产品依据时增加跨字段依赖 | 独立格式生成器或常量列表可能机械完成；原概述未要求分布真实性、可复现或字段关联。细则未知 | E3+E4；P:5127；M:19 |
| 19 `nlohmann_json_modularization` | UBJSON、Merge Patch、Grisu2、range iteration、metadata 五目标 | 格式/数值语义深度与公共 C++ 编译兼容并存；不必五项全耦合 | 真实 parse→patch→iterate→serialize 旅程；数值/格式 reference；现有调用方编译 fixtures 验证 API | metadata 可能很简单，成熟 helper 也可使连接 API 变短；不能按五目标一律判断深。起点/配置/权重未知 | E3+E4；P:5136；M:20 |
| 20 `notebook_lossless_compression` | 可见语料训练字典+逐文件压缩/解压；字节无损，按总压缩率 | 训练产物与解码契约相连，压缩收益要跨文档泛化；结构语义不允许丢原字节 | 另一结构化文档域配 train/eval 划分；实际重复结构驱动编码；字典/大小归因反馈和独立无损 oracle | 标准压缩器+字典可能已接近天花板；JSON parse 后重写非字节无损。接口/预算/资源/公式未知 | E3+E4；P:5145；M:21 |
| 21 `packer_plugin_datasources` | Packer Go 插件六目标；地址/DNS、发现/checksum、HCL2、敏感值、模板函数 | 配置→插件身份/发现→调用跨边界，值元数据与错误归属可在边界丢失 | 离线真实插件调用旅程；敏感标记贯穿表达式与输出；旧插件兼容 fixtures 和调用 trace | 摘要不足以恢复完整六项拆分；不能编造版本/签名/网络下载要求。固定单插件可能低成本完成 | E3+E4；P:5154；M:22 |
| 22 `pocketbase_backend_architecture` | hooks 链、middleware router、动态 OAuth2 registry、regex 随机串四目标 | 扩展顺序、注册生命周期与 request context 可形成深点；四模块不一定全耦合 | 认证/请求旅程牵引顺序与中止；registry 更新和旧 provider 兼容；明确 regex 子集配属性 oracle | registry map+接口包装可能很快；不能从 OAuth2 推出完整协议交互。regex 范围、TODO/评分未知 | E3+E4；P:5163；M:23 |
| 23 `pocketbase_tools_extensions` | 嵌套字段 JSON、zip、时区 cron、SQL index parser/builder 四包 | 主要可能是交付宽度；各自递归结构、时间语义、语法往返带来深度，无需强造共同依赖 | 共同后端运维版本目标；按真实时间/SQL 方言定义 reference；导出归档/迁移旅程检查工具使用 | zip 可正常用标准库，不应禁库补难；DST、SQL dialect、路径规则均未知，可能是四个短任务组合 | E3+E4；P:5172；M:24 |
| 24 `postgres_wire_on_sqlite` | PostgreSQL v3 server/SQLite backend；认证、simple/extended queries、类型、事务、catalog；PG tests 通过率 | 协议状态与后端存储语义不完全同构，元数据和结果都要被真实客户端接受 | 明确协议/存储映射矩阵；真实客户端 prepare/bind/execute 与错误后继续；跨会话/事务旅程 | 完整协议库可能合法覆盖很多工作，须测组合基线；认证、PG 版本/子集、actual judge 未知，不能承诺完整兼容 | E3+E4；P:5181；M:25 |
| 25 `quic_transport_stack` | RFC9000 子集：连接、TLS 派生、AEAD、packet number/header protection、frames | 字节格式、密码状态与连接推进相连，早期错误可能在后续解密暴露 | 独立包级 reference+公开 crypto vectors；合法/非法 traces 和中间值；仅按产品目标加入网络恢复 | 不可默认真实 UDP、重传/拥塞控制/完整 QUIC；固定 packet parsing 可能不深。范围/crypto API/评分未知 | E3+E4；P:5190；M:26 |
| 26 `regex_automata_repair` | Rust regex-automata NFA/DFA、Unicode、captures、hybrid engine 修复 | 同一 regex 语义在不同执行表示保持一致，一处修复可影响另一 engine 或捕获位置 | 固定正确版本构造因果退化；多 engine 同输入差分；真实 Unicode/搜索组合配最小反例 | 少数明确 TODO/panic 可能很快恢复；删太深且无规格可能只是重造。原退化类型/数量/测试未知 | E3+E4；P:5199；M:27 |
| 27 `schemathesis_datagen_pipeline` | 八目标含 headers、coverage hooks、多 schema pytest、双向 discriminator、503、多错、regex AST | 实际 TODO 有 bundled ref 身份恢复、请求/响应分工、作用域顺序/函数复用隔离；也明确有独立改进 | 另一 API 工具的完整版本 roadmap；协议元数据贯穿生成/校验；扩展点跨阶段/作用域一致且旧 API 可用 | 不强称八项全耦合；503 可是小修。仅选定层 TODO，非最终源码/hidden。官方有低分平台，不证明始终进步 | E1+E2+E3+E4；P:5208；M:28；J:24,28；T:19–26,56–120,170–177 |
| 28 `schemathesis_reporting_observability` | post-validation hook、多格式 VCR/HAR/JUnit/NDJSON、pytest、branch-aware examples 五目标 | 一次运行被多个输出/插件消费，各消费者对事件/失败语义及生命周期需一致 | 统一运行事件语义+多消费者；hook/失败/examples 在插件中联动；产品需流式时明确关闭/中途失败语义 | 实际 TODO 未得；不能声称原题有 streaming、取消或 crash 安全。若只序列化整理好字典，主要是格式宽度 | E2+E3+E4；P:5217；M:29；J:24,28 |
| 29 `schemathesis_config_modernization` | TOML/autodiscovery、namespace、metrics、transport/response、checks 六目标 | 配置和扩展边界迁移；解析后要跨公共 API/插件生效，旧入口兼容可增加回归深度 | 真实配置迁移旅程及来源优先级；自定义 transport/response/checks 联用；旧调用方 fixtures 与迁移诊断 | alias+TOML load 可能很快完成；实际层级/namespace/兼容承诺未知，不补写原版精确规则 | E2+E3+E4；P:5226；M:30；J:24,28 |
| 30 `stream_processing_engine` | Rust JSON streams；窗口聚合、filter、projection、有状态算子；正确性/畸形输入/吞吐 | 共享事件模型，解析、状态更新与执行布局受三个目标约束 | 原创 DSL 和明确窗口语义配解释器；真实过滤/分组/窗口/投影流水线；profile+畸形输入后可继续状态 | 可能仅 batch group-by；不能默认 event time、watermarks、乱序、持久化。时间/接口/资源/公式未知 | E3+E4；P:5235；M:31 |
| 31 `tls13_handshake_state_machine` | Python 处理 handshake traces；状态、key schedule、消息验证；提供 crypto API | 顺序、transcript 与派生值相连，前一步错在后续才显现 | 明确协议子集与 crypto API；合法/非法 traces 检查中间值和状态；由实际协议需要引入可选分支 | trace checker 不是网络 TLS 栈；中间值若已全给可能轻。resumption/0-RTT/扩展等范围未知 | E3+E4；P:5244；M:32 |
| 32 `vault_sdk_resilience` | 模板、公平调度、持久 token cache、证书工具、API hooks 五目标 | 调度资源、跨进程状态和 request lifecycle 各具深度，五项不必互依赖 | token 获取/复用/API 旅程；明确公平/取消/关闭语义配可控任务；证书/模板进入旧 SDK 调用兼容 | 文件 cache+queue 包装可能足够；公平定义、原子/崩溃恢复、证书细则均未知，不宣称原题已要求 | E3+E4；P:5253；M:33 |
| 33 `vliw_kernel_optimization` | 仅 solution.py 的 kernel generator；全正确后最小化模拟 cycles | 单文件生成器仍可能有指令依赖、向量化和资源调度深度；难在生成程序而非 LOC | 独立 ISA/资源模型+真实 kernel；正确朴素生成器与 simulator；开放布局/访存/调度结构优化并给瓶颈反馈 | 一套标准调度模板可能饱和；实际 ISA/资源/hidden 负载未知，不能编具体 hazard | E2+E3+E4；P:5262；M:34；J:24,28 |
| 34 `cpu_full_flow` | RISC-V emulator、HAL、Verilog CPU、Verilator SoC 全课程 | 跨软件模型/硬件实现/整机接口的自然依赖链，可把语义偏差推迟到系统集成显现 | 明确 ISA/外设子集，同一软件贯穿四层；各层 reference+architectural state；整机程序驱动集成 | 可能大量已给代码或无反馈规模过大；课程章节数非难度。不能默认完整 ISA、流水线/cache。实际阶段/起点/评分未知 | E3+E4；P:5271；M:35 |
| 35 `zstd_api_modernization` | stable struct/query、参数接口、静态分配、字典、memory estimate 五目标 | 公共 ABI、配置解释和资源所有权约束；不同上下文创建/配置方式需一致 | 真实受限内存使用旅程；参数/字典/estimate 协同；旧调用方 ABI/错误/生命周期验证 | 可能仅暴露成熟内部函数；压缩领域不代表按压缩率/性能计分。ABI 承诺、细则、初始实现未知 | E3+E4；P:5280；M:36 |
| 36 `cfzip_compression_engine` | C++17 从头压缩产品；archive、stream CLI、字典 train/use、integrity；大小/速度/内存/正确性 | 格式、训练产物和解码端协同，多指标限制编码架构，stream/integrity 是交付生命周期 | 原创有边界 archive 配独立 reader/writer；真实 stream/dictionary/integrity 契约；授权语料/资源预算与归因反馈 | 原题明确 no external libraries，但不应普遍复制禁库；格式、基线、预算、组合公式未知，需测合法正常基线 | E3+E4；P:5289；M:37 |

T＝`research/comparison-2026-10-14/original_image_metadata/author_only/schemathesis_datagen_pipeline/layer_8/app/TODO.md`。上述 T 全文 177 行已读；P 的每个行号均为该任务完整设计说明段。M 全文已读，保留每题未知项；12 个 J 已读完整题面及评分字段，未读外部评分器。

## 主类计数与全部 ID 核对

主类采用 M 的 mechanism_primary（本地研究归类，非官方原生子类），每题仅归一个主类，共 36：

- **M1 多目标工程演进：13**：`copier_modular_refactor`、`entt_graph_module`、`litestar_infra_refactor`、`mimesis_modular_refactor`、`nlohmann_json_modularization`、`packer_plugin_datasources`、`pocketbase_backend_architecture`、`pocketbase_tools_extensions`、`schemathesis_datagen_pipeline`、`schemathesis_reporting_observability`、`schemathesis_config_modernization`、`vault_sdk_resilience`、`zstd_api_modernization`。
- **M2 从规格构建系统能力：12**：`arc_compiler_runtime`、`dependent_type_checker`、`high_performance_object_mapper`、`juliet_vulnerability_analyzer`、`odata_query_service`、`lua_native_compiler`、`postgres_wire_on_sqlite`、`quic_transport_stack`、`stream_processing_engine`、`tls13_handshake_state_machine`、`cpu_full_flow`、`cfzip_compression_engine`。
- **M3 正确性约束下性能优化：6**：`ann_vector_search_qps`、`exchange_core_throughput`、`ffmpeg_swscale_reimplementation`、`integer_compression_codec`、`notebook_lossless_compression`、`vliw_kernel_optimization`。
- **M4 缺失或退化实现恢复：3**：`rust_multicrate_reconstruction`、`codeflash_repair_performance`、`regex_automata_repair`。
- **M5 行为等价重实现与移植：2**：`git_rewrite_in_zig`、`libexpat_x86_assembly`。

## 跨题机制覆盖与反例

以下是非互斥的设计机制索引，用来防止把代表性案例的特点套到全部任务。未列入不代表该题实际不存在，只表示当前材料不足以确认/突出；尤其论文概述不足以证明隐藏测试组合。

| 机制 | 有材料支撑的原题 ID（或明确的设计推断） | 不能普遍化的反例/边界 |
|---|---|---|
| 完整发行带来的交付宽度 | 全部 13 道 M1（上列）；每项来自同一产品版本目标，但可含独立改进 | `vliw_kernel_optimization`、ANN 不靠发行目标数量；PocketBase tools 明确多个相对独立工具，不能强称全耦合 |
| 自然能力链/跨表示语义 | `arc_compiler_runtime`、`rust_multicrate_reconstruction`、`codeflash_repair_performance`、`dependent_type_checker`、`odata_query_service`、`lua_native_compiler`、`regex_automata_repair`、`schemathesis_datagen_pipeline`、`cpu_full_flow`；协议题见下行 | Rust 真实 crate 图未得；不能把所有 roadmap 都当强依赖链，不能以跨文件数替代语义链 |
| 协议/格式/执行表示的兼容映射 | `ffmpeg_swscale_reimplementation`、`git_rewrite_in_zig`、`libexpat_x86_assembly`、`nlohmann_json_modularization`、`odata_query_service`、`postgres_wire_on_sqlite`、`quic_transport_stack`、`tls13_handshake_state_machine`、`cfzip_compression_engine`；`high_performance_object_mapper` 是类型表示映射 | 不代表都要从零、禁止依赖或覆盖完整协议；已知子集与 oracle 决定真实性 |
| 多模式/作用域/扩展点组合 | 实际 TODO 直接支持 `schemathesis_datagen_pipeline`；概述支持 `copier_modular_refactor`、`high_performance_object_mapper`、`packer_plugin_datasources`、`pocketbase_backend_architecture`、`schemathesis_reporting_observability`、`schemathesis_config_modernization`、`vault_sdk_resilience`、`zstd_api_modernization` 的设计推断 | 其余概述没有给组合矩阵；不能声称原题 hidden 已要求所有笛卡尔积交互 |
| 跨操作状态/生命周期 | 明确领域状态：`git_rewrite_in_zig`、`postgres_wire_on_sqlite`、`quic_transport_stack`、`tls13_handshake_state_machine`、`stream_processing_engine`、`vault_sdk_resilience`、`litestar_infra_refactor`；字典/产物：`notebook_lossless_compression`、`cfzip_compression_engine`；资源 ABI：FFmpeg/Expat | “有状态”不等于 crash recovery、并发、持久化；TLS traces 不等于网络栈。`rust_multicrate_reconstruction` 的重开流程是建议，实际契约未知 |
| 明确正确性约束下的性能/大小搜索 | 全部 6 道 M3；另论文明确 `codeflash_repair_performance`、`dependent_type_checker`、`stream_processing_engine`、`cfzip_compression_engine` 有性能相关指标 | `high_performance_object_mapper` 名称不足以证明性能评分；`zstd_api_modernization` 属于 API 演进，不能据领域推断压缩率计分 |
| 实现语言/产物形态本身就是目标 | `git_rewrite_in_zig`、`libexpat_x86_assembly`、`lua_native_compiler`、`ffmpeg_swscale_reimplementation`、`cpu_full_flow`、`vliw_kernel_optimization` | 原生编译/ABI/ISA 限制可保护测量目标；ANN 明确可用 FAISS，不能把“禁库”视为全体难度规律 |

官方时间曲线显示“困难”与“额外时间仍进步”也不等同：`research/software-engineering-2026-10-15/official-software-time-scores.csv:49` 的 datagen/GPT-5.4 从 2h–12h 都为 56.6；`:22` 的 Git/Opus 4.8 在 4h/6h/8h 都为 22.8；`:58` 的 VLIW/GPT-5.5 从 2h 71.6 增至 12h 85.6。它们是官方四舍五入聚合，不是本地 trajectory 或 gpt-6.1-sol 测量。要复现同难度，应对齐模型/工具/资源，记录阶段产物和平台原因，不能仅给长预算。

## 覆盖与验证边界

已用脚本核验 36 个卡片 ID 与 CSV 集合相同：36 个唯一 ID，缺失 0，额外 0，重复 0；CSV 重算主类计数为 M1=13、M2=12、M3=6、M4=3、M5=2，总计 36。公开任务 JSON 为 12/36，其他 24/36 为论文概述；实际 TODO 为 1/36 的选定镜像层。未 clone 源码、未深审全部代码、未还原镜像、未运行模型/容器、未读取外部 hidden tests，也未据此验收新题难度。
