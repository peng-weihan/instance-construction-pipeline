# 02_restler_recovery：真实campaign的崩溃恢复与状态一致性

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/microsoft/restler-fuzzer/tree/6d984deedbc54aad957fa3da0c7e9e5df23a2aee)；commit `6d984deedbc54aad957fa3da0c7e9e5df23a2aee`。

许可观察：MIT；另行固定实际被测服务及其许可。

## 已有能力与拟出的题

driver 已调用 saver，但固定版本 saver.save 直接 return，load 也提前返回默认状态。旧代码中的 pickle 路径不是已启用的生产恢复机制。

让 RESTler 的真实 BFS campaign 支持可恢复执行：持久化 generation、请求/资源 journal，在外部服务重启、响应丢失及进程崩溃后恢复一致状态。

原题类别参照：Schemathesis 工程演进类；相似的是框架状态与执行链改造，不复用原题需求。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- CLI→driver→checkpoint/journal 的真实入口

- 真实服务、资源创建/清理与重放边界；通过落盘代码文件提交，由 judge 每次新启动 campaign

## 参考与迭代评分

控制器在确定的请求序号注入故障，保存服务端审计记录，与不停机对照及独立资源状态检查比对。不能仅测 save/load 函数。

拟评分维度：

- checkpoint 原子性与损坏回退

- 恢复后的 BFS generation/覆盖语义

- 资源与依赖状态一致

- 重试/重放的重复副作用控制

- CLI 配置、并发和回归

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 持久化跑通后，解决响应丢失时请求是否执行的歧义及服务端资源复用

- 进一步解决多个请求序列、并发 worker、清理失败与 checkpoint 的交互

最强廉价基线：先试只移除 early return、修 pickle、加原子 rename 的基线；它若已覆盖所有评分，说明新题仍退化为小修复。

先做的否证探针：用实际 RESTler CLI 对真实 Polaris 服务完成一次按序号注入的 kill/restart；确认旧 component 高分不能通过这个完整场景。

构造风险：

- 旧小样只有组件闭环，正式 score 仍无效

- Polaris 本地曾缺 Java；需要实际 .NET/Java 服务构建链，不能换成 toy 服务冒充

- exactly-once 只有协议允许时才可要求，必须明确允许的幂等键与服务能力

## 实际取得的源码证据

- [真实 saver 入口；下方有 early return](https://github.com/microsoft/restler-fuzzer/blob/6d984deedbc54aad957fa3da0c7e9e5df23a2aee/restler/utils/saver.py#L12)；本地 [`sources/02_restler_recovery/files/restler/utils/saver.py:12`](../sources/02_restler_recovery/files/restler/utils/saver.py)。

- [driver 加载 checkpoint 的调用](https://github.com/microsoft/restler-fuzzer/blob/6d984deedbc54aad957fa3da0c7e9e5df23a2aee/restler/engine/core/driver.py#L695)；本地 [`sources/02_restler_recovery/files/restler/engine/core/driver.py:695`](../sources/02_restler_recovery/files/restler/engine/core/driver.py)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/02_restler_recovery/manifest.json)。[完整 Git 文件树索引](../sources/02_restler_recovery/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

旧 profile：samples/software-multiline-001/02_restler；组件参考 6/6 不能迁移为完整题 Oracle。

