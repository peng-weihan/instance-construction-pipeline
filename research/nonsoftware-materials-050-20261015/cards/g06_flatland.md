# G06_FLATLAND · Flatland

状态：潜力 high / scope_probe；素材研究，未构题/运行/难度验收。
来源：[flatland-association/flatland-rl](https://github.com/flatland-association/flatland-rl/tree/e355074d0f7afe0df8de92caed2274330369dbcf)
固定版本：`e355074d0f7afe0df8de92caed2274330369dbcf`
来源单元：铁路轨道环境、终局更新、ShortestPathPolicy原生测试
材料：[manifest](../sources/g06_flatland/manifest.json)，含文件树、原文URL和SHA256。

拟题：**扰动下的多列车在线调度**
交付在线调度策略，在列车陆续发车、共享单线与会车限制及故障下提高到达率和准点性；任务对象是策略而非实现仿真器。
交付：调度策略入口、事件/延误诊断、可重放轨迹及方案分析。

自然难点一：单列车最短路可能造成多车死锁，局部最优需让路和等待。
自然难点二：故障与中途目标改变后续占线，调度必须跨时段修订而不能只算一次静态路线。
正常基线：原生ShortestPathPolicy、优先级预约表、集中式路径规划或MAPF求解器正常适配。
首个探针：复核原生固定seed测试中到达率1/7和2/7的现象，但不当作新题成绩；试预约表基线是否解决剩余死锁。
降级/淘汰：若全部地图可由简单优先级预约闭合则重设自然事件分布；若仅靠增加列车数量拖慢则不计高难。

独立评分：私有simulator重放动作，输出到达率、总延误、死锁和非法动作；设可比时限，预先验证实例可解。
生成与划分：留出路网瓶颈、目标组合和故障过程；地图拓扑族与seed分别划分，平衡无解实例。
谱系/污染：与组合优化MAPF有能力交叉，但这里交付在线策略，评分用交互轨迹；同Flatland不同赛季不重复计素材。
离线与计算：数组观察及CPU模拟，无大图像；当前环境版本与轨迹工具健康、故障可复现性未运行。
许可观察：根MIT；引入外部铁路数据需另查，拟题优先程序生成。

证据：[1](https://github.com/flatland-association/flatland-rl/blob/e355074d0f7afe0df8de92caed2274330369dbcf/flatland/envs/rail_env.py#L451)；[2](https://github.com/flatland-association/flatland-rl/blob/e355074d0f7afe0df8de92caed2274330369dbcf/tests/test_flatland_envs_rail_env_policies.py#L13)
证据1：环境在全员结束或步数上限时累计终局奖励，并记录真实arrival_time。
证据2：原生测试给ShortestPathPolicy在固定种子两种场景断言1/7、2/7到达率；仅是源码测试预期。
实际选读：flatland/envs/rail_env.py:451-490；tests/test_flatland_envs_rail_env_policies.py:13-35
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
