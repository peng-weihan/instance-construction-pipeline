# O05_MAPF 延迟与持续任务下的多机器人分配和路径协调

- 类别：optimization；潜力：high；优先级：hold_reference。素材研究，未构题/运行/验证难度。
- 主来源：MAPF-Competition/Start-Kit@9bc75d9dd9883de049294ab2981bf325bbe19d49。
- 固定版本清单：[manifest](../sources/o05_mapf/manifest.json)。
- 本项素材单元：官方Start-Kit执行状态与输入输出合同、maze示例元数据

## 拟交付与难度

选定并冻结一个combined轨道，提交任务分配/无碰撞行动策略，在持续到达任务和公开延迟模型下提高完成量。
- 交付：离线策略程序、可重放行动/分配记录和完成任务统计。
- 难度来源：分配改变机器人去向和拥堵，局部最短路可能降低整个车队完成量。
- 难度来源：执行延迟使计划与实际状态分离，重规划、避碰和计算预算共同影响长期吞吐。

## 验证与划分

- 正常基线：官方starter与成熟优先级规划、CBS/RHCR/LNS等适用算法，正常调参；不禁标准路径算法。
- 首个探针：先跑健康kit与独立trace复算，确认2026动作时长/延迟规则，再比较官方与成熟规划方案。
- 停止条件：环境版本不稳定或只需改调度参数即可全解；没有明确轨道则不成题。
- 独立评测：由冻结可信环境重放动作、碰撞/任务状态并统计numTaskFinished与错误；候选自报统计不可信，另写小规模独立网格检查。
- 生成与划分：新建仓库/障碍拓扑、任务到达/延迟生成模型，按布局族和任务过程拆分，不把现成地图换seed当新题。
- 谱系/重叠：与原warehouse_forklift_routing及本批Flatland都是多主体路径谱系；新引擎不能替代地图/任务生成与评测独立性。
- 离线/计算：CPU C++/Boost/Python bindings，headless可设计；示例JSON引用的地图/任务资产未完整获取，未跑环境。
- 许可观察：根MIT；地图和竞赛外部资产须逐项核权，仓库license不自动覆盖引用图。

## 选读证据

- [src/ActionModel.cpp:490](https://github.com/MAPF-Competition/Start-Kit/blob/9bc75d9dd9883de049294ab2981bf325bbe19d49/src/ActionModel.cpp#L490)：行动状态包含未完成动作及方向，计划动作与实际动作存在时长状态。
- [Input_Output_Format.md:100](https://github.com/MAPF-Competition/Start-Kit/blob/9bc75d9dd9883de049294ab2981bf325bbe19d49/Input_Output_Format.md#L100)：输出合同分别记录actual/planner paths、任务事件、动作/调度错误与超时。
