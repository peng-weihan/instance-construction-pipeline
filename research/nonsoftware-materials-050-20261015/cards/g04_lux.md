# G04_LUX · Lux AI Season 2

状态：潜力 high / hold_reference；素材研究，未构题/运行/难度验收。
来源：[Lux-AI-Challenge/Lux-Design-S2](https://github.com/Lux-AI-Challenge/Lux-Design-S2/tree/5bcb3c775d536cecda32a3c041a9814279b79c5b)
固定版本：`5bcb3c775d536cecda32a3c041a9814279b79c5b`
来源单元：官方S2环境、配置、Python agent与移动冲突示例
材料：[manifest](../sources/g04_lux/manifest.json)，含文件树、原文URL和SHA256。

拟题：**资源供应链与对抗工厂经营**
交付从工厂选址到采冰、供水、供电、运输和地衣竞争的完整策略，针对未见地图与对手持续改进。
交付：可运行agent、预算内规划器、开发回放、资源损失和策略消融报告。

自然难点一：工厂选址和早期投资会约束后续水/能量供应链，短期采集最优可能长期破产。
自然难点二：多机器人移动冲突、动作队列与对手争夺同时影响行动可执行性和终局收益。
正常基线：官方Python示例、启发式采集+运输+工厂生存，允许公开路径规划和竞争方案正常适配。
首个探针：先修订并验证固定版本API健康脚本：所读collision例子使用4元组step而当前env注解为5元组；再做工厂生存基线。
降级/淘汰：若参考环境/样例协议不能一致闭合则先hold；若公开策略薄适配达标则重设地图/对手合同。

独立评分：不信agent自报资源；隔离运行官方step并保存动作和重放，以终局地衣/胜负及非法动作率分层反馈。
生成与划分：除seed外留出地形/资源空间结构、工厂数和对手策略组合；禁止把隐藏对手代码映射给agent。
谱系/污染：与microRTS同为资源对抗但不同引擎、动作和经济链；公开Kaggle方案污染需查。
离线与计算：Python/numpy数组环境，无需大视觉资源；API兼容、CPU每步预算与离线依赖未实测。
许可观察：根Apache-2.0；公开参赛策略不能默认同许可。

证据：[1](https://github.com/Lux-AI-Challenge/Lux-Design-S2/blob/5bcb3c775d536cecda32a3c041a9814279b79c5b/luxai_s2/luxai_s2/env.py#L760)；[2](https://github.com/Lux-AI-Challenge/Lux-Design-S2/blob/5bcb3c775d536cecda32a3c041a9814279b79c5b/luxai_s2/tests/collision.py#L12)；[3](https://github.com/Lux-AI-Challenge/Lux-Design-S2/blob/5bcb3c775d536cecda32a3c041a9814279b79c5b/luxai_s2/luxai_s2/env.py#L995)
证据1：step区分早期工厂阶段并检查动作空间，类型注解含5个返回量。
证据2：固定seed移动冲突示例构造不同power的重型机器人并检查淘汰结果，调用协议需健康复核。
证据3：实际step返回observations、rewards、terminations、truncations、infos五项；原例四项调用需修订核验。
实际选读：luxai_s2/luxai_s2/env.py:760-808；luxai_s2/tests/collision.py:12-48；luxai_s2/luxai_s2/env.py:995-1015
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
