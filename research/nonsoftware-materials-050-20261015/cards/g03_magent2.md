# G03_MAGENT2 · MAgent2 / Battle

状态：潜力 medium / hold_baseline；素材研究，未构题/运行/难度验收。
来源：[Farama-Foundation/MAgent2](https://github.com/Farama-Foundation/MAgent2/tree/f3fca5a78504615986dfba37d85137c9e15d1db6)
固定版本：`f3fca5a78504615986dfba37d85137c9e15d1db6`
来源单元：Battle原生环境、C++GridWorld绑定、并行观察定义及渲染测试
材料：[manifest](../sources/g03_magent2/manifest.json)，含文件树、原文URL和SHA256。

拟题：**局部视野下的小队协同对抗**
交付局部观察小队策略，在障碍、出生分布和对手战术变化下实现集火、撤退、包围与生存；限定可计算的小队规模。
交付：共享或多角色策略入口、局内通信/记忆方案、对局回放和战术分析。

自然难点一：局部观察下，集火和撤退需要跨单位协调，单体贪心会相互阻塞。
自然难点二：步进/攻击/死亡的不同奖励可能诱发刷分，必须以完整对局胜负校验。
正常基线：随机、最近敌人追击、编队集火及现成多智能体训练代码的合法适配。
首个探针：先固定小队做不渲染step/reset/seed重放探针；比较集火启发式能否已饱和。
降级/淘汰：若仅增加单位数量或依赖长训练才能拉开差距则暂缓；简单集中式策略全面达标则重设范围。

独立评分：私有进程运行环境，限制所见观察；胜负/存活与资源预算分项，并用多对手池和对称出生配对。
生成与划分：留出地图瓶颈拓扑、兵力比例和对手角色组合；团队大小变化不能成为唯一新分布。
谱系/污染：独立MAgent底层，不是microRTS包装；仍属网格战斗，需与旧RTS谱系及共享PettingZoo接口区分。
离线与计算：需要本地C++扩展，战斗可用数组观察；所读渲染测试仅证明headless测试设计，不能替代引擎无显示运行证据。
许可观察：根MIT；C++后端与依赖随完整发行再审。

证据：[1](https://github.com/Farama-Foundation/MAgent2/blob/f3fca5a78504615986dfba37d85137c9e15d1db6/magent2/environments/battle/battle.py#L129)；[2](https://github.com/Farama-Foundation/MAgent2/blob/f3fca5a78504615986dfba37d85137c9e15d1db6/magent2/environments/magent_env.py#L38)；[3](https://github.com/Farama-Foundation/MAgent2/blob/f3fca5a78504615986dfba37d85137c9e15d1db6/tests/test_render.py#L25)；[4](https://github.com/Farama-Foundation/MAgent2/blob/f3fca5a78504615986dfba37d85137c9e15d1db6/magent2/environments/battle/battle.py#L181)
证据1：Battle设定max_cycles、seed以及步进/攻击/死亡和击杀奖励。
证据2：并行环境分别提供各agent观察和全局state，必须阻止评分时全局state泄露。
证据3：渲染测试用dummy SDL并检查只初始化display/font；不是对游戏难度的测试。
证据4：底层GridWorld配置写入seed并定义局部CircleRange视野与攻击距离。
实际选读：magent2/environments/battle/battle.py:129-155；magent2/environments/magent_env.py:38-85；tests/test_render.py:25-47；magent2/environments/battle/battle.py:181-205
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
