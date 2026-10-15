"""Render manually researched candidate designs with local source evidence.
This is documentation/inventory, not a task generator or runtime validator.
"""
import csv, datetime, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
D=[]
def add(id,priority,license,anchor,task,existing,scope,oracle,dimensions,late,shortcut,probe,risks,evidence,previous=None):
 D.append(dict(id=id,priority=priority,license_observation=license,edgebench_analogue=anchor,proposed_task=task,existing_capability=existing,artifact_scope=scope,reference_plan=oracle,score_dimensions=dimensions,post_two_hour_hypotheses=late,cheap_strong_baseline=shortcut,first_falsification_probe=probe,construction_risks=risks,evidence=evidence,previous_profile=previous))
add('01_openapi_streaming','P1','MIT；保留 LICENSE 和贡献者声明。','schemathesis_datagen_pipeline / reporting_observability：改造框架生产代码。',
 '为真实 Python SDK 生成器增加一个完整的流式端点合同：同步/异步 NDJSON 迭代、取消与关闭、端点认证覆盖；再验证它与 multipart 模型编码及共享 client 的交互。',
 '已有 sync/async API、认证 client、multipart 与 client 生命周期；CHANGELOG 已记载多次 multipart 修复。这里的新需求是联合合同，不能把上述现有能力统称为缺失。',
 ['生成器解析/模型层、Jinja 模板、生成包的公开签名','在离线本地服务上执行生成后的 SDK；只改内部 schema helper 不算完成'],
 '先写独立 HTTP 观测器记录请求、迭代时序与关闭事件；参考分支需真正生成并运行包，不能用与 candidate 相同 helper 自证。旧参考只覆盖旧 profile。',
 ['逐记录流式交付且不预读完整响应','正常/异常/取消的资源关闭','sync/async 与类型签名一致','匿名/认证覆盖且无凭据串用','multipart 与历史生成回归'],
 ['已有流式 happy path 后，处理分块 UTF-8、半条记录、取消与复用连接的交互','完善 auth 覆盖、文件数组及多媒体类型与生成导入的联合兼容'],
 '给作者一个直接改模板、复用 httpx.iter_lines 的强基线；若几处模板修改即可过完整联合合同，缩小优先级，不能靠加同类样例保住难度。',
 '先在固定 commit 复现 ROADMAP 中的具体案例，再用最小 stream 模板补丁跑完整端到端行为矩阵。',
 ['issue 状态不能代替固定版本复现；multipart 部分已实现','NDJSON 是本批拟定合同，尚无该合同的完整参考分支','完整离线依赖与隐藏集尚未冻结'],
 [('openapi_python_client/templates/endpoint_module.py.jinja','def _parse_response','真实端点模板和解析入口'),('CHANGELOG.md','multipart array serialization','已有 multipart 改动历史')],
 'samples/software-multiline-001/01_openapi；旧 schema profile 本地满分但已拒作长程题；r2/ROADMAP.md 只有新设计。')
add('02_restler_recovery','P1','MIT；另行固定实际被测服务及其许可。','Schemathesis 工程演进类；相似的是框架状态与执行链改造，不复用原题需求。',
 '让 RESTler 的真实 BFS campaign 支持可恢复执行：持久化 generation、请求/资源 journal，在外部服务重启、响应丢失及进程崩溃后恢复一致状态。',
 'driver 已调用 saver，但固定版本 saver.save 直接 return，load 也提前返回默认状态。旧代码中的 pickle 路径不是已启用的生产恢复机制。',
 ['CLI→driver→checkpoint/journal 的真实入口','真实服务、资源创建/清理与重放边界；通过落盘代码文件提交，由 judge 每次新启动 campaign'],
 '控制器在确定的请求序号注入故障，保存服务端审计记录，与不停机对照及独立资源状态检查比对。不能仅测 save/load 函数。',
 ['checkpoint 原子性与损坏回退','恢复后的 BFS generation/覆盖语义','资源与依赖状态一致','重试/重放的重复副作用控制','CLI 配置、并发和回归'],
 ['持久化跑通后，解决响应丢失时请求是否执行的歧义及服务端资源复用','进一步解决多个请求序列、并发 worker、清理失败与 checkpoint 的交互'],
 '先试只移除 early return、修 pickle、加原子 rename 的基线；它若已覆盖所有评分，说明新题仍退化为小修复。',
 '用实际 RESTler CLI 对真实 Polaris 服务完成一次按序号注入的 kill/restart；确认旧 component 高分不能通过这个完整场景。',
 ['旧小样只有组件闭环，正式 score 仍无效','Polaris 本地曾缺 Java；需要实际 .NET/Java 服务构建链，不能换成 toy 服务冒充','exactly-once 只有协议允许时才可要求，必须明确允许的幂等键与服务能力'],
 [('restler/utils/saver.py','def save','真实 saver 入口；下方有 early return'),('restler/engine/core/driver.py','saver.load','driver 加载 checkpoint 的调用')],
 'samples/software-multiline-001/02_restler；组件参考 6/6 不能迁移为完整题 Oracle。')
add('03_httpx_transport','P2','BSD-3-Clause，依据 LICENSE.md；依赖另查。','vault_sdk_resilience / litestar_infra_refactor：跨层资源与执行策略。',
 '给 HTTPX 增加明确的请求执行策略合同：重试预算、可重放 body、认证/重定向边界与结构化执行事件，同时覆盖同步和异步。这是新需求提案，不是已确认上游 bug。',
 '固定源码已有 auth flow、redirect chain、sync/async transport 关闭，以及取消时关闭连接的测试。不能把已有取消清理再包装成新任务。',
 ['修改 Client/AsyncClient 的执行链及公开配置','输出机器可读但不泄漏敏感头的事件；候选实现作为库被真实调用'],
 '独立 scripted transport/loopback server 按事件序号返回响应；外部观测实际请求与 close 次数，冻结 clock 与 backoff。',
 ['重试和 redirect 共享预算','流式 body 的可重放性','跨 origin 认证边界','取消/异常时的关闭','事件语义与原 API 兼容'],
 ['基础重试之后处理 auth challenge、redirect 和不能 rewind 的 body','处理异步取消、部分响应消费与连接释放的交互'],
 'tenacity 风格 wrapper 加 MockTransport 可能很快覆盖需求；允许正常依赖，先验证 wrapper，不能靠禁库制造难度。',
 '把当前已有能力和拟增需求逐项对照，再构造一个最薄 wrapper；若不改执行链即满足合同则暂停此候选。',
 ['需求组合若缺乏共同原因，容易成为人为拼接','尚无固定的新需求参考实现或已复现缺陷','已有功能完备，早满风险高'],
 [('httpx/_client.py','def _send_handling_auth','现有认证执行链'),('tests/client/test_async_client.py','test_cancellation_during_stream','已有取消场景测试')])
add('04_pytest_fixtures','P2','MIT；第三方插件许可和版本需独立固定。','copier_modular_refactor / schemathesis_config_modernization：开发工具跨层演进。',
 '实现 fixture 执行图与失效原因诊断：在参数切换、动态 getfixturevalue、setup/teardown 失败和插件 hook 下，输出可复现的依赖及清理事件。',
 'pytest 已有 fixture 缓存、依赖 finalizer 注册、缓存失效与多个 finalizer 异常处理；本候选增量是一个公开、稳定且不扰动行为的诊断合同。',
 ['fixture 执行器、收集/报告与 plugin hooks','提交可安装源码，judge 在多个子进程收集行为和诊断，不能只分析静态测试文本'],
 '独立 fixture 体写事件日志，对照实际 setup/teardown 次序；正常 pytest 运行是行为基线，新增诊断需要独立期望生成器。',
 ['依赖关系含动态请求','缓存命中/失效原因','异常后的 finalizer 顺序','plugin hook 与报告一致','开启/关闭诊断时行为不变'],
 ['简单 DAG 后处理动态 fixture 和参数缓存失效','处理多个 teardown 异常、跨 scope 依赖及 plugin 重入'],
 '纯 pytest plugin 可以直接观察很多 hooks；先实现常规 plugin 基线，若已近满则无需改 core，也应降低此路线优先级。',
 '用现成 hooks 编写最小诊断 plugin，并验证它是否能区分实际缓存失效和重复 finalization；先证实 core 改造必要性。',
 ['目前是新诊断需求，不是复现完成的真实 bug','容易把测试条数误当工作量','插件版本组合多，必须冻结实际支持边界'],
 [('src/_pytest/fixtures.py','def finish','已有 finalization'),('src/_pytest/fixtures.py','def execute','已有缓存和依赖执行'),('doc/en/explanation/fixtures.rst','scope','fixture scope 文档')])
add('05_uv_resolution','P1','Apache-2.0 OR MIT；实际离线包索引中的包逐项另查。','Packer 插件/配置演进、依赖类型检查器：约束传播与兼容性。',
 '在 uv 中实现跨环境 lock 更新计划与机器可读解释：输入旧 lock 和变更，保持未受影响解稳定，解释 marker 分叉、受影响依赖及冲突；不是从零重新实现已有 universal resolver。',
 'universal lock、marker 分叉、workspace、lock 更新和冲突处理均已存在。新增合同必须明确超出 uv lock / --upgrade-package 的哪些输出和稳定性保证。',
 ['resolver、lock serialization 和新的 update-plan CLI/API','固定的本地 wheel/metadata 索引；不同 Python/platform marker 的离线目标矩阵'],
 '用小图穷举所有合法解验证计划/解释；大图对照固定 uv 参考结果和声明的稳定性目标。新计划的完整参考分支待写。',
 ['各环境依赖解合法','不必要变更受控','marker 分叉与合并','解释可追溯到输入约束','冲突诊断及 lock 可往返'],
 ['单环境解之后处理 extras、workspace 和跨平台分叉','在正确性保持下减少锁文件扰动并保证解释与最终解一致'],
 '先调用现有 uv lock 再做 lock diff 和约束回溯；若这已满足合同，则是短脚本题，不应升级为长程。',
 '用本地微型索引给出现有 uv + diff 的一个明确反例，并为小图计划写独立穷举检查器。',
 ['计划目标和最小变更的偏序需先定义，不能把所有无关升级都判错','包数据与 Rust 依赖尚未完整 vendor','索引规模本身不是推理难度证据'],
 [('docs/concepts/resolution.md','fork','已有 universal resolution 文档'),('crates/uv-resolver/src/resolver/mod.rs','marker','实际 resolver 实现'),('crates/uv/tests/lock/lock.rs','fn lock','真实 lock 回归入口')])
add('06_wasm_validation','P1','document/core 为 W3C 文档许可；interpreter 和 test 为 Apache-2.0。根 LICENSE 不是单一 Apache 许可。','arc_compiler_runtime / dependent_type_checker：从规格构建带验证的执行系统。',
 '从明确冻结的 WebAssembly 子集合同构造类型验证、模块实例化与执行器，覆盖 structured control、stack-polymorphism、tables/call_indirect、imports 和内存边界。',
 '规格仓库已有参考解释器、valid 模块与大量 assert_invalid/assert_trap 测试。当前源码 SHA 不在本报告中等同于 v1.0.0 tag；旧小样只实现 i32 的窄 VM。',
 ['模块验证、链接、实例化、解释执行的实际源码','显式列出支持 opcode 和导入 ABI；未支持特性必须稳定拒绝'],
 '隔离的官方解释器与固定 V8/其他实现交叉对照；生成合法/非法的结构化模块并缩减差异。两个参考不一致先剔除争议输入。',
 ['类型验证含不可达代码','控制栈与函数调用','table 和间接调用','链接/实例化阶段','内存/数值边界及 trap 分类'],
 ['i32/control 跑通后处理类型多态、分支合流和非法模块','加入多模块导入、间接调用及实例化时失败的阶段一致性'],
 '测已有 VM 绑定或 wasm 执行库 wrapper 能覆盖多少；若交付 API/正常依赖允许其完整通过，应放弃此 profile，不能临时禁止工具。',
 '先冻结指令/ABI 子集，拿旧 i32 实现跑新增 validation + linking 用例，确认新增分数来自真实能力而非多造同类算术题。',
 ['完整 WASM 规范远超小样范围；必须先收敛可实现子集','旧负数除法缺陷只伤很少样例，需按语义维度重审权重','源码 SHA 与所谓 v1 标签需要分别记录'],
 [('interpreter/valid/valid.ml','let check_stack','独立类型验证实现'),('test/core/call_indirect.wast','assert_invalid','间接调用的非法模块用例'),('test/core/unwind.wast','assert','控制栈测试')],
 'samples/software-multiline-001/03_wasm；223 case 的旧分数仅适用于旧 i32 profile。')
add('07_arrow_ipc','P2','Apache-2.0，保留 NOTICE；独立互通数据仓库另固定许可。','stream_processing_engine / 自建数据系统：格式与状态交互。',
 '实现可被嵌入的增量 Arrow IPC 读写器，处理分段输入、嵌套 nullable 类型、dictionary delta/replacement、多 record batch 与损坏流，输出明确消费进度和诊断。',
 'Arrow 本身已有这些格式能力与跨语言 integration runner。必须选择合适的轻量 starter 或新增 API，不能在完整 Arrow 上要求再实现原样 reader。',
 ['进程内增量 API 加独立 CLI','公开明确 stream/file 的不同字典规则、支持类型和内存合同'],
 '固定独立语言的 Arrow producer/consumer 做互通，辅以手工最小消息和变形测试；不能 candidate 写什么再用自己读回就算正确。',
 ['Schema/RecordBatch 及 nested/null 布局','dictionary 生命周期','分块/截断输入','stream/file 互通','内存与诊断合同'],
 ['标量 reader 之后解决嵌套 offsets、validity 与共享字典','完善 delta/replacement、截断恢复及真正增量消费'],
 '直接用 pyarrow/Arrow Rust 的正常 wrapper 是必须先测的强基线；若 API 与资源合同没有实际差异，这条路线应淘汰。',
 '冻结公开 API 后，用一个现成 Arrow binding 实现最薄版本；只有出现合理合同下的真实缺口才构造。',
 ['成熟库包装即满分的风险非常高','尚未取得 arrow-testing 的完整固定数据包，只取得格式/runner 依据','增加类型数量不能替代长程证据'],
 [('format/Message.fbs','table DictionaryBatch','字典消息与 delta 字段'),('docs/source/format/Columnar.rst','DictionaryBatch','正式格式依据'),('dev/archery/archery/integration/runner.py','def run','跨语言互通 runner')])
add('08_http2_session','P2','MIT，LICENSE 指向 COPYING；测试依赖另查。','postgres_wire_on_sqlite / quic_transport_stack：有状态协议实现。',
 '构造不依赖真实互联网的 HTTP/2 会话核心：分片收包、HPACK 上下文、stream 生命周期、flow control、GOAWAY/RST/CONTINUATION 等交互，暴露进程内事件 API。',
 'nghttp2 已完整实现协议并有 HPACK/session 测试。素材用于参考和构造状态轨迹，不是提出 nghttp2 当前缺这些功能。',
 ['字节输入→帧→连接/stream 状态→事件输出','固定 RFC 子集、错误优先级和应用侧消费/窗口更新 API'],
 '固定 nghttp2 的事件适配参考，另用协议不变量检查器验证窗口、stream 状态及错误范围；网络端点只在 judge 的本地进程中运行。',
 ['帧增量解析','HPACK 上下文一致','stream/connection 错误范围','flow control','多 stream 与关停交互'],
 ['单 stream 后处理多 stream、窗口耗尽和部分消费','进一步处理 header continuation、动态表与关停竞态'],
 'hyper-h2 或 nghttp2 binding 常规 wrapper 可能立即解决全部合同；需要先做，不能通过禁止正常依赖掩盖这一点。',
 '先建立两段互相影响的 HPACK/flow-control 状态轨迹，同时实现现成 binding 基线；比较完整能力范围。',
 ['若只是 trace decoder，工程量会很小','若加入真实网络时序，会损伤确定性，应按事件驱动调度','完整 RFC 范围不明确则无法判断完成度'],
 [('tests/nghttp2_session_test.c','test_nghttp2_session_recv_continuation','跨帧 header 状态测试'),('tests/nghttp2_session_test.c','test_nghttp2_session_recv_data_no_auto_flow_control','显式流控测试'),('tests/nghttp2_hd_test.c','void test_','独立 HPACK 测试')])
add('09_valkey_transactions','P1','主源码 BSD-3-Clause，依据 COPYING；deps/LICENSES 需在离线打包时逐文件核对。','postgres_wire_on_sqlite / stream_processing_engine：协议与持久状态系统。',
 '构造带 RESP3 API 的事务型 KV 服务，明确 MULTI/EXEC/WATCH、多个客户端、错误与断连语义，再增加 crash-safe journal 与恢复；参考 Valkey 语义但使用独立新任务合同。',
 'Valkey 已有 multi.c、AOF 和真实 multi/protocol 测试；不是在完整可运行 Valkey 上要求补一个已存在命令。',
 ['协议层、数据状态、事务队列、watch 失效、日志重放','提交源码和静态配置；judge 每次从固定数据集新建服务并执行确定的客户端事件序列'],
 '用固定 Valkey 生成命令级参考，独立小状态机验证事务；任务自定义 journal 必须有独立恢复不变量，不用参考自身序列化结果充当 oracle。',
 ['RESP3 编码/错误','事务排队与执行','多客户端 WATCH 失效','断连及错误隔离','journal 截断与崩溃恢复'],
 ['单客户端命令后处理排队错误、watch 变化与跨客户端交互','完成基础持久化后处理部分 journal、崩溃点和恢复重放'],
 '测系统 redis/valkey 直接代理或嵌入现成服务器能否满足新合同；正常服务依赖若足以解题则此版本不合格。',
 '先写不依赖 socket 时序的事件调度器，给出事务/崩溃恢复的最小跨模块链；确保不是字符串字典 toy。',
 ['不得把不可控墙钟 TTL、并发调度当隐藏难点；需要可注入逻辑时间','旧服务器的命令集合很大，必须明确子集','正常可用完整服务带来的 shortcut 需先筛'],
 [('src/multi.c','void execCommand','事务执行真实入口'),('src/aof.c','loadAppendOnly','持久化加载入口'),('tests/unit/multi.tcl','MULTI / EXEC basics','真实事务回归素材')])
add('10_datafusion_sort','P1','Apache-2.0，保留 NOTICE；crate 各许可随 vendor 汇总。','ann_vector_search_qps / exchange_core_throughput：正确性下的真实引擎性能优化。',
 '在固定 DataFusion 50.0.0 源码中优化 SortExec/TopK/多分区 merge，在内存上限和 spill 条件下保留 SQL 排序语义；交付可编译真实引擎补丁。',
 '源码已有 external sort、TopK、memory reservation 和 spill；目标是性能改善，不能把现有功能称为待实现。固定 Cargo.toml 的 MSRV 为 1.86.0。',
 ['生产算子及必要 planner/runtime 改动','真实 RecordBatch 执行路径；不允许把实际引擎换成一个独立 Python 排序脚本再冒称优化'],
 '正确性使用独立 SQL/Arrow 结果合同，计时运行真实编译后的引擎；tie 顺序、NaN、NULL 与字符串 collation 先明确。baseline/reference 时间必须实测，当前均未填。',
 ['SQL 排序正确性门槛','TopK 与全排序时延','spill 工作负载时延','峰值内存和 I/O','跨 partition 结果'],
 ['普通数值排序之后处理 string/NULL、高重复、offset/limit','改善低内存、多 partition 与 spill 的协调，保持正确性'],
 '先扫现有 sort 配置、batch size 和算法开关；已有优化配置若已接近上限，不能发明一个更慢 baseline 来造 headroom。',
 '先在固定 50.0.0 编译真实 probe，完成真实 baseline；旧较新版本补丁要重新适配，dry-run 成功不是性能证据。',
 ['上一轮没有真实 DataFusion 编译/性能分，不能沿用模拟或 Python proxy 分值','耗时和确定性依赖 CPU/磁盘；跨架构计时端点不能共用假常数','Rust 依赖构建需先 vendor'],
 [('Cargo.toml','rust-version','固定工具链下限'),('datafusion/physical-plan/src/sorts/sort.rs','pub struct SortExec','真实执行算子'),('datafusion/physical-plan/src/sorts/sort.rs','fn spilled_bytes','已有 spill 路径')],
 'samples/software-multiline-001/04_datafusion；原较新 revision 与本候选 50.0.0 不同，当前正式奖励仍无效。')
add('11_rocksdb_compaction','P2','GPL-2.0 OR Apache-2.0；COPYING 和 LICENSE.Apache 已下载。选择许可并保留逐文件声明。','exchange_core_throughput / notebook_lossless_compression：正确性与多个资源指标下的性能优化。',
 '在固定资源与固定混合读写/恢复负载上改进 RocksDB compaction 调度或数据路径，优化吞吐/尾延迟，同时约束持久性、空间及写放大。',
 '引擎已有多种 compaction 与大量可调参数。db_bench 有配置和计时；db_compaction_test 是正确性素材，不能拿 db_bench 单独证明无数据丢失。',
 ['引擎源码及明示允许的配置','judge 新建数据目录、重放固定操作日志、执行确定崩溃点；提交不依赖 agent 的活 DB'],
 '独立 key/value 操作日志模型检查结果和恢复；实测 untouched baseline 与最强合理配置基线。性能端点暂空，不按指标理论边界假定可达上限。',
 ['读写/恢复正确性门槛','混合负载吞吐','固定窗口尾延迟','空间和写放大','资源预算'],
 ['单一吞吐优化后解决读写互相影响和 compaction stall','协调恢复、后台 compaction 与空间上限的性能取舍'],
 '先试 pipelined write、buffer/compaction 参数和批处理；成熟引擎普通调参可能消耗全部 headroom，应先否证。',
 '同机重复运行 untouched 与强配置 baseline，随后用 db_stress/日志模型检查；若剩余稳定增益不足则不出题。',
 ['严格尾延迟容易受宿主噪声影响','禁 WAL 可虚增吞吐，必须由耐久性合同和行为检查约束','持续后台状态要在每次 verifier 内重建，不能依赖 agent DB'],
 [('README.md','dual-licensed','许可及引擎说明'),('tools/db_bench_tool.cc','DEFINE_int64(write_buffer_size','已有调参基线'),('db/db_compaction_test.cc','TEST_','真实 compaction 测试')])
add('12_croaring_kernels','P2','Apache-2.0 OR MIT，依据完整 LICENSE；测试 realdata 的来源另固定。','integer_compression_codec / vliw_kernel_optimization：组合表示和机器内核优化。',
 '针对混合 array/bitset/run 容器的批量 bitmap 查询，优化交并差、cardinality 聚合或避免中间物化的数据路径，保持标准序列化和边界行为。',
 'CRoaring 已有 SIMD、运行时 dispatch 和多类容器运算。任务不能仅要求写一个 AND 内核，也不能把打开既有 SIMD 开关叫新算法。',
 ['真实库内核与批量接口，稳定 C ABI','固定合成/许可确认的真实分布；测处理时间、内存和构建成本'],
 '小规模使用独立整数集合 oracle，大规模校验固定摘要及逐样例结果；原始性能 baseline 必须在指定 CPU 实测。',
 ['集合语义正确性门槛','不同容器/密度分布的查询时间','避免中间物化的批量路径','序列化互通','内存与构建成本'],
 ['单容器快速路径之后做混合表示与 skew 的算法选择','优化聚合与序列化协调，并解决 scalar/SIMD 两条路径一致性'],
 '调用库已有 and_cardinality、聚合接口、run_optimize 和 CPU dispatch；若现成 API 组合已近最优，不应继续堆数据规模。',
 '先把最强现成 API 组合跑在声明负载上，检查是否存在剩余可稳定改善的热点。',
 ['x86 AVX 与 ARM NEON 的 headroom 不同；不能承诺一组跨机器性能端点','成熟库早满风险高','新任务批量 API 与内存预算尚未冻结'],
 [('README.md','ENABLE_ROARING_MICROBENCHMARKS','已有微基准入口'),('src/roaring.c','roaring_bitmap_and_cardinality','现成 cardinality 快路'),('tests/mixed_container_unit.c','array_negation_range_test','混合容器边界素材')])
add('13_toml_lossless','P1','Apache-2.0 OR MIT；保留所有 crate 的许可及测试数据声明。','rust_multicrate_reconstruction / regex_automata_repair：跨 crate 语义恢复。',
 '构造跨 tokenizer/parser、span/decor 与 toml_edit 结构修改链的受控缺失实现，恢复注释/空白/原始字符串保真、错误位置和连续编辑兼容。',
 'toml-rs 已提供无损编辑和 span 数据；旧小样只去掉四个 helper，恢复范围太窄。新 profile 不能继续只按那四个函数的覆盖计分。',
 ['多个实际 crate 的生产代码缺口及保留公开 API','改动要跨原始文本→span→结构→输出；不做任意删除文件导致无法起步的题'],
 '固定完整参考版本在私有 verifier 编译；独立编辑操作脚本检查语义与不变片段，生成新组合/错误边界，避免仅逐字复用上游 tests。',
 ['合法/非法 TOML 语义','span 和错误位置','注释/空白/字符串保真','dotted key/implicit table/array-of-tables 编辑','连续编辑及 serde 回归'],
 ['解析单文档后修补 implicit/dotted table 的编辑交互','处理多轮编辑、despan/ownership 与错误位置的一致性'],
 '检查 starter、vendor、文档和已安装 crate 中是否仍有可直接复制的原实现；再试薄封装现有 toml_edit。若正常可用依赖即可满分，重做缺口合同。',
 '先做跨层依赖图与受控缺口清单，证明只恢复旧 helper 不足；用真实多轮编辑观察文本而非只查 AST。',
 ['原实现公开且可能被记忆，不能把源码恢复自动当成新训练能力','新缺口及 reference/starter 差分尚未实施','原本狭窄的 35 case 满分不等于新合同可达'],
 [('crates/toml_edit/src/document.rs','fn despan','文本所有权与 span 的联系'),('crates/toml_edit/src/table.rs','implicit','隐式 table 行为'),('crates/toml_edit/tests/testsuite/edit.rs','fn parsed_document_outlives_input','真实文本与连续编辑素材')],
 'samples/software-multiline-001/05_toml；旧本地参考 1 分，尚无新跨层任务实现。')
add('14_tree_sitter_incremental','P1','MIT；使用的各语言 grammar 是独立仓库，必须另固定 commit/许可。','regex_automata_repair / rust_multicrate_reconstruction：核心状态与跨层恢复。',
 '恢复 Tree-sitter 在编辑后重用旧树、修正节点范围及错误恢复的关联实现，保留 API 和确定的 grammar，验证连续多次编辑后的解析一致性。',
 'Tree-sitter 已有完整增量 parser、tree_edit、changed_ranges 与 Rust binding；受控缺口尚待构造，不声称发现上游缺陷。',
 ['lib/src/parser.c、tree.c 和必要 stack/绑定路径','提供能初始完整 parse 的 starter，再逐步恢复增量路径，避免完全无法解析的死起点'],
 '固定未改动版本作差分参考；每次编辑额外从头完整 parse，独立核对语法树、byte/point 与不变量。语法树一致不代表 changed_ranges 已正确，需单独检查。',
 ['初始 parse 保留','单次/多轮 edit','UTF-8/UTF-16 与 byte/point','changed_ranges 合同','错误恢复与节点生命周期'],
 ['普通插删之后处理多字节位置、跨节点 edit 与旧树复用','处理错误节点、连续编辑及 external scanner 状态恢复'],
 '每次从头 parse 可以轻易通过只查最终 AST 的 grader；先实现此基线，检查 changed-range/API 与合理工作量指标是否仍有真实缺口。',
 '用整树重解析 baseline 对照多轮 edit 与 changed_ranges；先冻结 grammar 及其真实生成文件，不靠代码行数推断难度。',
 ['性能计分若需要时间端点必须另实测，不能用树大小伪造速度','grammar 尚未完整冻结下载','公开 core 源码可能被直接复原，需跨状态组合而非单补函数'],
 [('lib/src/tree.c','void ts_tree_edit','公开编辑入口'),('lib/src/tree.c','TSRange *ts_tree_get_changed_ranges','changed range 计算'),('crates/cli/src/tests/parser_test.rs','fn test_parsing_after_editing_beginning','实际编辑回归素材')])
add('15_jq_composition','P2','源码 MIT 风格许可；COPYING 声明 docs 为 CC BY 3.0，不能把手册按 MIT 再分发。','git_rewrite_in_zig / libexpat_x86_assembly：行为兼容的重实现。',
 '在明确语言/进程内 API 合同下实现 JSON filter 引擎和 CLI，覆盖流式组合、词法作用域、递归、reduce/foreach、更新路径及错误前缀；按固定 jq 1.7.1 行为裁剪范围。',
 'jq 已有完整解释器和测试；旧 Python 小样的 84 个例子不足以覆盖组合语义。新增 profile 要重建语法/语义范围，不是随机重复旧例子。',
 ['parser→作用域/求值器→流/错误→CLI','可嵌入 API 必须为真实需求；不得临时设置语言限制仅用于阻止正常解法'],
 '隔离官方 jq 1.7.1，生成有类型/范围限制的 AST 组合，固定输入；结合变形关系与错误产生前的输出序列核对。非确定操作不纳入。',
 ['stream cardinality 与顺序','作用域/closure/递归','reduce/foreach','path update 与缺失/null','错误前缀、退出码及进程内 API'],
 ['简单 filter 后处理 binding 与 generator 多输出的乘积语义','处理递归/异常/更新路径在嵌套组合中的交互'],
 '直接调用现成 jq 或 libjq wrapper；若目标只是 CLI 兼容且环境/依赖允许，包装本来就是有效解，路线要换合同或淘汰，不能事后禁用。',
 '拿旧实现对新生成的有界 AST 组合做语义差分，同时测正常 libjq wrapper；先确认新增合同有实际缺口。',
 ['恢复上游可复制实现的记忆风险','完整 jq 范围过大，裁剪得太小又会早满','性能和语言约束必须有实际可嵌入场景依据'],
 [('tests/jq.test','try .a[] catch','多输出与错误组合'),('src/execute.c','case ON_BACKTRACK','真实回溯执行语义'),('COPYING','CC BY 3.0','文档与源码许可区分')],
 'samples/software-multiline-001/06_jq；旧参考 1 分是 host 行为小样，不是完整 jq 难度证据。')
add('16_libarchive_cli','P2','主体 BSD-2-Clause 风格；COPYING 明示个别文件和构建脚本多许可，不能只给一个总许可证。','git_rewrite_in_zig / cfzip_compression_engine：持久文件状态与 CLI/格式兼容。',
 '构造归档读写及 bsdtar 风格 CLI 的行为兼容任务：tar/pax、长路径/Unicode、链接/元数据、重复 -C 和分段流，按明确文件系统合同验证真实解包状态。',
 'libarchive 已能读写多格式流式归档，并带 tar/cpio/zcat；现有实现是参考，不应把给一个已可调用 libarchive 的 wrapper 当成新大工程。',
 ['可嵌入 reader/writer 与 CLI','明确支持格式、平台元数据、符号链接和路径策略，隔离临时目录；不以一次往返自证格式正确'],
 '固定 libarchive/bsdtar 作跨读写参考，同时独立检查成员内容、元数据和退出状态；只在格式规定范围比较字节，压缩时间戳/UID/locale 固定。',
 ['格式解析与写出互通','分段/截断流','长路径/PAX 元数据','链接及多 -C 的文件状态','错误与确定性'],
 ['普通文件之后实现 PAX/长路径和 hardlink/symlink 语义','解决前向流输入、截断、文件位置和部分成功的错误行为'],
 '系统 tar、libarchive 或现成 archive binding 可能充分解题；必须先按正常工具合同试包装。若已有库全覆盖，应淘汰这条实现题。',
 '先取固定格式的跨工具读写最小场景，并测现成 binding；再决定是兼容实现题还是已有能力包装题。',
 ['平台权限、mtime、顺序与路径行为需明示，不能跨平台盲目字节比较','压缩库和 fixture 的来源许可需单独收齐','成员数量/文件体积变大本身不构成长程'],
 [('README.md','streaming archives','实际流式格式/CLI 范围'),('libarchive/archive_read_support_format_tar.c','pax','真实 PAX 支持实现'),('tar/test/test_option_C_upper.c','DEFINE_TEST','真实多 -C 文件系统行为测试')])

FAMILY_NAMES={'engineering_evolution':'工程演进','system_implementation':'系统能力实现','correctness_constrained_performance':'正确性约束的性能优化','implementation_recovery':'跨层实现恢复','behavioral_reimplementation':'行为兼容重实现'}

def main():
 manifest=json.loads((ROOT/'source-manifests.json').read_text()); sources={x['id']:x for x in manifest['candidates']}
 plan=json.loads((ROOT/'plan.json').read_text()); plans={x['id']:x for x in plan['candidates']}
 cards=ROOT/'cards';cards.mkdir(exist_ok=True)
 index=[];missing=[]
 for d in D:
  s=sources[d['id']]; p=plans[d['id']];ev=[]
  for rel,needle,claim in d['evidence']:
   source=ROOT/'sources'/d['id']/'files'/rel
   lines=source.read_text(errors='replace').splitlines()
   hits=[i for i,line in enumerate(lines,1) if needle in line]
   if not hits: missing.append({'id':d['id'],'file':rel,'needle':needle});continue
   ev.append({'path':str(source.relative_to(ROOT)),'line':hits[0],'claim':claim,'url':f"https://github.com/{s['repo']}/blob/{s['revision']}/{rel}#L{hits[0]}"})
  c={**d,'family':p['family'],'title':p['title'],'new_source':p['new_source'],'repo':s['repo'],'revision':s['revision'],'readiness':'source_evidence_acquired_design_proposed','task_package_complete':False,'six_hour_difficulty_verified':False,'teacher_rollouts_started_for_this_profile':0,'constructor_model_run_for_this_batch':False,'evidence':ev,'source_manifest':f"sources/{d['id']}/manifest.json",'grading_status':'dimensions_proposed_not_frozen_no_scores_or_endpoints_measured'}
  index.append(c)
  lines=[f"# {d['id']}：{p['title']}",'',f"优先级：**{d['priority']}**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。",'',f"来源：[参照源码](https://github.com/{s['repo']}/tree/{s['revision']})；commit `{s['revision']}`。",'',f"许可观察：{d['license_observation']}",'',f"## 已有能力与拟出的题\n\n{d['existing_capability']}\n\n{d['proposed_task']}",'',f"原题类别参照：{d['edgebench_analogue']} 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。",'',"交付范围："]
  lines += [f'- {x}' for x in d['artifact_scope']]
  lines += ['',f"## 参考与迭代评分\n\n{d['reference_plan']}",'',"拟评分维度："]+[f'- {x}' for x in d['score_dimensions']]
  lines += ['',"评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。",'',"## 六小时潜力与第一道筛选\n\n以下是待验证的后续改进路径，不是时长估计："]+[f'- {x}' for x in d['post_two_hour_hypotheses']]
  lines += ['',f"最强廉价基线：{d['cheap_strong_baseline']}",'',f"先做的否证探针：{d['first_falsification_probe']}",'',"构造风险："]+[f'- {x}' for x in d['construction_risks']]
  lines += ['',"## 实际取得的源码证据",'']+[f"- [{x['claim']}]({x['url']})；本地 [`{x['path']}:{x['line']}`](../{x['path']})。" for x in ev]
  lines += ['',f"完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/{d['id']}/manifest.json)。[完整 Git 文件树索引](../sources/{d['id']}/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。",'']
  if d['previous_profile']: lines += ['旧 profile：'+d['previous_profile'],'']
  rendered=re.sub(r'([^\n])\n(?=- )',r'\1\n\n','\n'.join(lines)+'\n')
  (cards/(d['id']+'.md')).write_text(rendered)
 result={'batch':plan['batch'],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidates':index,'unresolved_evidence_anchors':missing,'counts':{'total':len(index),'new_projects':sum(c['new_source'] for c in index),'revised_existing_sources':sum(not c['new_source'] for c in index),'P1':sum(c['priority']=='P1' for c in index),'P2':sum(c['priority']=='P2' for c in index),'new_profiles_task_complete':0,'new_profile_6h_rollouts':0}}
 (ROOT/'candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 with (ROOT/'candidates.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['id','priority','family','title','repo','revision','new_source','proposed_task','readiness']);w.writeheader()
  for c in index:w.writerow({k:c[k] for k in w.fieldnames})
 print(json.dumps({'counts':result['counts'],'unresolved_evidence_anchors':missing},ensure_ascii=False))
if __name__=='__main__':main()
