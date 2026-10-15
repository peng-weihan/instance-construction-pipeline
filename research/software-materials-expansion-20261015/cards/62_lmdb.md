# 62_lmdb LMDB 快照读与持久事务写的页复用效率

- 路线：M3；优先级：`hold_until_baseline`。素材候选，未构题/构建/运行/校准。
- 固定源码：`LMDB/lmdb@253ba5219172531b719bc14fee6b4aa1a2a5c4a5`；源码哈希/清单见 `../sources/62_lmdb/manifest.json`。
- 完整候选范围：事务/快照→B+tree cursor→copy-on-write/空闲页回收→持久提交→重开读取；固定 durability、读者生命周期和磁盘预算。
- 原题锚点：`exchange_core_throughput`；仅借难度机制，不承诺同等运行难度。
- 已有能力：已有 mmap/MVCC/串行写、loose page/FreeDB 页复用与 oldest reader 限制；不是给简易 KV 加事务。
- 拟议缺口：未证实缺口：合理事务批次/mapsize/page/读者复用后，碎片化和长期读者约束下页搜索/回收是否仍有空间。

## 三类工作负载/工作流

- 读密集随机/范围：零拷贝局部性与页缺失
- 批量小事务/大值：同步成本、overflow 页与吞吐
- 长寿命快照+反复更新：保留页/碎片与写延迟

- 最强正常基线：优化构建、合理 mapsize/事务批次/游标复用与合法顺序写提示；强基线保留合同要求的同步，不用 NOSYNC/MAPASYNC 偷换 durability。
- 首探/否证：固定存储和 fsync 合同，先扫正常配置、区分冷/热 OS cache；若收益只来自少同步/结束必要快照/缓存状态则撤销。
- 正确性 oracle：冻结上游+内存有序映射校对每次读写/abort/快照历史，重开校对；独立进程崩溃注入仅在后续容器验证。原生 mtest 是回归素材，不是完整耐久 oracle。
- 测量计划：固定硬件/CPU/内存/存储与 seed，分离准备/实现执行；交错重复测正确结果的时间、RSS/分配及特定资源，记录噪声与跨 seed 泛化。奖励上下端点均未测；上游宣传倍率不是本题收益。
- 后续结构假设 1：强配置后若连续页范围搜索/合并仍耗时，研究 free page 索引或搜索顺序；必须遵守 oldest snapshot。
- 后续结构假设 2：强配置后若 COW/overflow 复制和 cursor 更新仍耗时，研究批量布局/页操作，保留提交和崩溃语义。
- 离线：C/Make/pthread 与真实支持 mmap/fsync 的本地文件系统；预置生成数据；未编译。
- 许可观察：libraries/liblmdb/LICENSE 为 OpenLDAP Public License 2.8，非 BSD/MIT；发布包须保留 COPYRIGHT/条款。
- 平台风险：页大小、对齐、mmap 和内存模型在 ARM/x86 不同；分平台读写/崩溃验证，不能用 RAM disk 外推磁盘。

## 源码与官方证据

- [libraries/liblmdb/mdb.c:2704](https://github.com/LMDB/lmdb/blob/253ba5219172531b719bc14fee6b4aa1a2a5c4a5/libraries/liblmdb/mdb.c#L2704)：已有 loose/FreeDB 分配与连续范围搜索。
- [libraries/liblmdb/mdb.c:2651](https://github.com/LMDB/lmdb/blob/253ba5219172531b719bc14fee6b4aa1a2a5c4a5/libraries/liblmdb/mdb.c#L2651)：回收受最老活动快照约束。
- [libraries/liblmdb/mtest.c:24](https://github.com/LMDB/lmdb/blob/253ba5219172531b719bc14fee6b4aa1a2a5c4a5/libraries/liblmdb/mtest.c#L24)：原生事务插入、commit 和 cursor 遍历测试。
- [libraries/liblmdb/LICENSE:1](https://github.com/LMDB/lmdb/blob/253ba5219172531b719bc14fee6b4aa1a2a5c4a5/libraries/liblmdb/LICENSE#L1)：许可版本 2.8。
- 官方上下文：[1](https://www.symas.com/lmdb.php)。
