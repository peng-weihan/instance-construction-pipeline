# 难度与最强廉价基线

当前决定：构造可审阅的优化题草稿，性能价值与六小时难度继续 held_for_evidence。完整上游 starter 本来支持全部已有排序功能；当前正确性分上限只有 0.25，NOP 可在该部分饱和。这是明确的早饱和风险，不是任务难度通过。仅有参考快路径、静态包或正确性满分都不能证明长时增长。

首个真实基线为本地主机 x86_64 上固定源码的 release 构建；生产代码未改，增加真实物理算子驱动。构建命令、原始编译输出在 authoring/evidence/baseline-build.log。首轮输入切片与 LIMIT 0 驱动错误单独保留；修正后重新执行。最强普通配置扫描使用原生 batch size 1024/8192/65536、sort-in-place 阈值 0/1MiB/64MiB、已有 TopK 与分区 merge、低内存 spill；固定种子、规模与真实 elapsed_ns 均在 authoring/evidence/baseline-sweep.json，每个配置内部执行三次。每工作负载最小中位数只是该有限扫描内最强观察值，不宣称全局最优或公平跨机锚点。没有把更慢默认值作为人为奖励分母。

两条后续改进路径（均为假设）：

1. 宽 payload、高重复键及局部已有序输入：比较 gather、row 编码、run 检测成本与内存保留，改进 identity 之外的局部顺序复用；同时检查 UTF-8、NULL 与复合键，避免只优化整数。
2. 在统一内存池中协调 partition-local TopK、merge 预留、spill 输出批次与合并扇入，比较较大的 offset/K 与全排序的交界。改动必须维持真实 spill、内存释放及所有原生回归，不能以提高内存上限换取假加速。

当前参考只做完整 identity permutation 的 payload 零拷贝，不能证明这些路径均可获得稳定性能收益；对无序输入多一次 O(n) identity 检查也可能退化。最强调参可能完全吞掉该优化空间，届时应 hold/reject，而不是禁止配置或人为减慢基线。独立 PyArrow/DuckDB/外部排序 wrapper 即使正确，也不改变本题交付的真实 pinned Rust 算子；但引擎内部合法库和算法复用仍允许。

最便宜剩余否证：对已观察最强 ordinary 配置与 reference 做交错、独立进程、多次重复重放，加入更小/更大的 K、更多分区和随机 workload，记录父进程 wall、引擎 elapsed、峰值 RSS 与实际 I/O。若收益低于波动，或只能在唯一 ordered payload 案例出现且一般 workload 明显倒退，则拒绝把它升级为性能训练题。当前没有六小时教师、ARM、五次正式同快照重评分、性能归一化、独立第三方 oracle 复审或跨机稳定性结论。


已完成补充否证：`authoring/evidence/ordering-metadata-baseline.json` 的 10 个真实进程重放全部正确，生产 sort.rs 与固定上游逐字节相同。对保证全局有序的单分区源，`try_with_sort_information` 加正确属性缓存足以让现有 SortExec 跳过排序；这一普通配置必须作为已知有序场景的强 B。不能把未声明排序信息的路径当作所有场景的最强上游基线。参考 fast path 只对未提供元数据的有序批次有独立用途；当前还没有普通调参之后广泛、稳定的性能改进证据。保留当前冻结矩阵，不移除会削弱参考优势的场景、不禁止既有 metadata API。状态维持 held_for_evidence。
