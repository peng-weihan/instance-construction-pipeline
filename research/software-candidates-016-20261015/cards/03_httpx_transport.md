# 03_httpx_transport：传输、重定向、认证与流式关闭的联合演进

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/encode/httpx/tree/b5addb64f0161ff6bfe94c124ef76f6a1fba5254)；commit `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`。

许可观察：BSD-3-Clause，依据 LICENSE.md；依赖另查。

## 已有能力与拟出的题

固定源码已有 auth flow、redirect chain、sync/async transport 关闭，以及取消时关闭连接的测试。不能把已有取消清理再包装成新任务。

给 HTTPX 增加明确的请求执行策略合同：重试预算、可重放 body、认证/重定向边界与结构化执行事件，同时覆盖同步和异步。这是新需求提案，不是已确认上游 bug。

原题类别参照：vault_sdk_resilience / litestar_infra_refactor：跨层资源与执行策略。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 修改 Client/AsyncClient 的执行链及公开配置

- 输出机器可读但不泄漏敏感头的事件；候选实现作为库被真实调用

## 参考与迭代评分

独立 scripted transport/loopback server 按事件序号返回响应；外部观测实际请求与 close 次数，冻结 clock 与 backoff。

拟评分维度：

- 重试和 redirect 共享预算

- 流式 body 的可重放性

- 跨 origin 认证边界

- 取消/异常时的关闭

- 事件语义与原 API 兼容

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 基础重试之后处理 auth challenge、redirect 和不能 rewind 的 body

- 处理异步取消、部分响应消费与连接释放的交互

最强廉价基线：tenacity 风格 wrapper 加 MockTransport 可能很快覆盖需求；允许正常依赖，先验证 wrapper，不能靠禁库制造难度。

先做的否证探针：把当前已有能力和拟增需求逐项对照，再构造一个最薄 wrapper；若不改执行链即满足合同则暂停此候选。

构造风险：

- 需求组合若缺乏共同原因，容易成为人为拼接

- 尚无固定的新需求参考实现或已复现缺陷

- 已有功能完备，早满风险高

## 实际取得的源码证据

- [现有认证执行链](https://github.com/encode/httpx/blob/b5addb64f0161ff6bfe94c124ef76f6a1fba5254/httpx/_client.py#L930)；本地 [`sources/03_httpx_transport/files/httpx/_client.py:930`](../sources/03_httpx_transport/files/httpx/_client.py)。

- [已有取消场景测试](https://github.com/encode/httpx/blob/b5addb64f0161ff6bfe94c124ef76f6a1fba5254/tests/client/test_async_client.py#L330)；本地 [`sources/03_httpx_transport/files/tests/client/test_async_client.py:330`](../sources/03_httpx_transport/files/tests/client/test_async_client.py)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/03_httpx_transport/manifest.json)。[完整 Git 文件树索引](../sources/03_httpx_transport/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

