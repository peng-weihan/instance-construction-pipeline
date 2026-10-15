# 01_openapi_streaming：流式SDK、取消与资源生命周期

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/openapi-generators/openapi-python-client/tree/0a283fe21eeaa23046faf622d4ff4b2c826d2edb)；commit `0a283fe21eeaa23046faf622d4ff4b2c826d2edb`。

许可观察：MIT；保留 LICENSE 和贡献者声明。

## 已有能力与拟出的题

已有 sync/async API、认证 client、multipart 与 client 生命周期；CHANGELOG 已记载多次 multipart 修复。这里的新需求是联合合同，不能把上述现有能力统称为缺失。

为真实 Python SDK 生成器增加一个完整的流式端点合同：同步/异步 NDJSON 迭代、取消与关闭、端点认证覆盖；再验证它与 multipart 模型编码及共享 client 的交互。

原题类别参照：schemathesis_datagen_pipeline / reporting_observability：改造框架生产代码。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 生成器解析/模型层、Jinja 模板、生成包的公开签名

- 在离线本地服务上执行生成后的 SDK；只改内部 schema helper 不算完成

## 参考与迭代评分

先写独立 HTTP 观测器记录请求、迭代时序与关闭事件；参考分支需真正生成并运行包，不能用与 candidate 相同 helper 自证。旧参考只覆盖旧 profile。

拟评分维度：

- 逐记录流式交付且不预读完整响应

- 正常/异常/取消的资源关闭

- sync/async 与类型签名一致

- 匿名/认证覆盖且无凭据串用

- multipart 与历史生成回归

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 已有流式 happy path 后，处理分块 UTF-8、半条记录、取消与复用连接的交互

- 完善 auth 覆盖、文件数组及多媒体类型与生成导入的联合兼容

最强廉价基线：给作者一个直接改模板、复用 httpx.iter_lines 的强基线；若几处模板修改即可过完整联合合同，缩小优先级，不能靠加同类样例保住难度。

先做的否证探针：先在固定 commit 复现 ROADMAP 中的具体案例，再用最小 stream 模板补丁跑完整端到端行为矩阵。

构造风险：

- issue 状态不能代替固定版本复现；multipart 部分已实现

- NDJSON 是本批拟定合同，尚无该合同的完整参考分支

- 完整离线依赖与隐藏集尚未冻结

## 实际取得的源码证据

- [真实端点模板和解析入口](https://github.com/openapi-generators/openapi-python-client/blob/0a283fe21eeaa23046faf622d4ff4b2c826d2edb/openapi_python_client/templates/endpoint_module.py.jinja#L81)；本地 [`sources/01_openapi_streaming/files/openapi_python_client/templates/endpoint_module.py.jinja:81`](../sources/01_openapi_streaming/files/openapi_python_client/templates/endpoint_module.py.jinja)。

- [已有 multipart 改动历史](https://github.com/openapi-generators/openapi-python-client/blob/0a283fe21eeaa23046faf622d4ff4b2c826d2edb/CHANGELOG.md#L287)；本地 [`sources/01_openapi_streaming/files/CHANGELOG.md:287`](../sources/01_openapi_streaming/files/CHANGELOG.md)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/01_openapi_streaming/manifest.json)。[完整 Git 文件树索引](../sources/01_openapi_streaming/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

旧 profile：samples/software-multiline-001/01_openapi；旧 schema profile 本地满分但已拒作长程题；r2/ROADMAP.md 只有新设计。

