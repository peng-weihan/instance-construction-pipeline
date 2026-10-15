# 软件工程候选池：16 条真实素材路线

> 执行状态已更新：素材阶段数据保留在下文；[实际出题启动记录](EXECUTION_STATUS.md)见独立报告。

**现有 6 条路线扩展为 16 个候选：6 个原来源重新定义更完整的范围，加 10 个新开源项目。** 每个候选均固定 40 位源码 commit、取得关键文件与许可、保存完整 Git 文件树索引，并写成可审阅的出题卡片。8 条建议先细化，另 8 条先做廉价解法筛选。优先级是下一步投入次序，不是难度通过标志。

本批实际落盘 **101 个关键源码/文档/许可文件，7,372,407 字节**；16 份 Git 文件树索引均未截断。这里只取得选读材料和文件索引，尚未下载/封装全部仓库、构建依赖、语言 grammar、参考服务和互通数据。下载成功不等于完整出题素材包就绪。

本批完成的是候选研究与构造输入，**没有新增完整题包、没有启动本批构造 CLI 或六小时求解运行**。旧六条小样保留原目录和结果；旧 profile 的 Oracle 或分数不能转移给这些扩大范围的新合同。科学/金融等已有运行不属于本批。

## 16 个候选

| # | 素材项目 | 拟出的题 | 机制 | 建议 | 来源 |
|---|---|---|---|---|---|
| 01 | [openapi-generators/openapi-python-client](https://github.com/openapi-generators/openapi-python-client/tree/0a283fe21eeaa23046faf622d4ff4b2c826d2edb) | [流式 SDK、认证覆盖、取消与资源生命周期](cards/01_openapi_streaming.md) | 工程演进 | P1 | 原来源扩展 |
| 02 | [microsoft/restler-fuzzer](https://github.com/microsoft/restler-fuzzer/tree/6d984deedbc54aad957fa3da0c7e9e5df23a2aee) | [真实 campaign 的 checkpoint/journal/外部状态恢复](cards/02_restler_recovery.md) | 工程演进 | P1 | 原来源扩展 |
| 03 | [encode/httpx](https://github.com/encode/httpx/tree/b5addb64f0161ff6bfe94c124ef76f6a1fba5254) | [重试预算、可重放 body、认证/重定向与事件链](cards/03_httpx_transport.md) | 工程演进 | P2 | 新增 |
| 04 | [pytest-dev/pytest](https://github.com/pytest-dev/pytest/tree/c9c19f8e62c12834ad83193a1869cc82fe9c700e) | [fixture 执行图、缓存失效与异常清理诊断](cards/04_pytest_fixtures.md) | 工程演进 | P2 | 新增 |
| 05 | [astral-sh/uv](https://github.com/astral-sh/uv/tree/9385290f1bf895cb3f587118ce92cce9a0585f77) | [跨环境 lock 更新计划与约束解释](cards/05_uv_resolution.md) | 工程演进 | P1 | 新增 |
| 06 | [WebAssembly/spec](https://github.com/WebAssembly/spec/tree/d910f03bd6d6477656fc5070b5098e8f909305d3) | [类型验证、模块链接与间接调用的 VM](cards/06_wasm_validation.md) | 系统能力实现 | P1 | 原来源扩展 |
| 07 | [apache/arrow](https://github.com/apache/arrow/tree/ca5564e007a209e251b9d4648af4bc6a53c68c4f) | [增量 IPC、嵌套类型与 dictionary 演化](cards/07_arrow_ipc.md) | 系统能力实现 | P2 | 新增 |
| 08 | [nghttp2/nghttp2](https://github.com/nghttp2/nghttp2/tree/7e10fcf3c58e692902939bab8f898bdd9ec9cff7) | [HPACK、flow control 与多 stream 状态机](cards/08_http2_session.md) | 系统能力实现 | P2 | 新增 |
| 09 | [valkey-io/valkey](https://github.com/valkey-io/valkey/tree/cf5efa70192faedacb6741ee2a8f800d0482862f) | [RESP3 事务、WATCH、多客户端与日志恢复](cards/09_valkey_transactions.md) | 系统能力实现 | P1 | 新增 |
| 10 | [apache/datafusion](https://github.com/apache/datafusion/tree/10343c18292fc3a9ca62b59c8bb530169fe79b82) | [真实 SortExec/TopK/spill/分区合并优化](cards/10_datafusion_sort.md) | 正确性约束的性能优化 | P1 | 原来源扩展 |
| 11 | [facebook/rocksdb](https://github.com/facebook/rocksdb/tree/a215c38a8ed34848edc152f7435eabc128208111) | [耐久性和读写放大约束的 compaction 优化](cards/11_rocksdb_compaction.md) | 正确性约束的性能优化 | P2 | 新增 |
| 12 | [RoaringBitmap/CRoaring](https://github.com/RoaringBitmap/CRoaring/tree/f2d9c6d3affaed28c8a899e96d85334ce4ae35af) | [混合 bitmap 容器的批量操作与聚合优化](cards/12_croaring_kernels.md) | 正确性约束的性能优化 | P2 | 新增 |
| 13 | [toml-rs/toml](https://github.com/toml-rs/toml/tree/ceac6e4412420d5a5c19e4f7293ad005cf1a31b2) | [无损解析、span、table 编辑的跨 crate 恢复](cards/13_toml_lossless.md) | 跨层实现恢复 | P1 | 原来源扩展 |
| 14 | [tree-sitter/tree-sitter](https://github.com/tree-sitter/tree-sitter/tree/8ca548849fc8dbefd699edcec26546bb14112820) | [增量解析、节点位置与错误恢复](cards/14_tree_sitter_incremental.md) | 跨层实现恢复 | P1 | 新增 |
| 15 | [jqlang/jq](https://github.com/jqlang/jq/tree/71c2ab509a8628dbbad4bc7b3f98a64aa90d3297) | [流、作用域、递归、更新路径与错误的兼容重实现](cards/15_jq_composition.md) | 行为兼容重实现 | P2 | 原来源扩展 |
| 16 | [libarchive/libarchive](https://github.com/libarchive/libarchive/tree/b10312a52e5e4d1baf047b563e501b4fb184adde) | [tar/pax、链接、元数据与分段流的行为兼容](cards/16_libarchive_cli.md) | 行为兼容重实现 | P2 | 新增 |

五种机制是我们对原题的分析分类，分配为 5/4/3/2/2，并非官方子类或官方占比。原题对应关系见每张卡片；原题证据与可知边界沿用[36 道软件题逐项研究](../software-engineering-2026-10-15/REPORT.md)。这支持“同类但不同需求”的设计判断，还不能证明统计上的同分布、六小时难度相等或训练收益。

## 哪些先做，哪些先否证

**P1：OpenAPI SDK、RESTler、uv、WASM、Valkey、DataFusion、TOML、Tree-sitter。** 它们有可定位的跨层行为链，可以写出具体的中期与后期改进假设。先实现卡片里的最小否证探针，再决定是否投入完整参考解；P1 不表示已经验证了六小时潜力。

**P2：HTTPX、pytest、Arrow IPC、HTTP/2、RocksDB、CRoaring、jq、libarchive。** 对应材料是真实的，但现成插件/库包装、普通参数设置或已有能力很可能解决大部分任务。先给强廉价基线机会；正常依赖能完整通过合理合同，说明该版本应淘汰或重新定义产品需求。不能临时禁止依赖、故意降速 baseline、隐藏公开算法或堆样例数量来补难度。

关键材料观察：Arrow 提供格式定义和跨语言 runner，但这也意味着 wrapper 基线很强；HTTPX 的取消清理和 pytest 的 finalizer 已存在，新增需求必须明确；uv 已有 universal lock，不能重复出这项功能；RocksDB/CRoaring 的成熟优化意味着性能余量必须测量后才知道。

## 怎样把这些材料交给三个 factory 方法

- 工程演进：用 DeepSWE C 的需求→失败证据→参考改造，再用 NL2Repo 方法补足公开规格。issue 只能作为线索，先在固定版本复现；不能把已实现能力说成缺失。
- 系统能力实现：从规格与独立参考提取状态合同，给可起步的骨架，逐层实现；一次往返自检不能替代跨实现互通。
- 性能优化：保持真实引擎和独立正确性检查；先测 untouched 和强合理配置 baseline，再决定目标及归一化，不填写虚构性能端点。
- 实现恢复：按一个关联行为链设计受控缺口、保留逆补丁和原生回归；公开上游可能被记忆，不按删除行数估算新颖性或时长。
- 行为重实现：用 ProgramBench 式可观察参考与差分探针，同时定义进程内 API、CLI/文件状态等真实合同；先检查现成 binding 是否已经满足全部需求。

[三个参考 factory 的实际能力与门禁](../software-engineering-2026-10-15/factory-methods.md)保持原有结论。原始规格和远端共享安装未修改；本批只新增自己的研究目录。

## 训练分离与六小时证据

新候选使用上述独立项目/新合同，不复制 EdgeBench 原始评测输入或私有 verifier。公开原题只用于机制和交付形态参照。后续生成的用例须分公开调试、重复反馈和作者质量审计集合；反馈集不能混入教师输入的参考答案。按源码谱系和机制做 split，特别是 OpenAPI/HTTPX、Arrow/DataFusion 这两组共享依赖关系，不能只靠随机 seed 宣称独立。

每张卡片给出两条“早期基础完成后还可能做什么”的具体路径，但它们是设计假设。构造阶段先看最强廉价基线是否早满、是否存在真实跨模块缺口；只有后续真实六小时、多次运行曲线才能校准长程难度。无进展的六小时运行也不能算好题。本批不代替任务书的完整交付与验收。

## 文件与可复现性

- [16 张卡片的机器可读索引](candidates.json) / [CSV](candidates.csv)：设计、范围、风险、首个否证探针及原题参照。
- [源码获取清单](source-manifests.json) / [冻结的获取计划](plan.json)：原始 URL、字节数、SHA-256 与 commit；404 备选许可名不等于缺少许可，历史拼错路径的修正也保留。
- [作者输入队列](authoring_queue.json)：16 个未启动 job；P1 在前，指定 gpt-6.1-sol/high 和用户提供的三个 Codex home。启动前须有当时可用容量，preferred account 不代表已获得 slot。
- `harvest_sources.py` → `supplement_sources.py`：按固定 SHA 获取关键文件及全文件树；`write_cards.py`、`finalize_inventory.py` 只渲染研究产物，不生成题包或验证难度。

三个远端路径此次已只读确认二进制存在且均为 codex-cli 0.160.0，配置模型均为 gpt-6.1-sol/high；这只是安装/配置确认，不是本批成功模型调用或正在构造的证据。

