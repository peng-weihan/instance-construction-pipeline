# 10_datafusion_sort：有界内存排序、TopK与多分区合并

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/apache/datafusion/tree/10343c18292fc3a9ca62b59c8bb530169fe79b82)；commit `10343c18292fc3a9ca62b59c8bb530169fe79b82`。

许可观察：Apache-2.0，保留 NOTICE；crate 各许可随 vendor 汇总。

## 已有能力与拟出的题

源码已有 external sort、TopK、memory reservation 和 spill；目标是性能改善，不能把现有功能称为待实现。固定 Cargo.toml 的 MSRV 为 1.86.0。

在固定 DataFusion 50.0.0 源码中优化 SortExec/TopK/多分区 merge，在内存上限和 spill 条件下保留 SQL 排序语义；交付可编译真实引擎补丁。

原题类别参照：ann_vector_search_qps / exchange_core_throughput：正确性下的真实引擎性能优化。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 生产算子及必要 planner/runtime 改动

- 真实 RecordBatch 执行路径；不允许把实际引擎换成一个独立 Python 排序脚本再冒称优化

## 参考与迭代评分

正确性使用独立 SQL/Arrow 结果合同，计时运行真实编译后的引擎；tie 顺序、NaN、NULL 与字符串 collation 先明确。baseline/reference 时间必须实测，当前均未填。

拟评分维度：

- SQL 排序正确性门槛

- TopK 与全排序时延

- spill 工作负载时延

- 峰值内存和 I/O

- 跨 partition 结果

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 普通数值排序之后处理 string/NULL、高重复、offset/limit

- 改善低内存、多 partition 与 spill 的协调，保持正确性

最强廉价基线：先扫现有 sort 配置、batch size 和算法开关；已有优化配置若已接近上限，不能发明一个更慢 baseline 来造 headroom。

先做的否证探针：先在固定 50.0.0 编译真实 probe，完成真实 baseline；旧较新版本补丁要重新适配，dry-run 成功不是性能证据。

构造风险：

- 上一轮没有真实 DataFusion 编译/性能分，不能沿用模拟或 Python proxy 分值

- 耗时和确定性依赖 CPU/磁盘；跨架构计时端点不能共用假常数

- Rust 依赖构建需先 vendor

## 实际取得的源码证据

- [固定工具链下限](https://github.com/apache/datafusion/blob/10343c18292fc3a9ca62b59c8bb530169fe79b82/Cargo.toml#L79)；本地 [`sources/10_datafusion_sort/files/Cargo.toml:79`](../sources/10_datafusion_sort/files/Cargo.toml)。

- [真实执行算子](https://github.com/apache/datafusion/blob/10343c18292fc3a9ca62b59c8bb530169fe79b82/datafusion/physical-plan/src/sorts/sort.rs#L881)；本地 [`sources/10_datafusion_sort/files/datafusion/physical-plan/src/sorts/sort.rs:881`](../sources/10_datafusion_sort/files/datafusion/physical-plan/src/sorts/sort.rs)。

- [已有 spill 路径](https://github.com/apache/datafusion/blob/10343c18292fc3a9ca62b59c8bb530169fe79b82/datafusion/physical-plan/src/sorts/sort.rs#L379)；本地 [`sources/10_datafusion_sort/files/datafusion/physical-plan/src/sorts/sort.rs:379`](../sources/10_datafusion_sort/files/datafusion/physical-plan/src/sorts/sort.rs)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/10_datafusion_sort/manifest.json)。[完整 Git 文件树索引](../sources/10_datafusion_sort/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

旧 profile：samples/software-multiline-001/04_datafusion；原较新 revision 与本候选 50.0.0 不同，当前正式奖励仍无效。

