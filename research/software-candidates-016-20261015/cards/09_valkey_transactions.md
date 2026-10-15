# 09_valkey_transactions：RESP3事务与持久化恢复服务

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/valkey-io/valkey/tree/cf5efa70192faedacb6741ee2a8f800d0482862f)；commit `cf5efa70192faedacb6741ee2a8f800d0482862f`。

许可观察：主源码 BSD-3-Clause，依据 COPYING；deps/LICENSES 需在离线打包时逐文件核对。

## 已有能力与拟出的题

Valkey 已有 multi.c、AOF 和真实 multi/protocol 测试；不是在完整可运行 Valkey 上要求补一个已存在命令。

构造带 RESP3 API 的事务型 KV 服务，明确 MULTI/EXEC/WATCH、多个客户端、错误与断连语义，再增加 crash-safe journal 与恢复；参考 Valkey 语义但使用独立新任务合同。

原题类别参照：postgres_wire_on_sqlite / stream_processing_engine：协议与持久状态系统。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 协议层、数据状态、事务队列、watch 失效、日志重放

- 提交源码和静态配置；judge 每次从固定数据集新建服务并执行确定的客户端事件序列

## 参考与迭代评分

用固定 Valkey 生成命令级参考，独立小状态机验证事务；任务自定义 journal 必须有独立恢复不变量，不用参考自身序列化结果充当 oracle。

拟评分维度：

- RESP3 编码/错误

- 事务排队与执行

- 多客户端 WATCH 失效

- 断连及错误隔离

- journal 截断与崩溃恢复

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 单客户端命令后处理排队错误、watch 变化与跨客户端交互

- 完成基础持久化后处理部分 journal、崩溃点和恢复重放

最强廉价基线：测系统 redis/valkey 直接代理或嵌入现成服务器能否满足新合同；正常服务依赖若足以解题则此版本不合格。

先做的否证探针：先写不依赖 socket 时序的事件调度器，给出事务/崩溃恢复的最小跨模块链；确保不是字符串字典 toy。

构造风险：

- 不得把不可控墙钟 TTL、并发调度当隐藏难点；需要可注入逻辑时间

- 旧服务器的命令集合很大，必须明确子集

- 正常可用完整服务带来的 shortcut 需先筛

## 实际取得的源码证据

- [事务执行真实入口](https://github.com/valkey-io/valkey/blob/cf5efa70192faedacb6741ee2a8f800d0482862f/src/multi.c#L183)；本地 [`sources/09_valkey_transactions/files/src/multi.c:183`](../sources/09_valkey_transactions/files/src/multi.c)。

- [持久化加载入口](https://github.com/valkey-io/valkey/blob/cf5efa70192faedacb6741ee2a8f800d0482862f/src/aof.c#L610)；本地 [`sources/09_valkey_transactions/files/src/aof.c:610`](../sources/09_valkey_transactions/files/src/aof.c)。

- [真实事务回归素材](https://github.com/valkey-io/valkey/blob/cf5efa70192faedacb6741ee2a8f800d0482862f/tests/unit/multi.tcl#L12)；本地 [`sources/09_valkey_transactions/files/tests/unit/multi.tcl:12`](../sources/09_valkey_transactions/files/tests/unit/multi.tcl)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/09_valkey_transactions/manifest.json)。[完整 Git 文件树索引](../sources/09_valkey_transactions/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

