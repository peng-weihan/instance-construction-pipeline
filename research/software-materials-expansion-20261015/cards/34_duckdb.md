# 34 DuckDB：受限内存下分组聚合的吞吐与资源效率

- 路线：M3；优先级：`hold_until_baseline`。素材候选，尚未构题、构建或运行。
- 固定源码：`duckdb/duckdb@dda2e4090494101087e7726581928e6af44dbc34`；源码片段、文件树和 SHA-256 见 `../sources/34_duckdb/manifest.json`。
- 完整候选范围：分组键处理→线程本地聚合→radix 分区/状态导出→并行 combine→扫描输出；保持 NULL、字符串、聚合状态及重复执行语义。
- 原 EdgeBench 锚点：`exchange_core_throughput` 的资源/调度搜索，以及 `integer_compression_codec` 的精确正确性门槛；不由领域直接推定六小时难度。

## 已有能力与可考察取舍

- 当前已有盐值过滤、探测与 dictionary 地址缓存：`src/execution/aggregate_hashtable.cpp:364-393,470-562`；另有 perfect aggregation 实现，不能把基础哈希快路径作为新功能。
- 分区数已经受线程、行宽和内存 reservation 约束：`src/execution/radix_partitioned_hashtable.cpp:241-291`；sink 还调用已有 adaptivity，不能仅凭固定阈值猜测缺少自适应。
- arena-backed 状态已经能够导出，当前回归包含 `first/last/min/string_agg`、64 MB、并行 combine 和递归复用：`test/sql/aggregate/aggregates/aggregate_state_spilling.test_slow:1-162`。旧文档列出的 spilling 限制不能直接当此 SHA 的缺口。
- 负载 A：低基数重复键、窄整数，哈希/合并开销与缓存命中之间取舍。
- 负载 B：高基数长字符串、宽状态，分区页数/峰值内存与导出/临时 I/O 之间取舍。
- 负载 C：倾斜基数和多线程、临界内存，分区负载均衡与额外 repartition 成本之间取舍。

## 基线、否证和测量计划

- 最强合理基线：此 SHA 的 Release 和原生 allocator/优化器/perfect/dictionary/radix/adaptivity 快路径；先扫正常 `threads`、`memory_limit`、合法数据布局和临时盘配置；保留相同 SQL/结果合同。
- Oracle：冻结上游二进制与独立小数据 Python 整数/字符串聚合交叉检查；无序结果规范化；浮点另订容差/顺序合同，不以哈希值相同代替全量语义验证。
- 原生 runner 已把 `Run` 与 `Verify` 分开、先 warmup 再计时：`benchmark/benchmark_runner.cpp:142-190`；已有 string group benchmark 是极少组，不能替代 B/C 的覆盖。
- 独立测量：固定 CPU/内存/临时盘、数据生成 seed 与 revision；分离生成/装载/查询/结果读取；交错跑两实现，重复测延迟、峰值 RSS、临时字节及 I/O，跨 seed 验证。
- 首探：先仅用已有设置和原生路径运行 A/B/C 的规模阶梯；若调参已满足目标，或差异在噪声内，撤销优化题方向；奖励端点与收益门槛均待测。
- 剩余结构假设 1：配置优化后，结合观测到的倾斜与状态宽度改进 partition/combine 调度，可能减少临界内存下长尾；须先证明确有失衡且非已有 adaptivity 所覆盖。
- 剩余结构假设 2：配置优化后，优化导出→分区增长→逐分区导入路径中的重复搬运/临时分配；须以 profile 证实热点，并保留现有 native/exported phase 转换。

## 离线与许可

- 根许可 MIT；这里只读取许可，并未完成依赖和数据再分发审计。完整 tarball、第三方目录、构建工具及使用的扩展需预置；当前只下载片段，无离线构建证据。
- x86/ARM 的缓存、allocator 和存储表现不同；各架构独立强基线与校准，不能搬用倍率。
- 官方上下文：[外排聚合设计](https://duckdb.org/2024/03/29/external-aggregation)、[调优指南](https://duckdb.org/docs/preview/guides/performance/how_to_tune_workloads)。博客实验是上游历史结果，本卡没有实测性能。
