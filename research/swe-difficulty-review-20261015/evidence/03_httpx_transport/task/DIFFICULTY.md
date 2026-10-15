# 难度证据和剩余假设

本题是 constructed_unverified 草案，尚无六小时难度结论。真实仓库规模、作者新增代码行数、参考满分、静态 schema 检查均不构成难度接受依据。

最强已实测的独立廉价方案是原生 Client 外的 send retry loop，以及重试当前 transport 的 wrapper（均在参考实现前编写，见 baseline_probe.py 与 cheap-baseline.json）。随后还用真实 tenacity 9.1.2 重跑这两种集成，得到相同的三次 dispatch 预算失败；tenacity 和原生构建工具也已封装到公开离线依赖中，未禁用正常工具。outer 在 redirect→503 后重启原始 URL；transport wrapper 保持当前 hop，但无法天然共享 auth/redirect 的逻辑预算。两者在 budget=2 场景实际进入三次；真实流 transport 的二次消费抛 StreamConsumed。MockTransport 默认 Request.read() 缓存会遮住这个问题，所以 verifier 不只靠它。HTTPTransport(retries=...) 原本支持连接层重试，不提供本题逻辑 send 的全部新合同。这些结果只否证已跑的薄实现，不证明所有 wrapper 路线不可能；允许使用 tenacity 等正常工具或更完整的 wrapper/subclass。

starter 本身保留大量原生行为和配置验证，最终本地 NOP 得分约 0.46746。分数没有强行归零；这既说明可用起点，也说明早满风险高。初版 scorer 曾错误地把 trace 当成所有组的共同前置，作者在构造阶段解耦它，使真实预算/重放等进展能够独立得分；旧证据保留，正式冻结版本在 score-spec.json。没有教师分数被改写。

两个具体后续改进路径仍有共同的执行状态原因：一是把 auth re-yield、307 保体 redirect、partial/overflow stream、transport Request.read() 旁路统一进懒惰 replay ledger，并保证 POST→GET 不被旧 body 阻断；二是把同步/异步错误、取消、discard close、流式返回和并发/嵌套 send 的作用域统一，最后用外部 transport 轨迹核对结构化事件。这些都能交付独立生产代码并反映到语义分组，不能据此推算模型必须花多久。

最便宜的剩余否证是从公开 starter 单独实现 ContextVar + budget-aware transport wrapper + 有界 tee，保持原 auth/redirect，再跑同一冻结 verifier；如果这条合理薄扩展很快达到满分，应 hold/reject 六小时用途，不禁止该工具路线、不加无关需求。真实参考只有约三百行生产新增代码，强模型早饱和完全可能。另需没有参考暴露的独立合同审阅、更多自定义 auth/嵌套异步取消审计，以排除自证遗漏。

当前可达性：本地 reference 在冻结语义输入达到 1；两个参考派生 near-miss 分别去掉缓存上限/foreign auth strip，表现为对应组下降。这两者是 mutation 检查，不是独立便宜解，也不证明参考最优或六小时增长。评分无性能项，未虚构吞吐/延迟锚点。ARM、实际固定镜像、Harbor native/周期集成、三条六小时轨迹均未运行；本轮用户明确延期，不启动教师来补它们。
