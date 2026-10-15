# 已构造候选的难度缺口与可扩展交付物

本稿只读复核既有题面、评分与历史证据；未联网、未运行候选、未启动模型，未修改旧任务或评分。下面的新范围、组合场景和否证步骤均为**未运行设计**，不是新题已实现或已达到六小时难度的声明。路径均相对仓库根目录。

## 结论与证据口径

当前多数候选把真实大项目收缩成了一个特性或四个恢复函数。难度应来自交付完整子系统所需的状态、模块依赖、兼容面和调试反馈，而非仓库名字、文件数、故障数或预算字段。建议先验证 OpenAPI 产品里程碑、RESTler 恢复执行子系统、HTTPX 客户端执行层这三个方向；EdgeKV、Tree-sitter、TOML 需要重新选取完整产品范围。

| 候选 | 实际还缺什么 | 已有证据能说明什么 | 没有证明什么 |
|---|---|---|---|
| OpenAPI streaming | 生成器类型/模板、流式资源所有权、operation security 与请求编码集成 | 独立于最终参考补丁的 HTTPX 行迭代薄包装得到 .60，21/36 | 没有盲解完成耗时，.60 不等于剩余 .40 很难 |
| RESTler recovery | 一份顺序 BFS campaign 的 intent/result/UUID 重放和配置绑定 | pickle 加强方案恢复后多了两次 POST；作者参考达到 1 | 没有最强合法 response-replay 独立求解基线；没有 worker/GC/checker 集成 |
| HTTPX execution | 共享 dispatch 预算、有界 body replay、origin/cleanup/trace | 两种 tenacity 薄包装均突破预算；作者参考达到 1 | 不等于 ContextVar＋共享预算＋tee 包装无法快速完成 |
| EdgeKV | Python starter 上补事务、WATCH 与 EKV1 效果日志 | 常规 Valkey 事务能力已有；指定 CLOCK/日志不由裸 Valkey 提供 | 不是改造 Valkey 引擎；Valkey 探针也不是完整可提交 wrapper 分数 |
| Tree-sitter | 受控移除的 edit/ranges/reuse API 实现 | 完整参考 API＋忽略 old_tree 可以满分，当前奖励不要求高效增量 | 满分对照借用了完整上游 API，不能推出未知参考的 solver 很快满分 |
| TOML | 三文件四函数的 string decoder、folding、format、writer | 作者恢复参考 35/35；ASCII/丢格式反例为 .8667/.60 | 反例来自参考消融，且没有公开 cheap baseline 或盲解耗时 |

四种证据须分别记录：①作者参考证明合同可实现；②参考派生消融证明评分能否看见某能力；③不借参考补丁的正常库/配置/wrapper 基线用于检验廉价解；④本稿提出但未执行的设计。只有第三类与后续独立轨迹能支持早满或耗时判断。特别是 Tree-sitter 的“full_reparse_complete_apis”构造明确从 `material-src/tree-sitter` 复制完整 lib 后加 `old_tree=NULL`（`samples/software-authored-016-r1/14_tree_sitter_incremental/author-tools/controls.py:3-15`）。

## 1. OpenAPI：从一个流式接口升级为可发布的 SDK 生成器版本

**实际缺口与早满点。** 当前限定一个成功状态、一种成功媒体类型、referenced object 或 integer record；JSON/multipart 编码已有上游支持（`research/swe-difficulty-review-20261015/evidence/01_openapi_streaming/task/instruction.md:3-15`）。薄包装直接复用 HTTPX `iter_lines/aiter_lines`、context manager 和现有 `_parse_response`（`samples/software-authored-016-r1/01_openapi_streaming/author-tools/cheap.py:1-27`），已得到 .60（`research/swe-difficulty-review-20261015/evidence/01_openapi_streaming/evidence/frozen/results.json:153-175`）。UTF-8、分块、关闭等多个检查会随一个正常库选择共同解决，不能当多个独立长期里程碑。此前另一题的 composition profile 更被约 130 行通用预处理闭合；它是另一个版本，不得与 streaming .60 混报（`samples/software-multiline-001/REPORT.md:11,22`）。

**合理的新交付物（设计）。** “支持真实业务 API 的可发布 SDK 生成器版本”，先复现固定版本上的具体产品缺口，再确定以下相互关联目标：

- 统一 schema 引用/组合与稳定类型模型，让递归引用、判别联合、请求/响应方向差异贯通 parser→property→imports→模板，而非只预处理少数 schema。
- 明确 request representation 选择：多媒体类型的 requiredness、JSON/form/multipart 的模型和签名、文件流所有权；复用现有 codec。
- 统一 typed response/error：多个合法状态/媒体类型、普通与流式入口、可解析的类型注解和一致错误模型。
- security 继承/可选/匿名覆盖与共享 client 共存，保留 sync/async 对称和非流式兼容。
- 生成出来的 SDK 在一份真实 service workflow 中可用，并能重新生成、安装、类型检查和跑原生回归。每个目标交付行为，不能只交新增选项。

本地 issue 路线仅是待复现线索：multipart 文件数组、多 body requiredness、anonymous security（`samples/software-multiline-001/01_openapi/r2/ROADMAP.md:5-14`）；本轮没有复核这些 issue 当前状态，也没有声称固定版本均仍有缺陷。

**三条端到端组合场景（设计）。**

1. 含判别联合与相互引用模型的 schema→生成 SDK→JSON 创建 job→用 response ID 开启 typed NDJSON→消费者提前退出→复用 client 查询普通 endpoint；检查类型、实际 wire、响应关闭和后续调用。
2. 同一 endpoint 的 JSON/multipart 显式选择→带重复文件 part 的匿名上传→服务器观察 boundary/文件字节/无认证→共享认证 client 调私有 endpoint→异步取消流；检查请求级隔离与文件/response 所有权。
3. 修改 schema 增加一个合法 response variant→重新生成→旧普通调用仍可用→错误状态生成 typed error→非 ASCII record 分块→sync/async 结果一致；观察全链而非模板文本。

**先否证。** 在任何新评分冻结前，用当前 normal Jinja customization＋HTTPX＋一个通用 schema lowering 层实现最强合法候选。若这层即可完成上述真实目标，承认廉价方案，缩短预算或换产品范围，不能事后禁模板、HTTPX、预处理或删掉它已通过的分数。只有仍需多个可分别交付的模块且集成反馈可推进，才进入后续轨迹校准。

## 2. RESTler：从顺序重放扩为完整可恢复 campaign 执行层

**实际缺口与早满点。** 当前明确只支持 one worker、BFS、无 GC/checkers/refreshable auth/custom generators（`research/swe-difficulty-review-20261015/evidence/02_restler_recovery/task/instruction.md:26-32`）。核心是原生驱动中的 durable response/UUID replay，而非恢复整个 fuzzer。12 个检查中，多数有共同前提：实现一份可靠 event journal 与 logical occurrence ID 后可能一起通过。pickle 独立基线已暴露真实重复效果，日志记录 operations=28、live_resources=16；审查对照无故障 26 次（`research/swe-difficulty-review-20261015/evidence/02_restler_recovery/evidence/cheap-crash-result.log:1`；`research/swe-difficulty-review-20261015/REPORT.md:73-79`）。它只否证这份 pickle 方案。作者参考的完整分数和近错对照不能替代独立 recovery solver。

**合理的新交付物（设计）。** “可在实际 campaign 生命周期使用的恢复执行子系统”：

- 请求 occurrence identity、rendered values、响应和依赖资源的一致 journal；调度/BFS 恢复和已完成 campaign 只读打开。
- 支持生产场景所需的 worker 调度与 campaign checkpoint cut；并行时比较依赖顺序/效果集合，不强求调度偶然顺序字节相同。
- 将 GC 和 checker 请求纳入资源所有权、依赖活性与恢复语义；不得因 GC 把尚需读取的资源删掉。
- auth refresh、超时/重试、服务重启和 pending request 状态协同；只在网关确实提供 idempotency ledger 的边界内保证不重复效果。
- checkpoint/日志版本、压缩与恢复诊断；绑定会改变执行语义的配置，允许合同内的安全运维参数变化。

**三条端到端组合场景（设计）。**

1. 多 worker 创建父/子资源→某个 POST 网关已提交但未回包→进程死亡→auth 令牌更新→恢复 pending key→继续依赖 GET/checker→GC 只删不再使用的资源；观察 backend audit 和最终资源图。
2. 某 worker 完成 generation，另一 worker 在渲染 UUID/发送之间中断→旧 checkpoint＋journal 重建→重试相同 occurrence、后续 occurrence 使用不同 ID→native coverage/summary 与无故障语义基准一致。
3. 边探索边 checkpoint/compact→重启时遇 torn tail→保留已提交历史并继续→completed campaign 再打开无 wire；另测 complete-record corruption 拒绝且不发请求。

**先否证。** 独立实现最强合法 journal＋response replay＋现有 scheduler hook，不借参考补丁；先在当前合同上测，再在新的完整生命周期上测。如果核心 reducer 加几处 hook 就快速闭合全部，说明选择的新范围仍窄。并行/GC 是新增支持面，必须先有真实可运行 reference 和独立服务 oracle；不能把“加入多 worker”字样当长时性证据。无需 arbitrary API 的 exactly-once 保证，当前网关边界在题面已明确（同 instruction:45-55）。

## 3. HTTPX：从 dispatch 计数特性扩为完整执行策略子系统

**实际缺口与早满点。** starter 已保留原生 API 和上游正常能力，新任务只是 opt-in policy（`research/swe-difficulty-review-20261015/evidence/03_httpx_transport/task/instruction.md:3-5`）。当前明确不含 sleeps/clocks/jitter/Retry-After scheduling（同文件:13），主要缺共享预算、tee replay、origin 和清理。tenacity outer/transport 两方案三次 dispatch 只证明简单集成不对（`.../evidence/cheap-baseline-tenacity.json:3-23`）。uncapped .98214、foreign-auth .90476 明确是 reference-derived mutation（`.../task/AUTHORING_REPORT.json:59-98`），只能说明特定尾部缺陷仍得高分。

**合理的新交付物（设计）。** “生产客户端完整执行层”：保持普通库/包装/子类均可用，交付 deadline/attempt budget、重试时机与 Retry-After、可中断 backoff；stream replay 与 caller-owned 文件/流；auth/redirect/mount 的统一执行状态；按 origin 的并发/rate-limit admission 与取消；稳定公开诊断与兼容入口。并发调度只为真实共享配额需求存在，不能凭空增加与产品无关的 circuit breaker、持久化或协议重写。测试时用可注入时钟快速推进，不以真实睡眠制造难度。

**三条端到端组合场景（设计）。**

1. async 上传流→401 auth challenge→307 同源重定向→429 Retry-After→等待期间 cancellation→释放 response、replay buffer、origin permit→同 client 新请求成功；独立观察 dispatch 和资源。
2. 多个并发 send 共用 origin quota、各自独立 attempt/deadline→一个跨 origin redirect→凭据移除→挂载 transport 部分读取 body 后失败→拒绝不可重放请求；一个请求失败不能耗掉别人的逻辑预算。
3. sync 和 async 在相同脚本服务上重放→读取最终 response 时失败→不错误重试已暴露 body→close 异常保留正确主异常→trace 与真实 dispatch 对齐→禁用 policy 回到原生行为。

**先否证。** 完整写出 ContextVar/显式 per-send state＋共享预算＋有界 tee＋现成 retry scheduler 的合法方案；当前尚未做此强基线。按目标分别检查是否都是一个 central loop 的副产品。若正常库组合很快完成，不禁库，不通过许多重复 trace 字段或更紧时间限制挽救长时性。此方向只在多个真实缺失执行能力和它们的集成确实仍需工作时优先。

## 4. EdgeKV：从事务练习扩为完整单节点持久化子系统

**实际缺口与早满点。** 交付是 Python 源码服务，不是 Valkey C 引擎；starter 已有 incremental socket、typed store、logical clock 与开发日志（`research/swe-difficulty-review-20261015/evidence/09_valkey_transactions/task/instruction.md:3-17`）。judge 按 reply 串行化事件，无并发吞吐分（同文件:76-82）；29 场景按六组分数（:159-172）。当前通常可由 command admission＋per-client queue＋key version＋effect WAL 四组核心状态闭合。Valkey 本体通过通常事务/WATCH，却不支持指定 CLOCK/EKV1，仅是产品能力探针（`.../evidence/baseline.json:20-54`）。不能把它当完整合法 wrapper 的分数，也不应为了难度继续限制正常存储库。

**合理的新交付物（设计）。** “可在线备份和持续运行的单节点持久化存储层”：事务效果日志＋一致恢复；snapshot/segmented WAL/compaction 的共同提交边界；边写边备份与 restore/校验 CLI；存储版本升级和兼容读取；客户端 backpressure、连接退出、读视图与 TTL 一致性。内置类型与命令范围按真实应用选取，不靠再加几十个平行命令。复制/集群先不引入，除非确有产品需求和可验证故障模型。

**三条端到端组合场景（设计）。**

1. 客户端 A WATCH→B 在含 TTL 的 EXEC 中更新→后台建立 snapshot→CLOCK 过期→A 中止→完成 compaction→强杀恢复；恢复状态与 snapshot cut＋后续日志效果一致。
2. 多客户端 pipelining→有的慢读造成 backpressure→事务已 fsync 尚未回包时死亡→恢复后数据原子可见→未完成客户端队列不恢复→继续写并执行在线备份；观察回复、数据和日志边界。
3. 旧版本 backup→新版本 restore/migrate→外部独立 reader 校验→持续写入并轮换日志→遇 torn final segment 恢复→遇完整记录损坏拒绝且不破坏备份；测试恢复后再备份的闭环。

**先否证。** 新版本允许正常 SQLite/WAL 或成熟 KV 支持时，优先用最强嵌入式存储＋薄 RESP adapter 对照。若需求全部由正常库轻易闭合，承认该结果，不发明独占 EKV2 格式阻止复用。只有真实“可独立读取/迁移”的产品需求才能要求格式。先用真实数据/恢复时间需求说明 snapshot/compaction 的必要性，再决定是否需要性能分，不能靠等待或小 safeguard 人为卡满分。

## 5. Tree-sitter：当前合同不测高效增量，宜另立完整文档服务

**实际缺口与早满点。** 当前只恢复四处 runtime 核心，完整首次解析 retained，明确允许 full reparse，不评分 pointer/allocation 或速度（`research/swe-difficulty-review-20261015/evidence/14_tree_sitter_incremental/task/instruction.md:3-5,12,16,20`）。198 个检查不是 198 个独立工程目标。当前 full-reparse 对照从完整上游 API 派生而来，得 1 说明**评分不区分高效增量**；只给受损 starter 加 old_tree=NULL 得 .46861，不得混成“廉价修改满分”（`samples/software-authored-016-r1/14_tree_sitter_incremental/task/AUTHORING_REPORT.json:50-63`）。

**合理的新交付物（设计）。** “面向编辑器的多语言文档解析与查询服务”：版本化文档/rope 与 edit→point 转换；解析调度、取消与旧结果抑制；host/embedded language included ranges 与 scanner 生命周期；query capture、diagnostic/index 缓存及失效；跨文档打开/关闭和隔离；可观测内存/延迟质量。保留正常完整 Tree-sitter 为可用组件，难点转为真实服务全链。若任务专门优化 parser，则另选确实存在、可稳定测量的编辑工作负载与性能目标，不能仅禁止 full reparse 或数复用节点。

**三条端到端组合场景（设计）。**

1. Markdown 文档包含 Python block→改变 fence/缩进并批量编辑中文→host ranges 更新→Python scanner 重新解析→query/diagnostics 更新→旧版本异步结果晚到被忽略；输出按 document version 关联。
2. 打开两个共享 grammar 的文档→一个复制快照供后台查询、另一个编辑→取消前者解析→关闭一个文档→另一个继续 edit/query；不泄漏 scanner/tree，也不污染 cache。
3. 项目文件重命名与一批 syntax repair→局部/全量解析任选→跨文档索引移除旧 symbol、产生新诊断→服务重开仍重建一致结果；检查用户可见索引而非候选自报 changed ranges。

**先否证。** 用完整现成 parser＋每次全量 parse/query＋简单 document map 作为最强直接方案。若在实际规模下正确性和用户需要的延迟/内存都达标，允许满分；不能为了“incremental”标签惩罚。若完整 service 仍被几处 wrapper 轻易闭合，则重估范围；若真正性能瓶颈存在，再冻结代表性文档/编辑负载和稳定计时，不把扩大字符数本身当系统设计难度。

## 6. TOML：从四个 helper 恢复扩为保格式配置迁移产品

**实际缺口与早满点。** 当前题面就是 four gaps/three files（`samples/software-multiline-001/05_toml/instruction.md:3-5`）；manifest 列出 escape 50 行、folding 84 行、format 23 行、writer 107 行（`.../authoring/mask-manifest.json:5-34`）。tokenizer、parser state、AST/container edit 大部分仍在。35 个行为案例和跨三 crate 是接口覆盖证据，不能扩大成重建 parser。reference=1、ASCII=.8667、丢格式=.6 来自作者对照，没有独立 cheap solver（`.../AUTHORING_REPORT.json:15-38,70-75`）。

**合理的新交付物（设计）。** “对真实项目配置执行安全、保格式迁移的 Rust 库＋CLI”：path selection/escaped dotted keys 与 array-of-tables；rename/move/insert/delete 的 CST 编辑及 comment/decor 附着规则；类型/约束诊断与 source span；分版本 migration plan、冲突检测、dry-run/diff；原子文件更新与失败恢复；serde/public API/feature 兼容。选择一组真实应用配置从旧版本迁移到新版本的完整规格，而非给 TOML 强加非标准 include 或随意业务规则。

**三条端到端组合场景（设计）。**

1. 带 escaped dotted key、Unicode multiline 与注释的配置→schema 诊断→生成 migration plan→把 scalar 移入 table→writer 保留其他内容→重新 parse＋serde 到目标配置→第二次迁移幂等。
2. array-of-tables 中按稳定 key 选择目标→rename/move 与已有 key 冲突→dry-run 报原始 span 且文件无变化→用户提供明确冲突策略后 apply→语义正确并保存未涉及的 comments/order。
3. CLI 对真实 workspace 配置集执行预检→部分文件含无效 escape→整批不写→修复后原子替换→故障打断时可恢复→重跑 plan 验证无重复迁移；多文件原子性仅在产品确实要求时纳入，不能凭空捆绑。

**先否证。** 首先用正常 toml_edit/serde 现成功能＋通用 path walker＋migration callbacks 构建最强合法方案。若主要需求已由 API 提供，不能靠删更多上游 helper 制造工作；改选真实缺失的 refactoring 语义，或把任务认作短程开发。若采用恢复路线，应交付相互依赖的完整语法/编辑子系统，不能按“删除多少行”定难度，也不能把作者私有 inverse patch 当学生捷径。

## 本稿实际读取覆盖

- 全文：`research/swe-difficulty-review-20261015/REPORT.md`、`review.json`；`samples/software-multiline-001/REPORT.md`；上述六题 instruction；`samples/software-multiline-001/01_openapi/r2/ROADMAP.md`；TOML `AUTHORING_REPORT.json`、`mask-manifest.json`；Tree-sitter `author-tools/controls.py`；OpenAPI `author-tools/cheap.py`、`controls.py`。OpenAPI/Tree-sitter 两份 samples instruction 与 evidence 副本已比较一致。
- 选段/结构：五题 `task/authoring/score-spec.json`（OpenAPI 各组、RESTler 各检查、HTTPX 部分结构、EdgeKV 各组、Tree-sitter 各组及 membership/性能字段）；TOML `authoring/score-spec.json:1-68`。未声称审计全部 hash 清单或所有冻结 case。
- 实际 grader 行为与聚合选段：OpenAPI `task/tests/grader.py:175-260`；RESTler `:74-174`；HTTPX `:183-252` 及聚合位置检索；EdgeKV `:173-234`；Tree-sitter `:73-123`；TOML `tests/grader.py` 的入口/比较/聚合位置检索。不是完整运行/QC。
- 既有证据：OpenAPI `evidence/frozen/results.json` 的 reference/nop/cheap 段；RESTler `cheap-crash-result.log` 和作者报告 `:1-130`；HTTPX `cheap-baseline.json`、`cheap-baseline-tenacity.json`、作者报告 `:1-140`；EdgeKV `baseline.json`；Tree-sitter 作者报告 `:1-100`；TOML 作者报告全文。大文件仅列实际阅读部分，不把文件存在算读完。

本稿没有重新验证旧分数的可执行环境、模型身份或作者运行时长。所有路线均须先把新交付物和最强正常基线做成，再冻结新版本；随后才有资格从独立解题轨迹判断是否持续获得实质成果。
