# RESTler 可恢复执行与资源生命周期

在完整 RESTler 引擎中实现 roadmap.json 七组需求，目标预算 6 小时。旧功能保持可用；只有显式配置 execution_policy 时启用新行为。配置键、重试时间、截止边界和清理规则见 interface.md。不是只写一个不被真实引擎调用的 helper。

实现以下公开接口：
- engine.core.execution_policy：validate_policy(config)、resolve(config,method,path)、Context(policy,clock=None,rng=None,cancelled=None)、CURRENT ContextVar、LeaseGraph(resources)。
- Context 提供 policy、clock、rng、deadline、events、terminal；clock 有 monotonic()/wall()/sleep(seconds)。terminal 为 succeeded/failed/timed_out/cancelled。
- LeaseGraph：created(id,refs=1)、acquire(id)、release(id)、cleanup(delete,context)。delete(id,remaining_seconds) 返回布尔成功；cleanup 返回 (deleted_ids,retained_ids)。资源规格为 id、parents 列表。
- engine.core.resilient_workflow.execute_workflow(spec,context=None)：按依赖顺序用真实 request_utilities.send_request_data/try_async_poll 创建资源，登记 dependencies.set_variable_no_gc，失败时回收已创建资源，返回 completed/failed/deleted/retained/events。
- workflow 的每个资源有 id、parents、request、delete_request，可选 value 和 leases。一个 workflow 持有一个 lease；结束时释放自己的 lease，外部 lease 保留。
- engine.tools.replay_execution.replay(records,policy)，以及既定 CLI。每条 record 有 request、responses（raw/success/elapsed）、wall、seed；返回规范化事件列表。输入可以包含认证头，输出事件必须脱敏。

接入 RestlerSettings 的 execution_policy 配置与原有 send_request_data、try_async_poll 调用路径。每个发起请求生成上下文，并通过 response._execution_context 传给轮询；CURRENT 显式指定时复用它。创建请求、轮询与最终 GET 共享 deadline。取消后仍允许独立清理预算。示例探针见 probe.py；注入的 transport 是替代外部服务，真实引擎调用链仍须经过。

提交 /workspace/repo/restler 的目录快照，根目录直接包含 restler_settings.py 和 engine/。七组权重依次为 .10/.15/.15/.15/.20/.10/.15。每组按行为检查通过比例计分；评分器在外侧记录真实 transport 调用与等待，返回具名失败项。
