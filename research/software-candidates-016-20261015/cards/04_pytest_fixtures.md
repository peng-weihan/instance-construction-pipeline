# 04_pytest_fixtures：fixture生命周期、动态收集与插件交互

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/pytest-dev/pytest/tree/c9c19f8e62c12834ad83193a1869cc82fe9c700e)；commit `c9c19f8e62c12834ad83193a1869cc82fe9c700e`。

许可观察：MIT；第三方插件许可和版本需独立固定。

## 已有能力与拟出的题

pytest 已有 fixture 缓存、依赖 finalizer 注册、缓存失效与多个 finalizer 异常处理；本候选增量是一个公开、稳定且不扰动行为的诊断合同。

实现 fixture 执行图与失效原因诊断：在参数切换、动态 getfixturevalue、setup/teardown 失败和插件 hook 下，输出可复现的依赖及清理事件。

原题类别参照：copier_modular_refactor / schemathesis_config_modernization：开发工具跨层演进。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- fixture 执行器、收集/报告与 plugin hooks

- 提交可安装源码，judge 在多个子进程收集行为和诊断，不能只分析静态测试文本

## 参考与迭代评分

独立 fixture 体写事件日志，对照实际 setup/teardown 次序；正常 pytest 运行是行为基线，新增诊断需要独立期望生成器。

拟评分维度：

- 依赖关系含动态请求

- 缓存命中/失效原因

- 异常后的 finalizer 顺序

- plugin hook 与报告一致

- 开启/关闭诊断时行为不变

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 简单 DAG 后处理动态 fixture 和参数缓存失效

- 处理多个 teardown 异常、跨 scope 依赖及 plugin 重入

最强廉价基线：纯 pytest plugin 可以直接观察很多 hooks；先实现常规 plugin 基线，若已近满则无需改 core，也应降低此路线优先级。

先做的否证探针：用现成 hooks 编写最小诊断 plugin，并验证它是否能区分实际缓存失效和重复 finalization；先证实 core 改造必要性。

构造风险：

- 目前是新诊断需求，不是复现完成的真实 bug

- 容易把测试条数误当工作量

- 插件版本组合多，必须冻结实际支持边界

## 实际取得的源码证据

- [已有 finalization](https://github.com/pytest-dev/pytest/blob/c9c19f8e62c12834ad83193a1869cc82fe9c700e/src/_pytest/fixtures.py#L1206)；本地 [`sources/04_pytest_fixtures/files/src/_pytest/fixtures.py:1206`](../sources/04_pytest_fixtures/files/src/_pytest/fixtures.py)。

- [已有缓存和依赖执行](https://github.com/pytest-dev/pytest/blob/c9c19f8e62c12834ad83193a1869cc82fe9c700e/src/_pytest/fixtures.py#L1231)；本地 [`sources/04_pytest_fixtures/files/src/_pytest/fixtures.py:1231`](../sources/04_pytest_fixtures/files/src/_pytest/fixtures.py)。

- [fixture scope 文档](https://github.com/pytest-dev/pytest/blob/c9c19f8e62c12834ad83193a1869cc82fe9c700e/doc/en/explanation/fixtures.rst#L79)；本地 [`sources/04_pytest_fixtures/files/doc/en/explanation/fixtures.rst:79`](../sources/04_pytest_fixtures/files/doc/en/explanation/fixtures.rst)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/04_pytest_fixtures/manifest.json)。[完整 Git 文件树索引](../sources/04_pytest_fixtures/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

