# 58_lucene Lucene 混合布尔检索的正确 top-k 与尾延迟

- 路线：M3；优先级：`hold_until_baseline`。素材候选，未构题/构建/运行/校准。
- 固定源码：`apache/lucene@8476457b8752be2fd8094eaf5cd9bf0cea9594ae`；源码哈希/清单见 `../sources/58_lucene/manifest.json`。
- 完整候选范围：查询重写→postings/块上界→WAND/minShouldMatch→collector→跨 segment top-k；固定索引、排序和 totalHits 合同。
- 原题锚点：`ann_vector_search_qps`, `exchange_core_throughput`；仅借难度机制，不承诺同等运行难度。
- 已有能力：WAND 已有 block-max 上界、collector 最小竞争分数反馈、head/lead/tail 与成本排序；IndexSearcher 已提供并行路径。
- 拟议缺口：未证实缺口：强正常查询计划/缓存/并行后，稀疏密集混合或 segment 倾斜是否仍有调度/迭代开销。

## 三类工作负载/工作流

- 高频+低频词和 minShouldMatch：跳过量与上界维护
- 多 segment/过滤器：并行利用与合并开销
- 大/小 k 与 score tie：竞争阈值与正确排序/尾延迟

- 最强正常基线：当前 JDK 的正常 JIT/Release、已有 WAND/MaxScore/缓存、合适 executor/slice；相同索引/查询与 exact 或 lower-bound totalHits 要求。
- 首探/否证：正常设置与查询形态矩阵先测，预热后交错记录 p50/p95、CPU、分配；若现有计划/并行已消除瓶颈则撤销。
- 正确性 oracle：冻结上游结果+小索引穷举完整评分；逐一比较 docID/score/tie/totalHits 语义；原生 WAND scaling 和 basics/random tests。
- 测量计划：固定硬件/CPU/内存/存储与 seed，分离准备/实现执行；交错重复测正确结果的时间、RSS/分配及特定资源，记录噪声与跨 seed 泛化。奖励上下端点均未测；上游宣传倍率不是本题收益。
- 后续结构假设 1：若强基线后 segment 工作量倾斜仍造成长尾，研究按成本细分调度和 collector 合并。
- 后续结构假设 2：若强基线后上界重算/队列维护仍主导，研究批量推进与上界缓存，严格不漏 competitive hit。
- 离线：固定完整源码/JDK/Gradle wrapper 与依赖缓存，预置 synthetic 索引/corpus；未试离线构建。
- 许可观察：根 Apache-2.0 与 NOTICE 已存；依赖/数据再分发未完整审计。
- 平台风险：JDK 向量实现、JIT 与 x86/ARM 缓存不同，分架构热身/校准。

## 源码与官方证据

- [lucene/core/src/java/org/apache/lucene/search/WANDScorer.java:55](https://github.com/apache/lucene/blob/8476457b8752be2fd8094eaf5cd9bf0cea9594ae/lucene/core/src/java/org/apache/lucene/search/WANDScorer.java#L55)：已有 block-max WAND 实现和竞争分数反馈。
- [lucene/core/src/java/org/apache/lucene/search/WANDScorer.java:111](https://github.com/apache/lucene/blob/8476457b8752be2fd8094eaf5cd9bf0cea9594ae/lucene/core/src/java/org/apache/lucene/search/WANDScorer.java#L111)：阈值缩放向下取整以免漏匹配。
- [lucene/core/src/test/org/apache/lucene/search/TestWANDScorer.java:90](https://github.com/apache/lucene/blob/8476457b8752be2fd8094eaf5cd9bf0cea9594ae/lucene/core/src/test/org/apache/lucene/search/TestWANDScorer.java#L90)：原生索引查询正确性测试。
- [lucene/benchmark-jmh/src/java/org/apache/lucene/benchmark/jmh/CompetitiveBenchmark.java:38](https://github.com/apache/lucene/blob/8476457b8752be2fd8094eaf5cd9bf0cea9594ae/lucene/benchmark-jmh/src/java/org/apache/lucene/benchmark/jmh/CompetitiveBenchmark.java#L38)：原生 JMH competitive 基准，非本次测量。
- 官方上下文：[1](https://lucene.apache.org/core/10_3_1/core/org/apache/lucene/search/IndexSearcher.html)。
