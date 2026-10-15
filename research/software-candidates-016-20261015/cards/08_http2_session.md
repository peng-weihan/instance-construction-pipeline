# 08_http2_session：HTTP2帧、HPACK与会话状态机

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/nghttp2/nghttp2/tree/7e10fcf3c58e692902939bab8f898bdd9ec9cff7)；commit `7e10fcf3c58e692902939bab8f898bdd9ec9cff7`。

许可观察：MIT，LICENSE 指向 COPYING；测试依赖另查。

## 已有能力与拟出的题

nghttp2 已完整实现协议并有 HPACK/session 测试。素材用于参考和构造状态轨迹，不是提出 nghttp2 当前缺这些功能。

构造不依赖真实互联网的 HTTP/2 会话核心：分片收包、HPACK 上下文、stream 生命周期、flow control、GOAWAY/RST/CONTINUATION 等交互，暴露进程内事件 API。

原题类别参照：postgres_wire_on_sqlite / quic_transport_stack：有状态协议实现。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 字节输入→帧→连接/stream 状态→事件输出

- 固定 RFC 子集、错误优先级和应用侧消费/窗口更新 API

## 参考与迭代评分

固定 nghttp2 的事件适配参考，另用协议不变量检查器验证窗口、stream 状态及错误范围；网络端点只在 judge 的本地进程中运行。

拟评分维度：

- 帧增量解析

- HPACK 上下文一致

- stream/connection 错误范围

- flow control

- 多 stream 与关停交互

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 单 stream 后处理多 stream、窗口耗尽和部分消费

- 进一步处理 header continuation、动态表与关停竞态

最强廉价基线：hyper-h2 或 nghttp2 binding 常规 wrapper 可能立即解决全部合同；需要先做，不能通过禁止正常依赖掩盖这一点。

先做的否证探针：先建立两段互相影响的 HPACK/flow-control 状态轨迹，同时实现现成 binding 基线；比较完整能力范围。

构造风险：

- 若只是 trace decoder，工程量会很小

- 若加入真实网络时序，会损伤确定性，应按事件驱动调度

- 完整 RFC 范围不明确则无法判断完成度

## 实际取得的源码证据

- [跨帧 header 状态测试](https://github.com/nghttp2/nghttp2/blob/7e10fcf3c58e692902939bab8f898bdd9ec9cff7/tests/nghttp2_session_test.c#L48)；本地 [`sources/08_http2_session/files/tests/nghttp2_session_test.c:48`](../sources/08_http2_session/files/tests/nghttp2_session_test.c)。

- [显式流控测试](https://github.com/nghttp2/nghttp2/blob/7e10fcf3c58e692902939bab8f898bdd9ec9cff7/tests/nghttp2_session_test.c#L47)；本地 [`sources/08_http2_session/files/tests/nghttp2_session_test.c:47`](../sources/08_http2_session/files/tests/nghttp2_session_test.c)。

- [独立 HPACK 测试](https://github.com/nghttp2/nghttp2/blob/7e10fcf3c58e692902939bab8f898bdd9ec9cff7/tests/nghttp2_hd_test.c#L68)；本地 [`sources/08_http2_session/files/tests/nghttp2_hd_test.c:68`](../sources/08_http2_session/files/tests/nghttp2_hd_test.c)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/08_http2_session/manifest.json)。[完整 Git 文件树索引](../sources/08_http2_session/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

