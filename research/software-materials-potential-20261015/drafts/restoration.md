# M4 关联实现恢复：高难潜力定向复评

本组承接已积累的固定版本来源，从原生语义链进入作者拟构造的关联实现缺口。结论服务于50项整体选题排序；没有运行健康gold、制作starter、执行隐藏评分或求解实验。

**建议：A 5 项、B 4 项、C 1 项。** 优先做 Helix/Jinja 的强基线探针，再做 Pydantic Core/Tantivy/Nushell；Tokio/Rustls 上限高，但先解决可确定评分与toolchain，不能将其作者成本计为求解难度。

恢复题共同门槛：完整健康同版副本、wheel/二进制、生成缓存若可被直接调用或取回，所有恢复题都可能失去剩余工作。正常成熟依赖仍允许；这首先是starter/环境泄漏与数据污染检查，不是任意禁库。不同替代引擎需满足真实宿主的公开对象、callback、状态及生命周期契约，不比较私有布局。

A仅表示值得构造样题。随机删多个函数可能仍可逐段拼回，删得更多也可能只把工作量和破坏面转交作者控制；不按原项目规模、函数数量或删除量推断长程。必须先证实自然关联缺口在清晰宿主/公共API合同下仍留有多个里程碑，并以健康gold与最强普通替换/包装基线复核。

| 来源 | 分档 | 难度上限 | 作者成本 | 为什么这样排 |
|---|---|---|---|---|
| 37_tokio | B | high | high | transition_to_running/idle 同时改变通知位、运行位和引用计数：单独修 spawn 或 sleep 不足，取消后再次通知、poll 中唤醒、关闭时资源回收必须共同一致。但定时器与任务核之间的具体缺口闭包尚未选定，项目并发复杂不自动转成题目难度。 |
| 38_tantivy | A | high | high | 同一文档写入、提交发布、reader 世代与旧视图保留形成跨操作状态：正常查询通过以后，失败的提交不可泄漏、新旧视图同时合法、文件回收不能破坏读者。源码实际以 META_LOCK 保护 segment 打开，原生 failpoint 检查失败提交不暴露文档，提供自然剩余里程碑。 |
| 39_rustls | B | high | high | early data 的剩余长度、状态推进与记录对齐，以及多次连接共享 ticket store 的单次消费，都是单握手成功后仍存在的跨消息/连接状态。规范和互通层次很深，但收敛到可离线确定评价的宿主行为比模板/编辑/校验链成本高，且与原 TLS 类素材相近。 |
| 64_nushell | A | high | high | IR 调用须保存并恢复外层 scope_regions/PC，return 要在闭包边界吸收；typed table/list 经 each 与外部 stdin 往返说明数据形态和控制流相连。简单算术或单条管线成功后，嵌套作用域、字节流、异常后的调用者恢复仍是实质工作。 |
| 65_ruff | B | high | medium | 解析时 recovery_context 要保存恢复，嵌套 list 的终止 token、indent平衡与进展相互作用；正常合法语法通过后，错误输入仍要保留可消费 AST 和后续语句。此范围有高上限，但当前证据不足以确认关联缺口不会退化为小型 parser helper 修复，且与 Syn/M5 parser 素材机制重复。 |
| 66_syn | B | high | medium | fork 在不消费父流的同时隔离 unexpected 状态，expression atom 要区分 group/closure/path/macro/struct，且与items和括号/结合性相连。完整链可有高难上限，但若只是 fork 或运算符优先级，工作量很局部；需要通过真实宏消费者证明恢复范围。 |
| 67_petgraph | C | medium | low | 节点删除既清incident edges又将槽接回free list；原生测试核对其他索引保持、clear_edges后空槽复用。这些是不平凡不变量，但可由直白Vec<Option<_>>/邻接集合实现；现有范围缺乏必须跨很长工程链的证据。 |
| 68_jinja | A | high | medium | 继承会把parent blocks接入当前Context链，scoped block要派生上下文；super必须按当前block找到下一层。render基本成功后，动态parent、loop局部、宏回调、同步/异步生成和close/aclose仍共同约束同一运行时。状态都能通过渲染/回调/生成器观察，比Tokio/Rustls更易稳定评分。 |
| 69_helix | A | high | medium | ChangeSet组合负责docA→docB→docC，invert必须重建被删除Unicode文本；Selection按方向给anchor/head不同粘性，History存原选区与逆操作并跨LCA组合。一次编辑或线性undo成功后，选择区坐标与分支历史仍有实质剩余。纯core轨迹与代数不变量使评分比并发/密码协议更可控。 |
| 70_pydantic_core | A | high | high | smart union每个分支重设exactness/fields_set_count再恢复外层状态，按有效字段数和精确性选最佳模型；serializer又按确切类型/instance和model上下文走不同路径。验证成功不等于模型身份、序列化和下一次调用都正确，形成可观测跨表示链。其输入/输出确定性较强，但PyO3/Rust构建提高作者成本。 |

## 重点比较与待主验证

- Helix：纯core文档/选区/历史轨迹，可用代数不变量补充gold差分。优先验证snapshot+diff是否快速覆盖，避免只删compose一个算法。
- Jinja：动态继承、scoped/super、async调用都有直接测试支持，Python回调和生成器可确定观测。优先验证健康Jinja包装/缓存泄漏；不比较生成的Python源码。
- Pydantic Core：union分支上下文、返回实例身份和serializer策略是清晰语义链。健康Python/Rust/PyO3闭包未跑，成本比Jinja高。
- Tantivy：明确Manual reload与元数据失败注入可避免异步可见性假bug。旧searcher/文件回收/失败重开跨层，需要主核查具体mask闭包和全量重建基线。
- Nushell：当前eval_block实际转IR，不能删旧AST evaluator即称执行链缺损。typed Value/Stack/registered command宿主合同应自然地进入评分；仅stdout合同容易被nu子进程包装。
- Tokio/Rustls：原生状态强，但任务/记录状态只有在可控调度或pair对端下才好评分。不能以偶发并发失败、随机密文差异判错，先做健康harness。
- Ruff/Syn：具有完整语言解析链潜力，当前B。若实际仅helper/结合性修复应降C；两者任务族相似，优先选一个证明真实下游消费剩余工作，避免素材数等同独立任务族数。
- Petgraph：当前C，标准容器+稳定ID映射可能自然满足。先做最便宜否证，不为追求长程扩API或添加内部free-list检查。

请主报告交叉核查：Jinja编译block的close/aclose与Context super链；Helix selection affinity与history changes_since的共同宿主合同；Tantivy Manual reload说明与失败提交不可见测试。跨文件语义支持潜力，尚不证明具体starter仍有同样工作量。

## 实际阅读范围

本次是定向快评，不是全仓架构审计。下表仅记录实际请求过的行范围；不宣称达到repo-analyzer的全仓快速/标准覆盖阈值。读取的大文件局部低于30%时按该技能口径不计为“已读整文件”，也未伪造全仓有效代码分母。

| 候选 | 源文件 | 实际行区间 | 文件总行数 | 用途 |
|---|---|---|---|---|
| 37_tokio | sources/37_tokio/files/tokio/src/runtime/task/state.rs | 110–180 | 657 | implementation |
| 37_tokio | sources/37_tokio/files/tokio/tests/time_sleep.rs | 18–70 | 447 | test |
| 38_tantivy | sources/38_tantivy/files/src/reader/mod.rs | 1–80 | 318 | specification |
| 38_tantivy | sources/38_tantivy/files/src/reader/mod.rs | 180–250 | 318 | implementation |
| 38_tantivy | sources/38_tantivy/files/tests/failpoints/mod.rs | 42–105 | 124 | test |
| 39_rustls | sources/39_rustls/files/rustls/src/server/tls13.rs | 1240–1300 | 1752 | implementation |
| 39_rustls | sources/39_rustls/files/rustls-test/tests/api/resume.rs | 327–403 | 1624 | test |
| 64_nushell | sources/64_nushell/files/crates/nu-engine/src/eval_ir.rs | 40–130 | 2287 | implementation |
| 64_nushell | sources/64_nushell/files/crates/nu-engine/src/eval.rs | 630–680 | 1024 | implementation |
| 64_nushell | sources/64_nushell/files/tests/shell/pipeline/commands/internal.rs | 1–85 | 1085 | test |
| 64_nushell | sources/64_nushell/files/crates/nu-protocol/tests/test_pipeline_data.rs | 1–15 | 15 | test |
| 65_ruff | sources/65_ruff/files/crates/ruff_python_parser/src/parser/mod.rs | 710–810 | 1788 | implementation |
| 65_ruff | sources/65_ruff/files/crates/ruff_python_parser/src/parser/tests.rs | 350–405 | 543 | test |
| 65_ruff | sources/65_ruff/files/crates/ruff_python_parser/tests/fixtures.rs | 1–105 | 812 | test |
| 66_syn | sources/66_syn/files/src/parse.rs | 945–990 | 1420 | implementation |
| 66_syn | sources/66_syn/files/src/expr.rs | 1901–1965 | 4249 | implementation |
| 66_syn | sources/66_syn/files/tests/test_expr.rs | 770–825 | 1721 | test |
| 67_petgraph | sources/67_petgraph/files/crates/petgraph/src/graph_impl/stable_graph/mod.rs | 350–440 | 2643 | implementation |
| 67_petgraph | sources/67_petgraph/files/crates/petgraph/tests/stable_graph.rs | 30–112 | 1310 | test |
| 68_jinja | sources/68_jinja/files/src/jinja2/compiler.py | 945–1040 | 1992 | implementation |
| 68_jinja | sources/68_jinja/files/src/jinja2/runtime.py | 145–215 | 1062 | implementation |
| 68_jinja | sources/68_jinja/files/tests/test_inheritance.py | 148–215 | 410 | test |
| 68_jinja | sources/68_jinja/files/tests/test_async.py | 20–66 | 720 | test |
| 69_helix | sources/69_helix/files/helix-core/src/transaction.rs | 150–225 | 1186 | implementation |
| 69_helix | sources/69_helix/files/helix-core/src/transaction.rs | 312–375 | 1186 | implementation |
| 69_helix | sources/69_helix/files/helix-core/src/selection.rs | 470–520 | 1458 | implementation |
| 69_helix | sources/69_helix/files/helix-core/src/history.rs | 80–145 | 634 | implementation |
| 69_helix | sources/69_helix/files/helix-core/src/history.rs | 393–465 | 634 | test |
| 70_pydantic_core | sources/70_pydantic_core_current/files/pydantic-core/src/validators/union.rs | 90–200 | 431 | implementation |
| 70_pydantic_core | sources/70_pydantic_core_current/files/pydantic-core/tests/validators/test_union.py | 40–110 | 1426 | test |
| 70_pydantic_core | sources/70_pydantic_core_current/files/pydantic-core/src/serializers/type_serializers/model.rs | 110–200 | 298 | implementation |
| 70_pydantic_core | sources/70_pydantic_core_current/files/pydantic-core/tests/serializers/test_model.py | 1–105 | 1286 | test |

逐项完整字段见 [restoration.json](restoration.json)。原登记和源码素材只读，未调整原素材池的priority。
