# K09_BLUESKY · BlueSky 航空运行

状态：潜力 high / hold_data；素材研究，未构题/运行/难度验收。
来源：[TUDelft-CNS-ATM/bluesky](https://github.com/TUDelft-CNS-ATM/bluesky/tree/46a2a8a5fa4e0bdd6f6991fefc70dc3512f8fc53)
固定版本：`46a2a8a5fa4e0bdd6f6991fefc70dc3512f8fc53`
来源单元：真实statebased冲突检测、航路测试与八机有/无风情景
材料：[manifest](../sources/k09_bluesky/manifest.json)，含文件树、原文URL和SHA256。

拟题：**受限空域的冲突消解与航班计划审计**
给定模拟空域、航路点、速度/高度约束、风场和交通计划，交付可执行调整计划及冲突、延误和航路代价证据。
交付：调整后的场景/指令表、逐航班轨迹、冲突清单、延误/绕飞表和方案说明。

自然难点一：水平与垂直间隔必须在同一时间窗成立，分别安全的投影不能保证整体安全。
自然难点二：局部航向/速度修改会改变下游会遇，需全局回放并核对路线及运行限制。
正常基线：现成statebased检测+MVP消解、简单错峰/高度层分配，允许成熟规划器直接适配。
首个探针：先运行有风/无风小情景并启用真正StateBased检测；detection基类返回空结果，不能当无冲突证明；独立几何核验采样间隙。
降级/淘汰：若单次MVP或静态错峰直接满足全部合同则降难；若需要未冻结导航/性能数据在线下载才能重放则hold_data。

独立评分：judge私有重放轨迹，独立检测连续时间/保守细步间隔、速度高度与航路约束；同时评价延误、绕飞和指令复杂度，报告须引用航班/时刻。
生成与划分：生成可行几何航点、交叉/汇聚交通和相关风场，按交通结构和风机制留出；不把现成SUPER8仅换机号当新题。
谱系/污染：专业航空计划而非交互奖励游戏；不声称适用于实际空管，评价范围固定为给定模拟模型。
离线与计算：数组仿真可计划headless；航空器性能/导航数据和插件需要固定版本许可与本地缓存，当前仅源代码/小情景已取。
许可观察：当前根MIT（不可依据旧版本印象写GPL）；外部BADA/导航/性能数据的许可不由根MIT覆盖。

证据：[1](https://github.com/TUDelft-CNS-ATM/bluesky/blob/46a2a8a5fa4e0bdd6f6991fefc70dc3512f8fc53/bluesky/traffic/asas/statebased.py#L28)；[2](https://github.com/TUDelft-CNS-ATM/bluesky/blob/46a2a8a5fa4e0bdd6f6991fefc70dc3512f8fc53/bluesky/test/traffic/test_route_wpt.py#L49)；[3](https://github.com/TUDelft-CNS-ATM/bluesky/blob/46a2a8a5fa4e0bdd6f6991fefc70dc3512f8fc53/bluesky/traffic/asas/detection.py#L227)
证据1：StateBased用相对速度计算CPA，并求水平/垂直冲突时间窗交集。
证据2：航路点测试规格列明坐标、类型、速度/高度和flyby限制。
证据3：Detection基类明确要求子类实现并默认返回空冲突；未启用真实检测会产生假安全。
实际选读：bluesky/traffic/asas/statebased.py:28-88；bluesky/test/traffic/test_route_wpt.py:49-82；bluesky/traffic/asas/detection.py:227-242
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
