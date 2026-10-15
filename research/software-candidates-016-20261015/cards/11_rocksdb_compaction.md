# 11_rocksdb_compaction：读写放大约束下的存储引擎优化

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/facebook/rocksdb/tree/a215c38a8ed34848edc152f7435eabc128208111)；commit `a215c38a8ed34848edc152f7435eabc128208111`。

许可观察：GPL-2.0 OR Apache-2.0；COPYING 和 LICENSE.Apache 已下载。选择许可并保留逐文件声明。

## 已有能力与拟出的题

引擎已有多种 compaction 与大量可调参数。db_bench 有配置和计时；db_compaction_test 是正确性素材，不能拿 db_bench 单独证明无数据丢失。

在固定资源与固定混合读写/恢复负载上改进 RocksDB compaction 调度或数据路径，优化吞吐/尾延迟，同时约束持久性、空间及写放大。

原题类别参照：exchange_core_throughput / notebook_lossless_compression：正确性与多个资源指标下的性能优化。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 引擎源码及明示允许的配置

- judge 新建数据目录、重放固定操作日志、执行确定崩溃点；提交不依赖 agent 的活 DB

## 参考与迭代评分

独立 key/value 操作日志模型检查结果和恢复；实测 untouched baseline 与最强合理配置基线。性能端点暂空，不按指标理论边界假定可达上限。

拟评分维度：

- 读写/恢复正确性门槛

- 混合负载吞吐

- 固定窗口尾延迟

- 空间和写放大

- 资源预算

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 单一吞吐优化后解决读写互相影响和 compaction stall

- 协调恢复、后台 compaction 与空间上限的性能取舍

最强廉价基线：先试 pipelined write、buffer/compaction 参数和批处理；成熟引擎普通调参可能消耗全部 headroom，应先否证。

先做的否证探针：同机重复运行 untouched 与强配置 baseline，随后用 db_stress/日志模型检查；若剩余稳定增益不足则不出题。

构造风险：

- 严格尾延迟容易受宿主噪声影响

- 禁 WAL 可虚增吞吐，必须由耐久性合同和行为检查约束

- 持续后台状态要在每次 verifier 内重建，不能依赖 agent DB

## 实际取得的源码证据

- [许可及引擎说明](https://github.com/facebook/rocksdb/blob/a215c38a8ed34848edc152f7435eabc128208111/README.md#L29)；本地 [`sources/11_rocksdb_compaction/files/README.md:29`](../sources/11_rocksdb_compaction/files/README.md)。

- [已有调参基线](https://github.com/facebook/rocksdb/blob/a215c38a8ed34848edc152f7435eabc128208111/tools/db_bench_tool.cc#L567)；本地 [`sources/11_rocksdb_compaction/files/tools/db_bench_tool.cc:567`](../sources/11_rocksdb_compaction/files/tools/db_bench_tool.cc)。

- [真实 compaction 测试](https://github.com/facebook/rocksdb/blob/a215c38a8ed34848edc152f7435eabc128208111/db/db_compaction_test.cc#L157)；本地 [`sources/11_rocksdb_compaction/files/db/db_compaction_test.cc:157`](../sources/11_rocksdb_compaction/files/db/db_compaction_test.cc)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/11_rocksdb_compaction/manifest.json)。[完整 Git 文件树索引](../sources/11_rocksdb_compaction/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

