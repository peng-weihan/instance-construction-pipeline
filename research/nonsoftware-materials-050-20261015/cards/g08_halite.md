# G08_HALITE · Halite III

状态：潜力 high / hold_reference；素材研究，未构题/运行/难度验收。
来源：[HaliteChallenge/Halite-III](https://github.com/HaliteChallenge/Halite-III/tree/e1050ee924292997b3a446b4be4c821848944fd8)
固定版本：`e1050ee924292997b3a446b4be4c821848944fd8`
来源单元：官方headless比赛引擎、地图模型、积分/崩溃排名集成测试
材料：[manifest](../sources/g08_halite/manifest.json)，含文件树、原文URL和SHA256。

拟题：**舰队采集与回港投资对抗**
交付舰队策略，联合优化采集、返航、产船和建立投递点，在有限回合和对手碰撞风险下最大化入库资源。
交付：标准IO bot、资源/投资回放、对手池对局与决策分析。

自然难点一：船在外携带资源不等于终局入库收益，需要返航时点和交通协调。
自然难点二：造船/投递点消耗当前财富但扩大后期收益，同时对手碰撞和枯竭改变回报。
正常基线：贪心采集+最短返航、投资回收期规则、公开强bot正常适配。
首个探针：先编译固定引擎并跑官方崩溃/排名测试，再比较无碰撞贪心与公开方案；不以旧竞赛冠军水平直接作新题门槛。
降级/淘汰：若强公开bot薄适配已满足全部新分布则降低优先级；若headless构建无法稳定重置则先修环境。

独立评分：引擎隔离运行bot并给真实资源、排名、崩溃和超时；配对地图种子与交换玩家号，回放独立复核。
生成与划分：留出资源场空间结构、地图尺寸和对手混合族；不从现有公开比赛回放抽取隐藏答案。
谱系/污染：不同底层于旧OpenTTD/RTS；经济对抗相似但动作/终局目标独立。旧赛季/同引擎不再计来源。
离线与计算：C++17引擎和脚本bot，无需网站/排行榜/在线账户；这里只取引擎片段，构建和依赖健康尚未证实。
许可观察：根MIT；官网vendor资产不纳入离线环境，公开bot另查许可。

证据：[1](https://github.com/HaliteChallenge/Halite-III/blob/e1050ee924292997b3a446b4be4c821848944fd8/game_engine/core/HaliteImpl.cpp#L450)；[2](https://github.com/HaliteChallenge/Halite-III/blob/e1050ee924292997b3a446b4be4c821848944fd8/game_engine/test/integration_test.py#L15)
证据1：终止检查考虑剩余地图资源和玩家船/造船能力。
证据2：官方集成测试用--results-as-json运行独立bot进程，读取回放和排名并检查崩溃场景。
实际选读：game_engine/core/HaliteImpl.cpp:450-477；game_engine/test/integration_test.py:15-60
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
