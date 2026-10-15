# K07_WNTR · WNTR 水务韧性

状态：潜力 high / scope_probe；素材研究，未构题/运行/难度验收。
来源：[USEPA/WNTR](https://github.com/USEPA/WNTR/tree/11eec7d5bf0a9367ffe04d75707918f0c0a890a1)
固定版本：`11eec7d5bf0a9367ffe04d75707918f0c0a890a1`
来源单元：PDD水力仿真、管段关键性示例、Net3 INP与压力-需求测试
材料：[manifest](../sources/k07_wntr/manifest.json)，含文件树、原文URL和SHA256。

拟题：**供水故障的隔离修复与服务恢复计划**
给定管网、重点用户、破管事件、维修能力和可操作阀门，交付分阶段隔离/修复方案、供水影响评估及恢复优先级。
交付：阀门与维修时间表、节点服务损失表、重点用户达标检查、恢复曲线和建议依据。

自然难点一：关闭故障管既能隔离泄漏又可能切断关键用户，图连通不等于压力和实际供水达标。
自然难点二：多个修复动作与水箱/控制时序耦合，逐个静态管段排名不能替代阶段恢复评估。
正常基线：原生pipe_criticality单管关闭分析+按影响贪心修复，允许EPANET/WNTR和调度求解器正常使用。
首个探针：先复现PDD小例和Net3正常/故障完整仿真；比较单管贪心与阶段方案，明确不收敛返回状态。
降级/淘汰：若只关一管并抄官方关键性示例已达标则下调；若参考仿真不收敛且无可靠可行性标签则hold。

独立评分：judge私有模型重放阀门/维修动作，核对可行班组/预算；独立计算PDD实际供水、压力、重点用户服务和恢复时间，不信报告自报。
生成与划分：新生成管网拓扑、用户权重、相关故障与需水时序；保留可恢复性标签，按失效机制/网络结构分割。
谱系/污染：与旧MODFLOW地下水反演不同，是城市供水运营决策；EPANET水力引擎可共享但不同网络不自动算新来源。
离线与计算：Net3与小PDD测试已取；WNTRSimulator主要水力，水质/污染需另引EPANET接口，不据当前材料承诺；离线依赖/运行未测。
许可观察：根声明Revised BSD，并含EPANET等第三方说明；不是简单把政府来源视为无条件公有领域。

证据：[1](https://github.com/USEPA/WNTR/blob/11eec7d5bf0a9367ffe04d75707918f0c0a890a1/wntr/sim/core.py#L1190)；[2](https://github.com/USEPA/WNTR/blob/11eec7d5bf0a9367ffe04d75707918f0c0a890a1/wntr/tests/test_sim_PDD.py#L21)；[3](https://github.com/USEPA/WNTR/blob/11eec7d5bf0a9367ffe04d75707918f0c0a890a1/examples/pipe_criticality.py#L14)
证据1：run_sim注明仅水力扩展期仿真，不收敛时可返回partial results/error_code，验收须检查完整性。
证据2：PDA测试以解析平方根关系核对低压下的真实需求满足量。
证据3：关键性示例关闭单管前reset_initial_values，并扣除正常工况已低压节点，适合作为正常基线。
实际选读：wntr/sim/core.py:1190-1243；wntr/tests/test_sim_PDD.py:21-43；examples/pipe_criticality.py:14-68
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
