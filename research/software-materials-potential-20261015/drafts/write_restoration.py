import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'software-materials-expansion-20261015'
OUT = Path(__file__).parent
CANDIDATES = {c['id']: c for c in json.loads((ROOT / 'candidates.json').read_text())['candidates']}
CONFIG = []

def add(id, tier, cost, scope, reason, shortcut, judge, milestones, probe, stop, reads, extra=None, potential='high'):
    c = CANDIDATES[id]
    read_scope = []
    evidence = []
    for p, a, b, kind in reads:
        path = Path(c['source_manifest']).parent / 'files' / p
        total = len((ROOT / path).read_text().splitlines())
        b = min(b, total)
        read_scope.append({'path': str(path), 'start': a, 'end': b, 'total_lines': total, 'kind': kind})
        for e in c['evidence']:
            if e['path'] == str(path) and a <= e['line'] <= b and e not in evidence:
                evidence.append(e)
    evidence.extend(extra or [])
    CONFIG.append(dict(id=id, tier=tier, potential=potential, authoring_cost=cost,
        recommended_scope=scope, difficulty_reason=reason, shortcut_risk=shortcut,
        judge_plan=judge, residual_milestones=milestones, first_probe=probe,
        stop_condition=stop, evidence=evidence,
        caveat='定向源码与原生测试选读支持语义潜力；健康 gold、缺损 starter、隐藏评分和求解试验均未完成，未证明长程难度。恢复范围是作者待构造的关联缺口，不是上游尚未实现的功能。公开上游源码的直接取回/整库替换是共同泄漏风险，不能靠任意禁用普通依赖来宣称题难。',
        read_scope=read_scope))
    # Persist each completed candidate immediately, keeping a valid JSON array.
    (OUT / 'restoration.json').write_text(json.dumps(CONFIG, ensure_ascii=False, indent=2) + '\n')

add('37_tokio','B','high',
    '保留 Runtime/Handle/JoinHandle、Future/Waker、计时 API 及健康 I/O，在宿主运行时中恢复任务通知/取消/引用所有权与计时器/关闭的关联生命周期；先只覆盖可确定观测的单线程与受控并发范围。',
    'transition_to_running/idle 同时改变通知位、运行位和引用计数：单独修 spawn 或 sleep 不足，取消后再次通知、poll 中唤醒、关闭时资源回收必须共同一致。但定时器与任务核之间的具体缺口闭包尚未选定，项目并发复杂不自动转成题目难度。',
    '锁式状态机、串行 scheduler、futures 工具是合法基线，可能覆盖有限合同。替代运行时薄包装还要保持宿主 Future/Waker、JoinHandle 取消与资源析构语义，不能只比较任务输出；但完整健康 Tokio 副本若在环境中可用可直接击穿，尚未排除。',
    '虚拟时间与手工 poll 控制轨迹，核对完成至多一次、JoinError/取消、唤醒后进展和 drop 计数；多线程只验证固定同步屏障下的不变量。选定 loom 检查须由健康参考先稳定通过，不匹配偶然调度顺序。阶段分任务/计时/关闭，再评交叉轨迹。',
    ['恢复基本 poll→通知→重新排队→join 的任务状态与所有权。','恢复 sleep/reset/取消及 shutdown 间的唤醒与资源释放，并使同一宿主任务流继续正常。'],
    '最便宜先在健康版本重复运行暂停时间+取消/析构轨迹，确认完全可控；接着以粗粒度锁/串行调度实现同一公开子集，检查是否很快全覆盖。',
    'gold 有偶发超时/依赖 wall-clock，或粗锁基线完整满足合同且剩余只有局部原子优化，则停止当前范围；不能靠吞吐门槛补难。',
    [('tokio/src/runtime/task/state.rs',110,180,'implementation'),('tokio/tests/time_sleep.rs',18,70,'test')])

add('38_tantivy','A','high',
    '在既有 schema/query/Directory 宿主中恢复 writer/segment 发布、删除可见性、显式 reader reload、旧 searcher 生命周期和提交失败后的重开；限定查询语言及排序并列合同。',
    '同一文档写入、提交发布、reader 世代与旧视图保留形成跨操作状态：正常查询通过以后，失败的提交不可泄漏、新旧视图同时合法、文件回收不能破坏读者。源码实际以 META_LOCK 保护 segment 打开，原生 failpoint 检查失败提交不暴露文档，提供自然剩余里程碑。',
    '全量重建/内存快照与成熟搜索库都允许，先作为强基线。它们仍要适配宿主 Directory、schema/collector、旧 Searcher 与失败发布行为；这是公开集成目标，不要求某种私有 segment 布局。若 snapshot+重建适配足额通过应降级，不能无依据增加性能门槛。完整原版可取回风险仍在。',
    'Manual reload+固定小文档集合，用独立查询/删除集合模型和健康版本差分；注入元数据保存失败、 reopen、保留旧 searcher，检查各视图与资源可用性。阶段分基础写查/提交删除/reload旧视图/失败恢复，不用提交后 sleep 等自动 reload。',
    ['恢复建索引、commit/delete 与 Manual reload 的文档可见性。','恢复失败发布后重开与继续写，保证旧 searcher 在新提交及 segment 生命周期变化后仍正确。'],
    '先用内存 Directory 在健康版本跑 A提交→旧searcher→B/删除→reload→save_metas失败→reopen 的纵向轨迹，再试全量重建+视图快照基线。',
    '强基线仅薄封装即可覆盖全部公开语义，或失败恢复无法离线稳定注入，停止当前缺口设计；若必须规定内部文件名/布局才能区分解法则重设。',
    [('src/reader/mod.rs',1,80,'specification'),('src/reader/mod.rs',180,250,'implementation'),('tests/failpoints/mod.rs',42,105,'test')],
    [{'path':'sources/38_tantivy/files/src/reader/mod.rs','line':198,'claim':'打开 segment 时取得 META_LOCK，避免 GC 在打开过程中移除文件。','url':'https://github.com/quickwit-oss/tantivy/blob/8a4cfc40f5b7446c0700471aa50290dbb7f8ea97/src/reader/mod.rs#L198'}])

add('39_rustls','B','high',
    '有限 TLS1.3 宿主连接公开 API：完整握手→ticket 消费/恢复→early/application data→部分 I/O 与关闭；保留可信 crypto provider、证书 fixtures，不恢复密码原语。',
    'early data 的剩余长度、状态推进与记录对齐，以及多次连接共享 ticket store 的单次消费，都是单握手成功后仍存在的跨消息/连接状态。规范和互通层次很深，但收敛到可离线确定评价的宿主行为比模板/编辑/校验链成本高，且与原 TLS 类素材相近。',
    '正常 TLS 库和 crypto provider 应允许；成熟 TLS 适配有机会覆盖线上协议，却还需匹配宿主 Rust 配置/证书回调、ticket store、非阻塞部分 I/O 和错误 API。不能未经试验证明不可薄包装；同版完整 rustls 副本尤其可直接覆盖。',
    '固定证书、可控输入分片和 provider，在内存 client/server pair 与独立对端间核对握手类型、ticket 使用、early-data拒绝/接受、应用字节与关闭错误；不逐字节匹配含随机性的密文。阶段分完整握手/恢复/early data/部分 I/O 与关闭。',
    ['恢复完整 TLS1.3 连接及应用读写，与保留 provider 和宿主 API 协同。','恢复共享 store 的 ticket 消费、early-data 长度/次序与分片输入，再闭合错误和 close 生命周期。'],
    '先离线编译健康 provider 并运行现有 ticket 不复用 pair 测试；加入自拟分片/close轨迹，做成熟 TLS API 适配成本试验。',
    '确定性 harness 无法构建、重复已有 TLS 任务而无新契约，或成熟 TLS 适配直接通过，停止当前方向；不得把密码构建/证书排障耗时算求解难度。',
    [('rustls/src/server/tls13.rs',1240,1300,'implementation'),('rustls-test/tests/api/resume.rs',327,403,'test')])

add('64_nushell','A','high',
    '保留词法/AST/IR 编译、命令注册及 typed Value/Stack 公共 API，恢复 IR 执行、PipelineData 流转与闭包/自定义命令 return/scope 边界；只引入固定离线 testbin，不扩成 shell 全量重写。',
    'IR 调用须保存并恢复外层 scope_regions/PC，return 要在闭包边界吸收；typed table/list 经 each 与外部 stdin 往返说明数据形态和控制流相连。简单算术或单条管线成功后，嵌套作用域、字节流、异常后的调用者恢复仍是实质工作。',
    '旧 AST evaluator/健康 nu 子进程是必须试的强基线。字符串 subprocess 无法直接携带宿主 Value/Span、Stack、已注册 Rust 命令和流错误/资源状态，适配可能实质复杂；但若合同只比终端 stdout 即容易被包装击穿。不得为卡基线引入私有 IR 字节布局，完整同版引擎替换风险仍在。',
    '健康固定 workspace API/脚本差分，独立核对类型、span/metadata、闭包 return边界、宿主回调副作用和下一次执行的变量/错误状态。固定 testbin 显式控制 stdin/stdout；阶段分值管线/闭包/外部流/错误后恢复，不依赖 shell 环境。',
    ['恢复 typed 值、table/list 与嵌套 each/custom command 在 IR 下的管线传递。','恢复 return/error/finally 边界和 caller scope/PC，再打通外部字节流及提前终止后的清理。'],
    '先健康构建并跑结构化each→固定testbin→结果访问和return后调用者继续两条纵向轨迹；再检查旧evaluator/nu subprocess能否携带宿主数据与注册命令完成。',
    '旧 evaluator 或几个转发调用已完整覆盖，或缺口导致parser/无关命令不可起步，则停止当前缺口；若依赖不确定外部程序而难稳定评分也先缩退。',
    [('crates/nu-engine/src/eval_ir.rs',40,130,'implementation'),('crates/nu-engine/src/eval.rs',630,680,'implementation'),('tests/shell/pipeline/commands/internal.rs',1,85,'test'),('crates/nu-protocol/tests/test_pipeline_data.rs',1,15,'test')])

add('65_ruff','B','medium',
    '只在固定 Python 版本/功能集中恢复 token→表达式/statement suites→recoverable AST/ranges→既有 formatter/linter 消费链；不得仅删除 list helper 或优先级表再称长程。',
    '解析时 recovery_context 要保存恢复，嵌套 list 的终止 token、indent平衡与进展相互作用；正常合法语法通过后，错误输入仍要保留可消费 AST 和后续语句。此范围有高上限，但当前证据不足以确认关联缺口不会退化为小型 parser helper 修复，且与 Syn/M5 parser 素材机制重复。',
    'CPython ast/其它 Rust Python parser 是合法基线；合法子集+AST映射可能覆盖大半。恢复诊断、Ruff typed AST/ranges 及下游消费不自然等价于标准AST，但差异必须由公开输入/行为而非私有快照证明。同版 parser crate 或完整原版替换可击穿。',
    '固定健康 Ruff 的 API 差分，分别检查合法 AST/ranges、recoverable错误后的语句/诊断位置和下游格式化/规则结果；CPython只作为共同合法子集参考。阶段分合法表达式/语句组合/错误恢复/下游闭合，避免精确匹配不承诺的错误文案。',
    ['恢复合法表达式与 statement/suite 的组合、优先级和源码范围。','恢复嵌套错误进展/终止及后续语句可用性，使formatter/linter能消费公开承诺的部分树。'],
    '先跑健康版本自拟合法+损坏语法工作流，再做CPython/替代parser到目标AST的适配；实际挖除前看剩余是否超过局部list helper。',
    '替代parser薄适配完成合同，或缺口只剩少数恢复helper/一个语法点，降 C 并重设；若健康版本不承诺下游接受错误树，不将该行为加入评分。',
    [('crates/ruff_python_parser/src/parser/mod.rs',710,810,'implementation'),('crates/ruff_python_parser/src/parser/tests.rs',350,405,'test'),('crates/ruff_python_parser/tests/fixtures.rs',1,105,'test')])

add('66_syn','B','medium',
    '保留 proc_macro2、AST类型和打印器/visitor，恢复 ParseBuffer 消费/分叉与 Expr/Item 递归调用的连贯子集，交付真实proc-macro消费者能使用的 tokens→AST→print/visit→Rust编译链；只做语法，不要求rustc语义分析。',
    'fork 在不消费父流的同时隔离 unexpected 状态，expression atom 要区分 group/closure/path/macro/struct，且与items和括号/结合性相连。完整链可有高难上限，但若只是 fork 或运算符优先级，工作量很局部；需要通过真实宏消费者证明恢复范围。',
    '另一个Rust parser、quote/proc_macro2及现存健康syn依赖合法。替代parser往往不是同一TokenStream/group/span/AST类型，适配可能多阶段，但不能据此排除薄适配；完整同版syn副本直接能覆盖，残留健康版本必须检查为出题泄漏。',
    '健康固定syn的AST/print差分，加 parse-print-parse结构不变量和小型proc-macro消费者编译；合法语法与span合同明确分开，不比较不承诺的错误字符串。阶段分表达式/Items嵌套/分叉失败/宏消费；feature flags固定。',
    ['恢复分叉不消费父流及表达式/Item/宏token边界的正确解析。','恢复嵌套组合、括号和跨度，使打印/visitor及真实宏消费者保持类型一致并编译。'],
    '先健康版本跑同一proc-macro小工作流，尝试替代parser映射；若恢复只改fork/precedence或现有完整parser转发即可，立即缩退。',
    '只剩局部语法修复、缺乏真实消费者的剩余工作，或与Ruff恢复题高度同构且无新能力信号，则降C重设；不要通过随意增加Rust语法点凑时长。',
    [('src/parse.rs',945,990,'implementation'),('src/expr.rs',1901,1965,'implementation'),('tests/test_expr.rs',770,825,'test')])

add('67_petgraph','C','low',
    '当前只保留为可变图稳定索引练习素材；若再立项，需以真实增删→遍历/算法→含空洞序列化→继续增删的宿主工作流自然扩展，而非扩大API数量。',
    '节点删除既清incident edges又将槽接回free list；原生测试核对其他索引保持、clear_edges后空槽复用。这些是不平凡不变量，但可由直白Vec<Option<_>>/邻接集合实现；现有范围缺乏必须跨很长工程链的证据。',
    '标准容器重建与现有Graph wrapper风险高，完整算法模块可保留调用。稳定外部索引可通过映射表实现；不能要求内部free-list布局/遍历偶然顺序来挡简单方案。成熟图库及全量重算应允许。',
    '独立节点/边集合模型生成操作轨迹，健康petgraph差分核对索引、双向邻接、自环/并行边、holes与序列化后继续操作；算法比较集合/路径合法性，不比较未承诺的遍历顺序。',
    ['恢复稳定索引下增删及自环/并行边的双向邻接一致。','恢复空洞序列化和visitor索引域，再让保留算法在后续mutation后继续正确。'],
    '先用简单标准容器或Graph+稳定ID映射实现同一操作轨迹；这是最便宜的高难否证，优先于制作复杂缺损starter。',
    '若简单基线覆盖全部行为即停止高难方向；只有真实公开工作负载证明现有方案的剩余缺口才能重开，不无依据追加性能限制。',
    [('crates/petgraph/src/graph_impl/stable_graph/mod.rs',350,440,'implementation'),('crates/petgraph/tests/stable_graph.rs',30,112,'test')],potential='medium')

add('68_jinja','A','medium',
    '保留lexer/AST/loader及Environment/Template公开API，关联恢复继承/block/super/scoped/include的编译与Context调用，再闭合同一多模板工作流的macro/async/escape及generator关闭。',
    '继承会把parent blocks接入当前Context链，scoped block要派生上下文；super必须按当前block找到下一层。render基本成功后，动态parent、loop局部、宏回调、同步/异步生成和close/aclose仍共同约束同一运行时。状态都能通过渲染/回调/生成器观察，比Tokio/Rustls更易稳定评分。',
    'MarkupSafe、Python AST/codegen、async工具允许。替代引擎要支持宿主loader、context-aware Python callbacks、Template/Undefined/Markup及async generator API，难以仅字符串转发；但包装健康Jinja同版本可能直接成功，需在基线探针实查。不要匹配私有生成Python文本或禁用正常库来防包装。',
    '固定健康Jinja差分render/generate/render_async/generate_async，独立检查loader调用、context回调观测、转义、yield后异常与close/aclose清理。以可控async函数替代网络I/O；阶段分继承/上下文宏/escape异步/生命周期，不比较私有codegen文本。',
    ['恢复多级继承、动态parent、scoped locals与super链的共享Context。','恢复macro/include/import上下文隔离，并使同一模板同步/异步流式输出、escape与终止清理保持一致。'],
    '健康Python环境先跑dynamic extends+scoped super、async macro两条纵向轨迹；尝试现存健康引擎/替代引擎保留宿主callbacks的最薄包装。',
    '环境中健康引擎/旧编译缓存可直接覆盖，或关联缺口只剩几个compiler visitor，即停止当前mask；若async关闭无稳定公开可观察行为则缩减评分，不推测资源泄漏。',
    [('src/jinja2/compiler.py',945,1040,'implementation'),('src/jinja2/runtime.py',145,215,'implementation'),('tests/test_inheritance.py',148,215,'test'),('tests/test_async.py',20,66,'test')])

add('69_helix','A','medium',
    '仅纯helix-core：保留Rope和编辑动作壳，恢复ChangeSet compose/invert/apply、Selection anchor/head affinity映射以及History分支/changes_since/undo-redo，交付Unicode多选择区编辑内核；不含GUI/LSP/grammar。',
    'ChangeSet组合负责docA→docB→docC，invert必须重建被删除Unicode文本；Selection按方向给anchor/head不同粘性，History存原选区与逆操作并跨LCA组合。一次编辑或线性undo成功后，选择区坐标与分支历史仍有实质剩余。纯core轨迹与代数不变量使评分比并发/密码协议更可控。',
    'Ropey、标准diff和完整文档快照式历史都是合法强基线。快照足以恢复文本，但要在宿主Transaction/Selection接口上保留坐标映射、分支changes_since和多选择区语义仍需适配；必须实际试验，不能凭内部实现推断难度。完整健康core替换依旧能击穿。',
    '健康固定core的操作轨迹差分与独立文本/选择区模型，验证compose与顺序apply等价、invert恢复、undo-redo及跨分支文档/选区。Unicode用明确字符坐标，受控timestamp；不评上游未实现的ChangeSet::map，不要求私有操作规范化布局。',
    ['恢复单次/复合编辑、Unicode反演和方向相关选择区映射。','恢复undo后分叉、分支间changes_since/LCA组合与原选区恢复，并检验空事务和多次执行。'],
    '健康core跑中文/emoji多选择区→复合编辑→undo→分支→changes_since；以snapshot+标准diff为强基线，看是否只需薄API映射即可完成。',
    '快照/diff适配直接足额覆盖，或缺口只剩compose单算法则重设；任何测试依赖ChangeSet::map TODO、GUI时序或未承诺的操作布局则删除该测试/暂停。',
    [('helix-core/src/transaction.rs',150,225,'implementation'),('helix-core/src/transaction.rs',312,375,'implementation'),('helix-core/src/selection.rs',470,520,'implementation'),('helix-core/src/history.rs',80,145,'implementation'),('helix-core/src/history.rs',393,465,'test')])

add('70_pydantic_core','A','high',
    '主仓pydantic-core子项目中保留Python SchemaValidator/SchemaSerializer/core_schema API及基础类型，关联恢复schema编译→strict/lax/JSON-Python校验→smart union模型选择→模型身份/结构化错误→serializer字段策略；冻结有限schema功能集。',
    'smart union每个分支重设exactness/fields_set_count再恢复外层状态，按有效字段数和精确性选最佳模型；serializer又按确切类型/instance和model上下文走不同路径。验证成功不等于模型身份、序列化和下一次调用都正确，形成可观测跨表示链。其输入/输出确定性较强，但PyO3/Rust构建提高作者成本。',
    'JSON Schema/其它校验库、Rust/Python数据工具允许。它们不天然保持宿主Python模型实例身份、自定义回调、strict/lax精确选择及序列化策略，需要实质适配；但同版pydantic_core wheel或完整引擎可直接覆盖，先检查依赖闭包，不能任意禁成熟校验器来抬难度。',
    '健康固定核心差分validate_python/validate_json与SchemaSerializer to_python/to_json；独立核对返回类型/身份、嵌套error locations、回调副作用、bytes/JSON模式及跨调用隔离。阶段分基础schema/嵌套union模型/错误状态恢复/序列化闭合，不依赖私有repr。',
    ['恢复嵌套schema与多分支校验，保留strict/lax/JSON-Python选择、实例身份和结构化错误。','恢复同一模型的serializer配置/字段策略，并在union失败与重复调用后保持验证/序列化上下文隔离。'],
    '先匹配Python/Rust/PyO3离线健康构建，跑模型union身份保持→序列化bytes/JSON的纵向轨迹；再用最强普通校验库适配同一合同，检查wheel/健康副本泄漏。',
    '健康wheel/残余完整引擎薄包装可通过、缺口只剩union比较器，或工具链无法稳定复现则停止当前mask；不能把Rust/Python构建排障计成高难。',
    [('pydantic-core/src/validators/union.rs',90,200,'implementation'),('pydantic-core/tests/validators/test_union.py',40,110,'test'),('pydantic-core/src/serializers/type_serializers/model.rs',110,200,'implementation'),('pydantic-core/tests/serializers/test_model.py',1,105,'test')],
    [{'path':'sources/70_pydantic_core_current/files/pydantic-core/src/serializers/type_serializers/model.rs','line':142,'claim':'模型serializer按exact type/instance检查兼容性，并以scoped model状态调用嵌套serializer。','url':'https://github.com/pydantic/pydantic/blob/8cd3bec6c7e1d360d92193841613465d30f63955/pydantic-core/src/serializers/type_serializers/model.rs#L142'},
     {'path':'sources/70_pydantic_core_current/files/pydantic-core/tests/serializers/test_model.py','line':39,'claim':'原生测试区分Python/JSON模式，对基础模型与子类的bytes字段序列化作明确断言。','url':'https://github.com/pydantic/pydantic/blob/8cd3bec6c7e1d360d92193841613465d30f63955/pydantic-core/tests/serializers/test_model.py#L39'}])

lines = ['# M4 关联实现恢复：高难潜力定向复评', '',
    '本组承接已积累的固定版本来源，从原生语义链进入作者拟构造的关联实现缺口。结论服务于50项整体选题排序；没有运行健康gold、制作starter、执行隐藏评分或求解实验。', '',
    '**建议：A 5 项、B 4 项、C 1 项。** 优先做 Helix/Jinja 的强基线探针，再做 Pydantic Core/Tantivy/Nushell；Tokio/Rustls 上限高，但先解决可确定评分与toolchain，不能将其作者成本计为求解难度。', '',
    '恢复题共同门槛：完整健康同版副本、wheel/二进制、生成缓存若可被直接调用或取回，所有恢复题都可能失去剩余工作。正常成熟依赖仍允许；这首先是starter/环境泄漏与数据污染检查，不是任意禁库。不同替代引擎需满足真实宿主的公开对象、callback、状态及生命周期契约，不比较私有布局。', '',
    'A仅表示值得构造样题。随机删多个函数可能仍可逐段拼回，删得更多也可能只把工作量和破坏面转交作者控制；不按原项目规模、函数数量或删除量推断长程。必须先证实自然关联缺口在清晰宿主/公共API合同下仍留有多个里程碑，并以健康gold与最强普通替换/包装基线复核。', '',
    '| 来源 | 分档 | 难度上限 | 作者成本 | 为什么这样排 |', '|---|---|---|---|---|']
for c in CONFIG:
    lines.append(f"| {c['id']} | {c['tier']} | {c['potential']} | {c['authoring_cost']} | {c['difficulty_reason']} |")
lines += ['', '## 重点比较与待主验证', '',
    '- Helix：纯core文档/选区/历史轨迹，可用代数不变量补充gold差分。优先验证snapshot+diff是否快速覆盖，避免只删compose一个算法。',
    '- Jinja：动态继承、scoped/super、async调用都有直接测试支持，Python回调和生成器可确定观测。优先验证健康Jinja包装/缓存泄漏；不比较生成的Python源码。',
    '- Pydantic Core：union分支上下文、返回实例身份和serializer策略是清晰语义链。健康Python/Rust/PyO3闭包未跑，成本比Jinja高。',
    '- Tantivy：明确Manual reload与元数据失败注入可避免异步可见性假bug。旧searcher/文件回收/失败重开跨层，需要主核查具体mask闭包和全量重建基线。',
    '- Nushell：当前eval_block实际转IR，不能删旧AST evaluator即称执行链缺损。typed Value/Stack/registered command宿主合同应自然地进入评分；仅stdout合同容易被nu子进程包装。',
    '- Tokio/Rustls：原生状态强，但任务/记录状态只有在可控调度或pair对端下才好评分。不能以偶发并发失败、随机密文差异判错，先做健康harness。',
    '- Ruff/Syn：具有完整语言解析链潜力，当前B。若实际仅helper/结合性修复应降C；两者任务族相似，优先选一个证明真实下游消费剩余工作，避免素材数等同独立任务族数。',
    '- Petgraph：当前C，标准容器+稳定ID映射可能自然满足。先做最便宜否证，不为追求长程扩API或添加内部free-list检查。', '',
    '请主报告交叉核查：Jinja编译block的close/aclose与Context super链；Helix selection affinity与history changes_since的共同宿主合同；Tantivy Manual reload说明与失败提交不可见测试。跨文件语义支持潜力，尚不证明具体starter仍有同样工作量。', '',
    '## 实际阅读范围', '',
    '本次是定向快评，不是全仓架构审计。下表仅记录实际请求过的行范围；不宣称达到repo-analyzer的全仓快速/标准覆盖阈值。读取的大文件局部低于30%时按该技能口径不计为“已读整文件”，也未伪造全仓有效代码分母。', '',
    '| 候选 | 源文件 | 实际行区间 | 文件总行数 | 用途 |', '|---|---|---|---|---|']
for c in CONFIG:
    for r in c['read_scope']:
        lines.append(f"| {c['id']} | {r['path']} | {r['start']}–{r['end']} | {r['total_lines']} | {r['kind']} |")
lines += ['', '逐项完整字段见 [restoration.json](restoration.json)。原登记和源码素材只读，未调整原素材池的priority。', '']
(OUT / 'restoration.md').write_text('\n'.join(lines))
