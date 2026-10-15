# 15_jq_composition：流、作用域、递归与错误前缀的CLI兼容

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/jqlang/jq/tree/71c2ab509a8628dbbad4bc7b3f98a64aa90d3297)；commit `71c2ab509a8628dbbad4bc7b3f98a64aa90d3297`。

许可观察：源码 MIT 风格许可；COPYING 声明 docs 为 CC BY 3.0，不能把手册按 MIT 再分发。

## 已有能力与拟出的题

jq 已有完整解释器和测试；旧 Python 小样的 84 个例子不足以覆盖组合语义。新增 profile 要重建语法/语义范围，不是随机重复旧例子。

在明确语言/进程内 API 合同下实现 JSON filter 引擎和 CLI，覆盖流式组合、词法作用域、递归、reduce/foreach、更新路径及错误前缀；按固定 jq 1.7.1 行为裁剪范围。

原题类别参照：git_rewrite_in_zig / libexpat_x86_assembly：行为兼容的重实现。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- parser→作用域/求值器→流/错误→CLI

- 可嵌入 API 必须为真实需求；不得临时设置语言限制仅用于阻止正常解法

## 参考与迭代评分

隔离官方 jq 1.7.1，生成有类型/范围限制的 AST 组合，固定输入；结合变形关系与错误产生前的输出序列核对。非确定操作不纳入。

拟评分维度：

- stream cardinality 与顺序

- 作用域/closure/递归

- reduce/foreach

- path update 与缺失/null

- 错误前缀、退出码及进程内 API

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 简单 filter 后处理 binding 与 generator 多输出的乘积语义

- 处理递归/异常/更新路径在嵌套组合中的交互

最强廉价基线：直接调用现成 jq 或 libjq wrapper；若目标只是 CLI 兼容且环境/依赖允许，包装本来就是有效解，路线要换合同或淘汰，不能事后禁用。

先做的否证探针：拿旧实现对新生成的有界 AST 组合做语义差分，同时测正常 libjq wrapper；先确认新增合同有实际缺口。

构造风险：

- 恢复上游可复制实现的记忆风险

- 完整 jq 范围过大，裁剪得太小又会早满

- 性能和语言约束必须有实际可嵌入场景依据

## 实际取得的源码证据

- [多输出与错误组合](https://github.com/jqlang/jq/blob/71c2ab509a8628dbbad4bc7b3f98a64aa90d3297/tests/jq.test#L177)；本地 [`sources/15_jq_composition/files/tests/jq.test:177`](../sources/15_jq_composition/files/tests/jq.test)。

- [真实回溯执行语义](https://github.com/jqlang/jq/blob/71c2ab509a8628dbbad4bc7b3f98a64aa90d3297/src/execute.c#L515)；本地 [`sources/15_jq_composition/files/src/execute.c:515`](../sources/15_jq_composition/files/src/execute.c)。

- [文档与源码许可区分](https://github.com/jqlang/jq/blob/71c2ab509a8628dbbad4bc7b3f98a64aa90d3297/COPYING#L25)；本地 [`sources/15_jq_composition/files/COPYING:25`](../sources/15_jq_composition/files/COPYING)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/15_jq_composition/manifest.json)。[完整 Git 文件树索引](../sources/15_jq_composition/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

旧 profile：samples/software-multiline-001/06_jq；旧参考 1 分是 host 行为小样，不是完整 jq 难度证据。

