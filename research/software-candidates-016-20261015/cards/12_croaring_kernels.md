# 12_croaring_kernels：混合容器的bitmap操作与压缩优化

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/RoaringBitmap/CRoaring/tree/f2d9c6d3affaed28c8a899e96d85334ce4ae35af)；commit `f2d9c6d3affaed28c8a899e96d85334ce4ae35af`。

许可观察：Apache-2.0 OR MIT，依据完整 LICENSE；测试 realdata 的来源另固定。

## 已有能力与拟出的题

CRoaring 已有 SIMD、运行时 dispatch 和多类容器运算。任务不能仅要求写一个 AND 内核，也不能把打开既有 SIMD 开关叫新算法。

针对混合 array/bitset/run 容器的批量 bitmap 查询，优化交并差、cardinality 聚合或避免中间物化的数据路径，保持标准序列化和边界行为。

原题类别参照：integer_compression_codec / vliw_kernel_optimization：组合表示和机器内核优化。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 真实库内核与批量接口，稳定 C ABI

- 固定合成/许可确认的真实分布；测处理时间、内存和构建成本

## 参考与迭代评分

小规模使用独立整数集合 oracle，大规模校验固定摘要及逐样例结果；原始性能 baseline 必须在指定 CPU 实测。

拟评分维度：

- 集合语义正确性门槛

- 不同容器/密度分布的查询时间

- 避免中间物化的批量路径

- 序列化互通

- 内存与构建成本

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 单容器快速路径之后做混合表示与 skew 的算法选择

- 优化聚合与序列化协调，并解决 scalar/SIMD 两条路径一致性

最强廉价基线：调用库已有 and_cardinality、聚合接口、run_optimize 和 CPU dispatch；若现成 API 组合已近最优，不应继续堆数据规模。

先做的否证探针：先把最强现成 API 组合跑在声明负载上，检查是否存在剩余可稳定改善的热点。

构造风险：

- x86 AVX 与 ARM NEON 的 headroom 不同；不能承诺一组跨机器性能端点

- 成熟库早满风险高

- 新任务批量 API 与内存预算尚未冻结

## 实际取得的源码证据

- [已有微基准入口](https://github.com/RoaringBitmap/CRoaring/blob/f2d9c6d3affaed28c8a899e96d85334ce4ae35af/README.md#L611)；本地 [`sources/12_croaring_kernels/files/README.md:611`](../sources/12_croaring_kernels/files/README.md)。

- [现成 cardinality 快路](https://github.com/RoaringBitmap/CRoaring/blob/f2d9c6d3affaed28c8a899e96d85334ce4ae35af/src/roaring.c#L3053)；本地 [`sources/12_croaring_kernels/files/src/roaring.c:3053`](../sources/12_croaring_kernels/files/src/roaring.c)。

- [混合容器边界素材](https://github.com/RoaringBitmap/CRoaring/blob/f2d9c6d3affaed28c8a899e96d85334ce4ae35af/tests/mixed_container_unit.c#L1402)；本地 [`sources/12_croaring_kernels/files/tests/mixed_container_unit.c:1402`](../sources/12_croaring_kernels/files/tests/mixed_container_unit.c)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/12_croaring_kernels/manifest.json)。[完整 Git 文件树索引](../sources/12_croaring_kernels/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

