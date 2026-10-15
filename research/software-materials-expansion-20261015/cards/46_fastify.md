# 46_fastify — 带插件作用域预算与资源清理的请求执行策略
- 来源：[fastify/fastify](https://github.com/fastify/fastify)；SHA `37df44a421817e7bb048fce834bf691abb0999d6`；M1 / `hold`。
- 已有：已有插件封装、作用域 hooks、handlerTimeout、request AbortController/signal、断连取消及 onRequestAbort/onTimeout；简单超时不是新功能。
- 拟任务缺口：拟扩展可组合执行策略：插件级并发/排队预算与 deadline 传递、等待队列取消、流式清理和可观察结果；是否只是薄插件待证明。
- 产品/子系统边界：交付 API 服务资源控制版本：重负载插件排队、公共路由独立，deadline 覆盖排队与 handler，断连撤销排队/下游工作；保留现有 handlerTimeout 与 hook 语义。
## 模块链与固定证据
- [`lib/route.js:534`](https://github.com/fastify/fastify/blob/37df44a421817e7bb048fce834bf691abb0999d6/lib/route.js#L534)：原生 handlerTimeout 已创建 AbortController 并在断连时 abort
- [`lib/context.js:47`](https://github.com/fastify/fastify/blob/37df44a421817e7bb048fce834bf691abb0999d6/lib/context.js#L47)：路由 context 保留 scoped lifecycle hooks 与 timeout
- [`docs/Reference/Encapsulation.md:6`](https://github.com/fastify/fastify/blob/37df44a421817e7bb048fce834bf691abb0999d6/docs/Reference/Encapsulation.md#L6)：插件 context 已定义 hooks/decorators 可见性
- [`test/hooks.test.js:3419`](https://github.com/fastify/fastify/blob/37df44a421817e7bb048fce834bf691abb0999d6/test/hooks.test.js#L3419)：原生测试覆盖 abort hook 的 root/child/route 顺序
## 组合场景
1. 受限插件内一个请求占位、第二个排队超时，公共兄弟路由继续服务且超时请求不进入 handler。
2. 客户端在排队或下游 fetch 中断开，等待项/资源及时清理，不影响同一 keep-alive 后续请求。
3. 流响应中途失败/断连，生成器 finally 和资源释放执行，hook 顺序及既有 timeout 错误保持契约。
## 基线与退出
- 强合法基线：已有 handlerTimeout/request.signal + scoped hooks + p-limit/AbortSignal.any 的普通插件；允许完整使用，先检查 Fastify 生态现成队列/限流方案。
- 首探/退出：先用插件组合实现排队 deadline、断连移除、stream 清理三场景；若无需通用新语义即满足则退出。不能以已有超时实现换名充数。
- 早期完成后的剩余假设：单路由队列成功后，嵌套插件策略继承/覆盖、排队耗时预算与并发释放仍可能未完成。
- 早期完成后的剩余假设：普通 JSON handler 正确后，流式响应、hijack、错误 hook 和 disconnect 竞态的清理/兼容仍需验证。
- 独立 oracle / 原生回归：独立 loopback 客户端/下游服务器记录真实连接与 handler 进入集合，资源探针观测泄漏；保留 hooks/plugin/stream/timeout 原生测试，inject 不能替代 socket 断连验证。
- 许可观察：根 LICENSE 为 MIT；第三方限流/队列插件许可另审。
- 离线/架构风险：预置固定 Node/npm 依赖；网络只 loopback，HTTP/1 首版；计时测试用 barrier/可控时钟，不能用微小 sleep 作为难度或正确性证据。
- 官方在线核对：[primary](https://github.com/fastify/fastify)；[primary](https://fastify.dev/docs/latest/Reference/Request/)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
