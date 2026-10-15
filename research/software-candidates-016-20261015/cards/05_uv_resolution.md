# 05_uv_resolution：跨环境依赖解析与增量锁定

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/astral-sh/uv/tree/9385290f1bf895cb3f587118ce92cce9a0585f77)；commit `9385290f1bf895cb3f587118ce92cce9a0585f77`。

许可观察：Apache-2.0 OR MIT；实际离线包索引中的包逐项另查。

## 已有能力与拟出的题

universal lock、marker 分叉、workspace、lock 更新和冲突处理均已存在。新增合同必须明确超出 uv lock / --upgrade-package 的哪些输出和稳定性保证。

在 uv 中实现跨环境 lock 更新计划与机器可读解释：输入旧 lock 和变更，保持未受影响解稳定，解释 marker 分叉、受影响依赖及冲突；不是从零重新实现已有 universal resolver。

原题类别参照：Packer 插件/配置演进、依赖类型检查器：约束传播与兼容性。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- resolver、lock serialization 和新的 update-plan CLI/API

- 固定的本地 wheel/metadata 索引；不同 Python/platform marker 的离线目标矩阵

## 参考与迭代评分

用小图穷举所有合法解验证计划/解释；大图对照固定 uv 参考结果和声明的稳定性目标。新计划的完整参考分支待写。

拟评分维度：

- 各环境依赖解合法

- 不必要变更受控

- marker 分叉与合并

- 解释可追溯到输入约束

- 冲突诊断及 lock 可往返

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 单环境解之后处理 extras、workspace 和跨平台分叉

- 在正确性保持下减少锁文件扰动并保证解释与最终解一致

最强廉价基线：先调用现有 uv lock 再做 lock diff 和约束回溯；若这已满足合同，则是短脚本题，不应升级为长程。

先做的否证探针：用本地微型索引给出现有 uv + diff 的一个明确反例，并为小图计划写独立穷举检查器。

构造风险：

- 计划目标和最小变更的偏序需先定义，不能把所有无关升级都判错

- 包数据与 Rust 依赖尚未完整 vendor

- 索引规模本身不是推理难度证据

## 实际取得的源码证据

- [已有 universal resolution 文档](https://github.com/astral-sh/uv/blob/9385290f1bf895cb3f587118ce92cce9a0585f77/docs/concepts/resolution.md#L407)；本地 [`sources/05_uv_resolution/files/docs/concepts/resolution.md:407`](../sources/05_uv_resolution/files/docs/concepts/resolution.md)。

- [实际 resolver 实现](https://github.com/astral-sh/uv/blob/9385290f1bf895cb3f587118ce92cce9a0585f77/crates/uv-resolver/src/resolver/mod.rs#L53)；本地 [`sources/05_uv_resolution/files/crates/uv-resolver/src/resolver/mod.rs:53`](../sources/05_uv_resolution/files/crates/uv-resolver/src/resolver/mod.rs)。

- [真实 lock 回归入口](https://github.com/astral-sh/uv/blob/9385290f1bf895cb3f587118ce92cce9a0585f77/crates/uv/tests/lock/lock.rs#L45)；本地 [`sources/05_uv_resolution/files/crates/uv/tests/lock/lock.rs:45`](../sources/05_uv_resolution/files/crates/uv/tests/lock/lock.rs)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/05_uv_resolution/manifest.json)。[完整 Git 文件树索引](../sources/05_uv_resolution/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

