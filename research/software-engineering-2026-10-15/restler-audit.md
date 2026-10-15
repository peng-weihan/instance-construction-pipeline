# RESTler 早满分审计：静态验收范围先于长时难度

当前证据支持两件事：历史 `agent-4` 快照在 **848.615 秒（14 分 8.615 秒）**取得 1.0；本地 007 题包的评分目标明显小于题面描述的完整工程目标。**没有取得首个满分模型补丁，不能断言模型已完成完整生产集成，也没有证据证明模型利用了评分漏洞。**

本次只读检查题包、运行脚本与已有历史摘要，未修改题包、评分器或旧轨迹，未执行模型、容器、攻击反例或并发审计。相关目录和祖先未发现适用的 AGENTS.md。远端只读 SSH 被本地沙箱阻止，升级请求中断；按任务要求停止远端取证。没有读取账号认证内容。

## 证据与版本边界

- 设计审计对象：`samples/long-horizon-built-007/restler_resilient_execution/`，以下以 `S/` 简写。
- 历史记录：`runs/remaining-three-001/current-review/restler/history.json`，以下以 `H` 简写；曲线表为同级 `all-curves/submissions.csv`。
- 运行实现：`agent_eval/restler-001/`。`prepare_remote.py:7,15–17` 指向远端 007 smoke 产物并复制其 public/solution/verifier；`launch_agent.py:4,22–29` 实际运行的是远端 `task-r4`，启动时核对 task/context/image hashes。
- **本地尚无该次运行 manifest/hash 全集可供核对**，所以无法证明本地 007 与历史 task-r4 实际评分镜像逐文件相同。失败项名称与本地用例吻合，提供关联证据；下文覆盖缺陷是对本地 007 的确定结论，对历史早满分仅构成有依据的解释，尚非完整因果归因。
- 证据提要及本地源文件 SHA256 已保存为 [local-evidence-summary.json](restler-evidence/local-evidence-summary.json)。它是从既有资料提取的审计摘要，不是新取回的模型轨迹。

## 原题想考什么，实际在考什么

题意要求在完整 RESTler 引擎接入七组能力：策略继承/校验、重试、幂等、异步统一 deadline、依赖 DAG/lease 清理、脱敏事件、离线 replay；强调真实调用链、原功能兼容，目标预算六小时。规定新增 API、Context 字段与 terminal 值，以及请求/轮询/最终 GET 共用 deadline（`S/instruction.md:3–15`、`S/public/interface.md:1–11`）。明确 API 和提供 probe 减少接口猜测是合理设计，但不能据此推断有六小时工作量。

本地 grader 的全部得分来源是按 suite 遍历静态 JSON case，每个 case 新建一个 Python probe worker，判定指定返回值，再按七组通过比例加权（`S/verifier/grader.py:24–63`）。运行包装器明确 `grade(candidate,'feedback')`（`agent_eval/restler-001/judge_entry.py:9–12`）。

| 评分组 | feedback 检查数 | 实际观测 | 完整目标中尚未充分证明的部分 |
|---|---:|---|---|
| policy | 7 | 两个覆盖值、五个非法配置 | 规范化路径组合、完整类型边界、错误配置路径；正常请求未显式 Context 时的配置贯通 |
| retry | 6 | 503退避、次数上限、Retry-After秒/日期/畸形、截止阻止等待 | jitter 数值/分布、连续时间与不同故障组合、真实网络与长序列 |
| idempotency | 8 | 六种方法、显式 key、一次不安全网络失败 | key 生成/稳定性/作用域、复杂重放与副作用一致性 |
| async | 3 | 一条完成+最终GET、一条共享截止、开始即取消 | 多轮轮询中取消、异步错误组合、并发/Context 隔离 |
| leases | 6 | 四个直接 graph case、两个两资源 workflow | 原生 GC/create-once 调用链、真实删除失败与重试、正清理预算耗尽、复杂 DAG/外部 lease 交互 |
| trace | 2 | 正常重试与失败的事件键/序号、两个固定秘密哨兵 | 因果 ID、事件内容/时间正确性、跨请求 trace、任意认证值脱敏 |
| replay | 4 | 同一函数同输入执行两次相等、普通请求成功、两条 legacy smoke | 与真实运行轨迹逐字段等价、多个record、CLI输出、replay对不同输入的敏感性 |

全体只有 **36 个 feedback case**；另有 7 个 public case 与 7 个 audit case。audit 不由上述评分入口调用，不能把“目录里有 audit”当作该次满分已通过独立终评。具体 case 位于 `S/private/behavior_cases.json:192–1072`，audit 从第 1073 行开始。清单和分组统计见本地证据摘要。

三个最明确的覆盖缩减：

1. **没有执行完整上游回归或 campaign。** probe 直接调用 `send_request_data/try_async_poll`，替换 socket 与 clock（`S/verifier/probe.py:14–31,53–59`）；workflow 由 probe 直接调用新增入口（第45–47行）。这确实触及部分真实引擎函数，但不验证正常 rendering、GC、fuzzer 入口能到达新增能力。`check_plan.json` 声明的三层检查只是计划，grader 没有消费这个文件。
2. **replay 的语义未被验收。** probe 仅计算 `a=replay(...); b=replay(...)` 并返回 `same`（第48–51行），case 只要求 `same:true` 与 schema（`behavior_cases.json:986–1012`）。没有对照在线事件、预期事件内容、请求次数、等待、CLI 文件输出。jitter 虽出现在输入，却没有数值断言。参考实现提供了真实 send 调用与 CLI（`S/solution/reference/engine/tools/replay_execution.py:10–25`），但参考解做了什么不等于评分要求候选也做到。
3. **资源清理多为小图/理想删除。** 直接 lease probe 的删除回调恒返回 True（`probe.py:39–44`）。两条 workflow 覆盖小规模回滚/清理；唯一 audit 清理预算检查是预算为0（`behavior_cases.json:1185–1222`），不是随删除耗时耗尽的正预算。与“长时恢复和资源生命周期”相比，主要状态交互尚未展开。

## 已保存历史说明了什么

| 提交 | 快照时间 | 分数/通过率 | 当时具名失败项 |
|---|---:|---|---|
| agent-1 | 320.616s（5:20.616） | 0.8041667 / 31÷36 | deadline_blocks_sleep、rollback_via_restler、redacted_trace、trace_failure、replay_deterministic |
| agent-2 | 496.415s（8:16.415） | 0.8625 / 33÷36 | redacted_trace、trace_failure、replay_deterministic |
| agent-3 | 686.608s（11:26.608） | 0.8625 / 33÷36 | 同上 |
| **agent-4** | **848.615s（14:08.615）** | **1.0 / 1.0** | **空** |

来源 `H:3–120`；agent-4 的反馈完成时间是 **871.955s（14:31.955）**，评分用时23.327s。快照 SHA256 为 `121e9406e028f00a74845fbfde094bf7114ba32946bc933ed7c4040b2f9a4343`。记录标明 `snapshot_atomic:false`；这是该历史记录的属性，不据此推断分数无效。表中的 31/36、33/36 由历史通过率结合本地 suite 数推得，记录本身直接保存的是 pass_rate。

可确认的行为变化只有：最初5个失败项，第二次减少到3个 trace/replay 项，第四次这些判定项全部通过。不能从这张表还原具体修改了哪些函数、生产代码行数、是否补了测试、是否使用捷径。**首个满分快照的代码量和完整目标完成度目前未知。**后续多次记录仍满分，只能说明同一验收规则持续饱和；不能补足这些缺失证据。记录到约4小时处仍有 error/running 项，因此本摘录也不证明完整六小时最终验收已结束。

## 难度缺陷与漏洞风险应分开

**已证实的本地设计缺陷**是达满分所需的行为范围偏窄和语义覆盖不足：36个固定代表检查、函数级注入而非完整生产流程、trace/replay较弱断言。细粒度反馈本身是任务应有的机制；它应帮助解决真实工程问题，而不只是满足这些有限断言。历史在5分多钟已到0.804，最后0.1375仅来自三个 trace/replay 判断项，这与评分范围很快被覆盖的解释一致，但仍受前述版本绑定边界限制。最优分一旦到1，继续数小时无法从这套分数辨别更完整的生产实现。

**可以静态指出的风险，尚未证明本次被利用：** `matches` 对 trace 仅验证键集合/连续序号和两段固定哨兵（`grader.py:9–16`），不检查语义内容；replay 返回某种固定且合法的事件结构，在这些断言中无法与正确语义充分区分。probe 与候选模块在同一 Python worker 中，共用 stdout JSON 通道；controller 对 transport/wait有外侧记录（第37–55行），但其他 final 字段依赖 worker 返回（第42–46行）。因此“隔离隐藏答案文件”与“所有评分观察不可被候选影响”是两个不同保证。未执行绕过样例，未取得候选代码，**不能把这些风险写成已确认作弊或已利用漏洞**。

## 重建方向

1. **先冻结这次满分补丁作回归样本，再判断差距。** 保留 agent-4、starter、参考解、task-r4镜像与hash；对新增验收分别报告通过/失败。该取证本次未完成，不把推测替代补丁审查。
2. **以真实 RESTler 工作流作为验收入口。** 固定 OpenAPI fixture、可恢复有状态HTTP服务、真实 rendering/async/dependencies/GC 入口；公开快速 smoke，隐藏完整创建→依赖使用→取消/故障→清理流程。保留上游选定回归并锁定必需测试ID，单列兼容性门槛。
3. **从需求生成状态组合。** 系统覆盖方法×幂等key×网络/HTTP故障×重试/轮询×截止/取消；DAG规模、共享父节点、外部lease、删除失败/超时。只增加随机seed不够，必须先声明状态不变量与交互覆盖。
4. **提高语义判别力。** jitter校验固定RNG下精确延迟；trace校验事件因果/时间/脱敏；replay对照真实受控运行的规范化轨迹，并实跑CLI、多record和错误输入。清理检查实际删除调用、剩余预算、保留对象一致性。
5. **反馈评分与作者质量审计分开。** 作者审计集覆盖新状态组合，不能反复反馈后再称holdout；它用于检查题目质量，不取代正式评分，也不改变一次运行全部提交的best-of-run。用不完整实现、关闭策略、恒定replay、遗漏清理等定向反例核查评分区分力。得分按需求组/交互层定义，必需门槛防止只实现helper即可饱和。
6. **重新校准长时价值。** 题目与评分完善后，按既定六小时学习窗口记录固定时点的分数和完整集成结果。要求多运行几个小时本身不会提高任务难度。

本审计结论是：**本地007更像带权重的有限行为验收集；现有证据不足以把“14分钟拿满分”解释成“14分钟完成完整RESTler工程目标”，也不足以解释成“利用漏洞拿分”。**首要重建工作应是补足生产入口、交互状态和语义oracle，然后再讨论长时预算。
