# 软件工程出题素材：50 项总目录

调研日期：2026-10-15。本批从原有 15 项扩充至 50 项，新增 35 个主仓库。

目录序号 1–50 用于浏览；素材 ID 沿用此前登记的 28–77。每行素材卡包含已有能力、拟交付范围、端到端场景、正常基线、首个否证探针、独立判据、许可和离线风险；固定源码链接到本次保存的 commit。

初筛：**23 项先验证范围，27 项暂缓并优先排查基线或工具链**。所有范围均为研究假设，尚未构题或验证长程难度。五类各 10 项用于扩展覆盖，不代表原题比例或正式出题配额。

[调研报告](REPORT.md) · [CSV](candidates.csv) · [JSON](candidates.json) · [完整性检查](inventory-check.json)

## M1 产品演进：交付完整产品里程碑

| 序号 | 来源与证据 | 可细化的交付方向 | 初筛 |
|---|---|---|---|
| 1 | [sqlalchemy/alembic](https://github.com/sqlalchemy/alembic/tree/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd) · [素材卡](cards/28_alembic.md) | 显式重命名意图驱动的数据库重构迁移版本 | 先验证范围 |
| 2 | [sphinx-doc/sphinx](https://github.com/sphinx-doc/sphinx/tree/b04a2101295ac3fb725b16111eda0284b6da4cca) · [素材卡](cards/29_sphinx.md) | 基于内容指纹的可解释文档增量构建模式 | 暂缓，先排查现有能力 |
| 3 | [mitmproxy/mitmproxy](https://github.com/mitmproxy/mitmproxy/tree/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b) · [素材卡](cards/30_mitmproxy.md) | 会话隔离与动态关联的离线 HTTP 工作流回放版本 | 先验证范围 |
| 16 | [tox-dev/tox](https://github.com/tox-dev/tox/tree/d947dd4e43388f727bb534c3f0ad7997d76b4767) · [素材卡](cards/43_tox.md) | 带资源租约与可恢复执行记录的测试矩阵版本 | 先验证范围 |
| 17 | [pypa/hatch](https://github.com/pypa/hatch/tree/ac9c0c9544795b380c2a5f63f80c1f46db3c5d4c) · [素材卡](cards/44_hatch.md) | 可移动的离线多环境交付包与安装审计 | 暂缓，先排查现有能力 |
| 18 | [celery/celery](https://github.com/celery/celery/tree/4b7a3652e3297730c0e018ce3038e0121de983bc) · [素材卡](cards/45_celery.md) | 可审计的工作流取消与补偿执行契约 | 暂缓，先排查现有能力 |
| 19 | [fastify/fastify](https://github.com/fastify/fastify/tree/37df44a421817e7bb048fce834bf691abb0999d6) · [素材卡](cards/46_fastify.md) | 带插件作用域预算与资源清理的请求执行策略 | 暂缓，先排查现有能力 |
| 20 | [go-task/task](https://github.com/go-task/task/tree/ad2782e1709f0bcf8fbbe0d8e00c2d239141e099) · [素材卡](cards/47_task.md) | 声明式任务的本地内容寻址工件缓存 | 先验证范围 |
| 21 | [apache/apisix](https://github.com/apache/apisix/tree/64a4afdd1353bd302f03cc8f0f780b8a78176137) · [素材卡](cards/48_apisix.md) | Standalone 配置包的预检、分阶段激活与回退 | 先验证范围 |
| 22 | [dbt-labs/dbt](https://github.com/dbt-labs/dbt/tree/8843d3dfca9a2ea2646a6273701a89ffffd4b11e) · [素材卡](cards/49_dbt.md) | 可离线重放的模型选择与 defer 影响审查包 | 暂缓，先排查现有能力 |

## M2 系统能力：规格驱动的完整子系统

| 序号 | 来源与证据 | 可细化的交付方向 | 初筛 |
|---|---|---|---|
| 4 | [eclipse-mosquitto/mosquitto](https://github.com/eclipse-mosquitto/mosquitto/tree/83f2620f0b955b89aadce32cceb96a8e81950f5e) · [素材卡](cards/31_mosquitto.md) | 持久会话与消息投递引擎 | 先验证范围 |
| 5 | [p4lang/behavioral-model](https://github.com/p4lang/behavioral-model/tree/7f4e1daca12b7fe52897687764b7e74ded7dab55) · [素材卡](cards/32_bmv2.md) | 编译后包处理程序执行系统 | 先验证范围 |
| 6 | [apache/avro](https://github.com/apache/avro/tree/3a207fa6e87c535b95eafca4cf5a6ef524d77df2) · [素材卡](cards/33_avro.md) | 带 schema 演进的跨实现数据文件系统 | 暂缓，先排查现有能力 |
| 23 | [apache/thrift](https://github.com/apache/thrift/tree/f4d8e8c3fa56ef04d7462e26d3b8226127edb2fe) · [素材卡](cards/50_thrift.md) | IDL 多文件语义前端与反射输出恢复 | 先验证范围 |
| 24 | [capnproto/capnproto](https://github.com/capnproto/capnproto/tree/b5ee48b9f3586fc83af8c429623e2c0d2435ec59) · [素材卡](cards/51_capnproto.md) | 运行时 Schema 加载、演进与动态访问恢复 | 先验证范围 |
| 25 | [SanderMertens/flecs](https://github.com/SanderMertens/flecs/tree/cc2924199858433cbf9fdaca25b291883ebd09de) · [素材卡](cards/52_flecs.md) | 延迟世界修改、观察者与查询缓存一致性恢复 | 先验证范围 |
| 26 | [nats-io/nats-server](https://github.com/nats-io/nats-server/tree/b55d969381aa05a7a59c563797b454d1b6b5fa37) · [素材卡](cards/53_nats.md) | 持久消息流与消费者重放系统 | 先验证范围 |
| 27 | [graphql/graphql-js](https://github.com/graphql/graphql-js/tree/e35a025d6e947ed2db0c1378e130f2bd0438732c) · [素材卡](cards/54_graphql.md) | 带异步解析器与订阅的 GraphQL 执行系统 | 暂缓，先排查现有能力 |
| 28 | [cel-expr/cel-go](https://github.com/cel-expr/cel-go/tree/5dcc82d6016cbe8ce7aef7b027538c42ed31c2d6) · [素材卡](cards/55_cel_go.md) | 类型检查与可复用执行计划的 CEL 表达式系统 | 暂缓，先排查现有能力 |
| 29 | [google/flatbuffers](https://github.com/google/flatbuffers/tree/b8431fbcd7a5c71817f314e18b332c0648554efa) · [素材卡](cards/56_flatbuffers.md) | schema 驱动的零拷贝二进制数据系统 | 暂缓，先排查现有能力 |

## M3 性能优化：保持正确性的资源取舍

| 序号 | 来源与证据 | 可细化的交付方向 | 初筛 |
|---|---|---|---|
| 7 | [duckdb/duckdb](https://github.com/duckdb/duckdb/tree/dda2e4090494101087e7726581928e6af44dbc34) · [素材卡](cards/34_duckdb.md) | 受限内存下分组聚合的吞吐与资源效率 | 待强性能基线 |
| 8 | [simdjson/simdjson](https://github.com/simdjson/simdjson/tree/9c003534b1be3bc4f1322bfa7a770a7ffbf247d9) · [素材卡](cards/35_simdjson.md) | 严格语义下的混合 JSON 流处理效率 | 待强性能基线 |
| 9 | [libvips/libvips](https://github.com/libvips/libvips/tree/06564b0a4c3f473d0e0cb9f9977ab647888aa43d) · [素材卡](cards/36_libvips.md) | 图像缩略处理流水线的资源与吞吐优化 | 待强性能基线 |
| 30 | [lz4/lz4](https://github.com/lz4/lz4/tree/48bfbfe351c5d6ea87d4af5557705e87755844e0) · [素材卡](cards/57_lz4.md) | LZ4 流式无损编解码的速度、压缩率与内存取舍 | 待强性能基线 |
| 31 | [apache/lucene](https://github.com/apache/lucene/tree/8476457b8752be2fd8094eaf5cd9bf0cea9594ae) · [素材卡](cards/58_lucene.md) | Lucene 混合布尔检索的正确 top-k 与尾延迟 | 待强性能基线 |
| 32 | [google/re2](https://github.com/google/re2/tree/2da0056814cf180480a19f5cf811e7e1c054bf6d) · [素材卡](cards/59_re2.md) | RE2 受限缓存下批量正则匹配与捕获 | 待强性能基线 |
| 33 | [fastfloat/fast_float](https://github.com/fastfloat/fast_float/tree/166d2b3df29cf8101bb715bde2125610881df791) · [素材卡](cards/60_fast_float.md) | 正确舍入十进制数值解析的批量吞吐 | 待强性能基线 |
| 34 | [libjxl/libjxl](https://github.com/libjxl/libjxl/tree/ef67fde2ec16d52e644c5a0969230b9a85e3eb31) · [素材卡](cards/61_libjxl.md) | JPEG XL 无损 Modular 编码的压缩率与资源效率 | 待强性能基线 |
| 35 | [LMDB/lmdb](https://github.com/LMDB/lmdb/tree/253ba5219172531b719bc14fee6b4aa1a2a5c4a5) · [素材卡](cards/62_lmdb.md) | LMDB 快照读与持久事务写的页复用效率 | 待强性能基线 |
| 36 | [uxlfoundation/oneTBB](https://github.com/uxlfoundation/oneTBB/tree/885b7813d38de698a9942e5026ad1bd9d16125d9) · [素材卡](cards/63_onetbb.md) | oneTBB 多 arena 嵌套任务的调度效率 | 待强性能基线 |

## M4 实现恢复：恢复关联实现与生命周期

| 序号 | 来源与证据 | 可细化的交付方向 | 初筛 |
|---|---|---|---|
| 10 | [tokio-rs/tokio](https://github.com/tokio-rs/tokio/tree/52ac7816230efabcae6fcc09cbe7ae630a48eddf) · [素材卡](cards/37_tokio.md) | 异步运行时的任务、计时器与关闭生命周期恢复 | 待可重复判据 |
| 11 | [quickwit-oss/tantivy](https://github.com/quickwit-oss/tantivy/tree/8a4cfc40f5b7446c0700471aa50290dbb7f8ea97) · [素材卡](cards/38_tantivy.md) | 全文索引的写入、提交、读视图与失败恢复 | 先验证范围 |
| 12 | [rustls/rustls](https://github.com/rustls/rustls/tree/d37c3c338fe30c3fdc70f0696997909ffd15f5b8) · [素材卡](cards/39_rustls.md) | TLS记录、握手恢复与应用I/O的关联状态恢复 | 待可重复判据 |
| 37 | [nushell/nushell](https://github.com/nushell/nushell/tree/6a4027ff14d55c2a274faa2c53e74ae9921af9a2) · [素材卡](cards/64_nushell.md) | 结构化管线与闭包执行链恢复 | 先验证范围 |
| 38 | [astral-sh/ruff](https://github.com/astral-sh/ruff/tree/3514027edb659bbc3c787d355be9d130e5587f15) · [素材卡](cards/65_ruff.md) | Python 解析、恢复与源码范围链恢复 | 先验证范围 |
| 39 | [dtolnay/syn](https://github.com/dtolnay/syn/tree/7c44a5565b4421035101cc16184e9af08ab5fc77) · [素材卡](cards/66_syn.md) | Rust token-stream 到语法树的解析链恢复 | 先验证范围 |
| 40 | [petgraph/petgraph](https://github.com/petgraph/petgraph/tree/b3eaf3a73f3ac7347b17bec3ba009f01eb8d2495) · [素材卡](cards/67_petgraph.md) | 稳定索引可变图存储与遍历恢复 | 暂缓，先排查现有能力 |
| 41 | [pallets/jinja](https://github.com/pallets/jinja/tree/5ef70112a1ff19c05324ff889dd30405b1002044) · [素材卡](cards/68_jinja.md) | 模板继承、作用域与异步执行链恢复 | 先验证范围 |
| 42 | [helix-editor/helix](https://github.com/helix-editor/helix/tree/ba40e547426b0f9896c8bdc699a4ab11f2b37dbc) · [素材卡](cards/69_helix.md) | 多选择区编辑事务与分支历史恢复 | 先验证范围 |
| 43 | [pydantic/pydantic](https://github.com/pydantic/pydantic/tree/8cd3bec6c7e1d360d92193841613465d30f63955) · [素材卡](cards/70_pydantic_core.md) | 类型校验、联合分支和模型序列化的关联恢复 | 先验证范围 |

## M5 行为兼容：重实现可观察工作流

| 序号 | 来源与证据 | 可细化的交付方向 | 初筛 |
|---|---|---|---|
| 13 | [RsyncProject/rsync](https://github.com/RsyncProject/rsync/tree/b70a61f394d0d4c71ee349a9260b4ed8babbb6be) · [素材卡](cards/40_rsync.md) | 目录同步工具的过滤、链接、更新与多步状态兼容 | 先验证范围 |
| 14 | [curl/curl](https://github.com/curl/curl/tree/03f3f4c6d97be3c2c9ad42010f65e61bf0a2c05c) · [素材卡](cards/41_curl.md) | HTTP传输CLI的重定向、重试、续传与输出兼容 | 待包装基线 |
| 15 | [github/cmark-gfm](https://github.com/github/cmark-gfm/tree/27d942c8b0a62d192f616e5bf3578f4b6a89e180) · [素材卡](cards/42_cmark_gfm.md) | GFM文档的解析、AST位置、扩展与渲染兼容 | 待包装基线 |
| 44 | [sharkdp/fd](https://github.com/sharkdp/fd/tree/14dcd92fb76ca0ebc2e82671a275f67c790d25fc) · [素材卡](cards/71_fd.md) | fd 查找、筛选与批量执行的行为兼容实现 | 先验证范围 |
| 45 | [mikefarah/yq](https://github.com/mikefarah/yq/tree/a814ff5166040ec745a96bddd79ee31c3a548e83) · [素材卡](cards/72_yq.md) | yq 多文档配置更新与可读输出兼容 | 先验证范围 |
| 46 | [restic/restic](https://github.com/restic/restic/tree/9da3b87b07706956e8dc5fd5cb259b99ec940f51) · [素材卡](cards/73_restic.md) | restic 本地仓库快照备份与恢复互操作 | 先验证范围 |
| 47 | [sqlfluff/sqlfluff](https://github.com/sqlfluff/sqlfluff/tree/1fdd794c925efa62f93ad78ff0d35ea41c60bea7) · [素材卡](cards/74_sqlfluff.md) | 模板化 SQL 的诊断、修复与源位置兼容 | 待范围收敛 |
| 48 | [jgm/pandoc](https://github.com/jgm/pandoc/tree/35742c0001ab2da45cebae1c37eacc2439f147ed) · [素材卡](cards/75_pandoc.md) | 文档 AST、扩展语义与跨格式转换兼容 | 待包装基线 |
| 49 | [johnkerl/miller](https://github.com/johnkerl/miller/tree/3fa2b291fc7bd93f491c93c2453e7d50a18d645d) · [素材卡](cards/76_miller.md) | 带 DSL 和跨记录状态的表格流处理兼容 | 先验证范围 |
| 50 | [wireshark/wireshark](https://github.com/wireshark/wireshark/tree/455e49bcca6882e317d83d76feb86cf88a27df1f) · [素材卡](cards/77_wireshark.md) | 离线抓包的跨帧重组、字段与过滤兼容 | 待离线工具链 |

## 阅读与筛选

优先读素材卡中的已有能力和正常基线。成熟库、原生扩展或简单配置若能完整满足范围，应停止该设计或换完整交付目标；不能靠禁止普通依赖增加难度。

性能方向的 10 项全部等待基线测量。实现恢复方向需要先跑通健康参考，再定义关联缺口。主仓库互不重复也不保证任务族独立，应另按协议、算法、依赖和测试生成谱系划分。

dbt、CEL-Go、Pydantic Core 的迁移或别名已归一，各只计一个来源。旧仓库材料保留作迁移证据，不额外计数。
