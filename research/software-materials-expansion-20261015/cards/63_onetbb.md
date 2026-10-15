# 63_onetbb oneTBB 多 arena 嵌套任务的调度效率

- 路线：M3；优先级：`hold_until_baseline`。素材候选，未构题/构建/运行/校准。
- 固定源码：`uxlfoundation/oneTBB@885b7813d38de698a9942e5026ad1bd9d16125d9`；源码哈希/清单见 `../sources/63_onetbb/manifest.json`。
- 完整候选范围：应用任务图→partitioner→arena admission/spawn→worker demand/唤醒→任务完成/取消；固定并发上限、嵌套与可见性合同。
- 原题锚点：`exchange_core_throughput`, `vliw_kernel_optimization`；仅借难度机制，不承诺同等运行难度。
- 已有能力：已有 arena、任务上下文/isolation、局部队列、可调 partitioner 与 worker demand；并非增加基础线程池。
- 拟议缺口：未证实缺口：合理 grain/partitioner/并发/affinity 后，混合任务和多 arena 是否仍有调度或唤醒成本。

## 三类工作负载/工作流

- 极短均匀任务：grain/调度开销与均衡
- 长短混合嵌套 DAG：窃取、缓存与长尾
- 多 arena/外部线程进入：资源限制与唤醒/竞争

- 最强正常基线：Release、正常 scheduler、auto/simple/affinity partitioner 和合理 grain/global_control/task_arena；合法串行阈值也应基线化，不强迫每小任务并行。
- 首探/否证：先调现有 API 参数与应用分解，固定输出和并发上限测吞吐/p95/CPU/RSS；若仅 grain/limit 即足够或空任务伪负载则撤销。
- 正确性 oracle：任务图确定性输出+执行计数/依赖顺序与并发上限日志，原生 task_arena 进入/attach/concurrent tests；后续 TSAN/压力测试不能替代输出检查。
- 测量计划：固定硬件/CPU/内存/存储与 seed，分离准备/实现执行；交错重复测正确结果的时间、RSS/分配及特定资源，记录噪声与跨 seed 泛化。奖励上下端点均未测；上游宣传倍率不是本题收益。
- 后续结构假设 1：强配置后若 arena has_tasks 扫描/唤醒仍为热点，研究可用任务提示与通知粒度，保留不丢任务和可见性。
- 后续结构假设 2：强配置后若嵌套隔离任务上下文切换/局部性仍主导，研究队列布局与调度，保留取消/异常传播。
- 离线：C++/CMake/Threads，按绑定功能固定 hwloc 等依赖与测试框架；未构建。
- 许可观察：根 Apache-2.0 已存，专门 exception/第三方条款按完整发行包核查，未完成审计。
- 平台风险：原子/内存序、拓扑与 oversubscription 在 ARM/x86 不同，独立资源上限校准。

## 源码与官方证据

- [src/tbb/arena.cpp:364](https://github.com/uxlfoundation/oneTBB/blob/885b7813d38de698a9942e5026ad1bd9d16125d9/src/tbb/arena.cpp#L364)：arena 维护局部、FIFO、resume 等既有任务检查。
- [src/tbb/arena.cpp:378](https://github.com/uxlfoundation/oneTBB/blob/885b7813d38de698a9942e5026ad1bd9d16125d9/src/tbb/arena.cpp#L378)：已有任务池状态与 worker demand 回收。
- [src/tbb/task_dispatcher.cpp:31](https://github.com/uxlfoundation/oneTBB/blob/885b7813d38de698a9942e5026ad1bd9d16125d9/src/tbb/task_dispatcher.cpp#L31)：spawn 设置上下文与隔离标记。
- [test/tbb/test_task_arena.cpp:1908](https://github.com/uxlfoundation/oneTBB/blob/885b7813d38de698a9942e5026ad1bd9d16125d9/test/tbb/test_task_arena.cpp#L1908)：原生并发 arena 测试。
- 官方上下文：[1](https://uxlfoundation.github.io/oneTBB/main/tbb_userguide/Controlling_Chunking_os.html)。
