# 难度与后续增长假设

本题已构造，六小时潜力仍是未标定假设。没有启动教师，也没有以代码行数、测试
数量、Oracle=1 或本地运行时长宣称难度接受。

卡片要求的廉价强基线已实际尝试：仅去掉 saver early return、修二进制 pickle
读写、fsync + atomic rename，原生 CLI 在 generation 1 因动态 grammar parser
无法 pickle 失败，见 `../evidence/cheap-native-gc.log`。继续加入常规模块注册
修复后，独立 cheap-plus 可以在真实博客服务上不中断完成 26 个操作、剩余 14 个
资源；它不是从私有 gold 复制而来。这说明“pickle 根本不可能工作”并非成立。

为强基线加入简单 CLI 和固定 checkpoint 目录后，真实服务第 2 个已提交操作处
杀死进程并重启服务，再恢复：exit=0，但执行 28 个操作、剩余 16 个资源，两个
已生效 POST 被重复执行。日志和服务 audit 见
`../evidence/cheap-crash-result.log`、`../evidence/cheap-crash-service/`。
它能保存 frontier，仍不能解决尚未形成 generation checkpoint 的业务副作用。
未禁止 pickle 以外的普通持久化工具来制造难度；题面选择不可执行格式是完整性
和恢复契约。没有证明某个成熟库不能显著缩短实现时间。

本任务的耦合点是 native BFS 重放与服务效果边界。持久化成功并不意味着请求已
被确认；native response parser 的动态 ID、UUID 生成、重复同体请求的逻辑身份、
HTTP 内部重试与跨进程恢复必须一致。参考采用 durable response replay，通过
原生算法重建 frontier 和监控，而非直接 pickle 内部对象。

两条具体的后续改善路径是：

1. 在能恢复 generation 的实现上，将 journal 的 intent/result 和 transport 内
   重试绑定同一 operation key，补齐 committed-before-response 故障、删除和
   resource ID 重建；产物是传输层及 driver 状态边界的源码，可通过 audit/DB
   差异定位，能体现创建、依赖与删除组的部分进展。
2. 在基本 wire replay 上覆盖原生 UUID/UUID suffix 的生成顺序，再补齐损坏尾部、
   原子 receipt、配置内容绑定与跨进程锁；产物是持久格式及 CLI 配置边界实现，
   能独立提升 UUID、integrity、configuration 和 ownership 组。

这些路径是可观察的语义改善，不表示它们会耗费某个指定小时数。当前参考实现
相对紧凑，顺序 BFS + response replay 可能很快覆盖合同，早期饱和风险明显；异步
GC、多 worker、服务事务中间崩溃不在本版 supported profile，不能把未来设想算成
本题现有难度。两个 near-miss 是 gold mutation，只证明测试有区分力，不是廉价
独立解法证据。权重冻结；不能为满足增长曲线临时改分母。

最便宜的下一步否证是仅向独立实现者提供公开环境，允许使用普通持久化库和
现有 reconnect，在固定本地快照下检查 response-replay 方案是否快速满分；随后
才是正式 21600 秒校准。本轮禁止该教师步骤，保留 constructed_unverified 状态。
ARM、原生 Harbor 双入口以及容器重建也需要后续实测，本地 UID 和分数证据仅
适用于已记录的 Linux host 环境。
