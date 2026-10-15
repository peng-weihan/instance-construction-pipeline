# 新增十五个软件工程出题素材

调研日期：2026-10-15。

**新增 15 个主来源，覆盖五条构造路线，每条 3 个。** 本轮与现有候选登记去重，排除了之前的 16 个来源以及新加入的 Scrapy、Lark、ripgrep、Ninja 等；15 个新来源没有与所查登记中的主仓库重合。Tantivy 使用当前 canonical 仓库 `quickwit-oss/tantivy`，抓取时的旧别名保留在来源记录中。

本轮实际保存 **140 份关键源码、文档、测试和许可文件，3,168,344 字节**，固定 15 个 40 位 commit、15 份未截断文件树，并核验了逐文件摘要和 76 个证据位置。这里是选读材料包，完整 checkout、离线依赖、健康参考运行和新题包尚未完成。验证结果见 [inventory-check.json](inventory-check.json)。

建议先对 **6 个来源做范围与简单解法验证**，其余 **9 个暂缓**。这些优先级表示下一步研究投入，不表示已经具有六小时难度。各类等量用于本轮扩展覆盖，不代表正式配额或原题比例。

## 十五个来源与可出的任务

每张卡都有已有能力、拟交付、工程链、三个组合场景、后续工作假设、独立判据、强正常基线和首个否证探针。以下任务方向是从源码能力中提出的设计，尚未构题。

| 路线 | 新来源与材料卡 | 可以细化的完整交付 | 本轮判断 |
|---|---|---|---|
| M1 产品演进 | [Alembic](cards/28_alembic.md) / [官方](https://github.com/sqlalchemy/alembic) | 面向明确重构意图的迁移产品版本：规划/校验、保数据变更、依赖顺序、可审查脚本、升级回退及后端兼容 | 先验范围；单项 rename 改写可能很短 |
| M1 产品演进 | [Sphinx](cards/29_sphinx.md) / [官方](https://github.com/sphinx-doc/sphinx) | 内容指纹、依赖失效解释、并行状态合并和目录迁移组成的增量构建模式 | 暂缓；官方扩展事件可能足够 |
| M1 产品演进 | [mitmproxy](cards/30_mitmproxy.md) / [官方](https://github.com/mitmproxy/mitmproxy) | 多会话 HTTP 场景回放：变量关联、依赖调度、隔离、取消/失败处理、持久化与报告 | 先验范围；内置 replay/addon 是强基线 |
| M2 系统构建 | [Mosquitto](cards/31_mosquitto.md) / [官方](https://github.com/eclipse-mosquitto/mosquitto) | 明确 MQTT 子集的单 broker：订阅、retain、QoS 会话、过期、流量配额与成功快照后的恢复 | 先验范围；现成 broker 包装须先检验 |
| M2 系统构建 | [BMv2](cards/32_bmv2.md) / [官方](https://github.com/p4lang/behavioral-model) | 冻结 JSON 执行子集的包处理引擎：parser→match/action→跨包状态→checksum/deparser | 先验范围与工具链；不自动包含整个 P4 生态 |
| M2 系统构建 | [Apache Avro](cards/33_avro.md) / [官方](https://github.com/apache/avro) | schema 图、编解码、writer/reader resolution、流式容器与跨实现互通 | 暂缓；官方库/fastavro 很可能已覆盖 |
| M3 性能优化 | [DuckDB](cards/34_duckdb.md) / [官方](https://github.com/duckdb/duckdb) | 受限内存分组聚合的分区、状态导出、并行合并与输出链 | 待强基线；先测现有适应策略和配置 |
| M3 性能优化 | [simdjson](cards/35_simdjson.md) / [官方](https://github.com/simdjson/simdjson) | 混合 JSON 流的批边界、按需访问、容量复用与扫描/解码效率 | 待强基线；不能只靠开启已有 SIMD |
| M3 性能优化 | [libvips](cards/36_libvips.md) / [官方](https://github.com/libvips/libvips) | 缩略图/ROI 流水线的缓存、区域调度、alpha/颜色与并发资源效率 | 待强基线；保留已有 thumbnail/Highway 快路径 |
| M4 实现恢复 | [Tokio](cards/37_tokio.md) / [官方](https://github.com/tokio-rs/tokio) | 任务状态、通知/取消、计时器和关闭生命周期的关联恢复 | 先验可重复判据；并发不能靠偶然调度评分 |
| M4 实现恢复 | [Tantivy](cards/38_tantivy.md) / [官方](https://github.com/quickwit-oss/tantivy) | 索引写入、提交/删除、reader 视图、segment 生命周期与失败处理恢复 | 先验范围；有明确纵向工作流和原生故障测试 |
| M4 实现恢复 | [Rustls](cards/39_rustls.md) / [官方](https://github.com/rustls/rustls) | 固定密码 provider 下 TLS1.3 记录、会话恢复、early/application data 与关闭的关联恢复 | 先验测试框架/依赖；不另造密码原语 |
| M5 兼容重实现 | [Rsync](cards/40_rsync.md) / [官方](https://github.com/RsyncProject/rsync) | 目录同步的过滤、保护/删除、链接、更新、dry-run/itemize 和多次运行副作用 | 先验范围；简单全量复制须有机会 |
| M5 兼容重实现 | [curl](cards/41_curl.md) / [官方](https://github.com/curl/curl) | 明确 HTTP 子集的传输 CLI：重定向、重试、续传、输出文件及退出行为 | 暂缓；libcurl 绑定可能轻易完成 |
| M5 兼容重实现 | [cmark-gfm](cards/42_cmark_gfm.md) / [官方](https://github.com/github/cmark-gfm) | GFM 解析库/CLI：block/inline、扩展节点、AST 位置、分块输入与渲染兼容 | 暂缓；先测成熟 Markdown 库适配 |

## 优先做的六个范围探针

这里的先后表示先消除什么未知项，不安排付费求解或已有运行队列。

| 次序 | 素材 | 最便宜而有判断力的验证 | 什么结果会停止当前设计 |
|---|---|---|---|
| 1 | Tantivy | 健康 gold 用 Manual reload 跑写入→提交→删除→失败提交→重开，再比较全量重建方案 | 只是少数 API 胶水；合理重建基线已满足全部范围 |
| 2 | Alembic | 用原生 Rewriter/rename API 处理跨表/字段/约束重构，并实际 upgrade→downgrade→upgrade | 单项名称映射和短插件已完成产品交付；缺少更完整版本目标 |
| 3 | Rsync | 固定本地文件树，比较过滤/硬链接/二次同步；普通复制与现成规则库作为对照 | 只剩参数适配，或者难点来自权限/平台偶然差异 |
| 4 | mitmproxy | 官方 addon 先实现两个会话的 ID/token 捕获替换、交错回放和取消 | 原生队列/metadata 加薄扩展已完整保证所有行为 |
| 5 | Mosquitto | 现成 broker/客户端先走重连、QoS 状态、会话过期和保存恢复；列出拟 starter 的真正缺口 | 包装现成 broker 就能全解；拟题只是重述已有服务 API |
| 6 | BMv2 | 固定预编译 JSON，用最薄 stock BMv2 文件 I/O 与控制适配检查包和寄存器轨迹 | 只是已有引擎适配；或完整参考的离线工具链无法闭合 |

产品演进方向需要作者进一步比较多个完整里程碑范围；不能把 Alembic 的一个 rename 功能，或 mitmproxy 的一个变量替换插件，直接升格为六小时任务。实现恢复方向先验证健康参考，再设计关联缺口。重实现方向先确定真实产物与兼容边界，普通依赖保持允许。

## 源码核对已经排除了哪些错误方向

- **Alembic 有 rename 操作，缺的是何种自动化流程必须说清。** 固定文档明确 autogenerate 不自动识别表/列重命名，原生 rename API 却已存在。新需求可以研究显式意图驱动的完整重构，不能描述成“实现 rename”。[固定文档](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/docs/build/autogenerate.rst#L162)
- **Tantivy 自动 reload 不是提交同步屏障。** 立即查询旧视图是文档允许的行为，确定性检查应显式 reload；不能把它误报为上游缺陷。[固定代码](https://github.com/quickwit-oss/tantivy/blob/8a4cfc40f5b7446c0700471aa50290dbb7f8ea97/src/reader/mod.rs#L15)
- **DuckDB 不是缺少聚合状态溢写。** 本次固定源码已有 arena-backed 状态低内存回归。题目应研究现有路径之上的真实资源取舍，而非照旧博客描述补已有能力。[固定回归](https://github.com/duckdb/duckdb/blob/dda2e4090494101087e7726581928e6af44dbc34/test/sql/aggregate/aggregates/aggregate_state_spilling.test_slow#L1)
- **libvips 已有多条成熟快路径。** 预缩小、缓存、动态线程池和 Highway 路径应保留为强基线；linear-light 的质量合同还限制能否使用 JPEG 预缩小。[固定代码](https://github.com/libvips/libvips/blob/06564b0a4c3f473d0e0cb9f9977ab647888aa43d/libvips/resample/thumbnail.c#L490)
- **标准丰富不自动意味着实现困难。** Avro、curl、GFM 都有成熟实现，可作为参考和规格材料；它们是否适合出长程题，先由正常包装基线决定。

## 怎样交给出题作者

每份材料都沿用 [全量原题分析中的构造卡要求](../software-difficulty-design-20261015/ANALYSIS_REPORT.md)：

```mermaid
flowchart LR
    A[固定源码与许可] --> B[区分已有能力和真正缺口]
    B --> C[选择完整产品或子系统范围]
    C --> D[强正常基线与首个否证]
    D --> E[健康参考与独立判据]
    E --> F[starter与新题包]
    F --> G[真实长程难度校准]
```

本轮到达的是 A 和任务范围设计，D 中的运行探针尚未执行。`build_scope_probe` 允许进入范围研究，不是“可直接出正式题”。性能三项先验证默认、最佳合法配置与现有算法路径，在相同正确性和资源约束下确有稳定收益后再冻结工作负载与奖励。当前没有性能端点、收益比例或时间估计。

## 来源与训练划分

新来源指主仓库不在所查旧登记中，不能据此宣称训练/评测完全独立。mitmproxy/curl/Mosquitto/Rustls 存在协议或依赖谱系联系，Tantivy/DuckDB/Avro 同属数据系统，Markdown 与解析工具也有语义关联。后续按源码、协议/算法、目标行为和测试生成谱系记录重叠，不只按项目名或 seed 划分。

许可已逐项目记录观察并保存文本；例如 cmark-gfm 的代码 COPYING 与扩展测试文本许可不同，Rsync 和 libvips 也不是 MIT。仅对实际纳入 starter/reference/test 的文件继续清点，不能把整个材料包统一标一种许可证。

## 交付文件与复核范围

- [15 份素材卡](cards/)：每份包含可操作的出题方向和否证。
- [候选 JSON](candidates.json) / [CSV](candidates.csv)：可直接供后续筛选和作者读取。
- [来源清单](source-manifests.json)：固定 SHA、选读文件、字节数、SHA-256 和上游 URL。
- [旧来源去重记录](previous-source-check.json)：保留所查登记路径及摘要，未改旧来源。
- [库存完整性结果](inventory-check.json)：15 个唯一主仓库、五类各 3，文件摘要、证据位置和本地链接检查。

三组研究分别完成关键源码与测试/规格阅读，主分析抽查了 Alembic 自动生成边界、Sphinx 失效逻辑、mitmproxy 队列、Mosquitto 重连、BMv2 parser、Avro resolution、DuckDB spilling、simdjson buffer 及 libvips 质量约束。root 负责的六卡在卡尾记录实际定向阅读范围。没有宣称完整仓库源码审计、源码能成功构建或候选难度已经通过。

运行 `python3 research/software-materials-expansion-20261015/collect_and_validate.py` 可重新核验本地库存；该命令只检查材料、生成清单，不执行候选、容器、基准或模型。
