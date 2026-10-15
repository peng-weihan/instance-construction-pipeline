# G07_TEXTWORLD · TextWorld / Cooking

状态：潜力 medium / hold_baseline；素材研究，未构题/运行/难度验收。
来源：[microsoft/TextWorld](https://github.com/microsoft/TextWorld/tree/6d88a0845bc904751d3b7f128d61f21cabdf6f70)
固定版本：`6d88a0845bc904751d3b7f128d61f21cabdf6f70`
来源单元：Cooking生成器、知识逻辑、原生生成/完成测试；不计手写IF目录
材料：[manifest](../sources/g07_textworld/manifest.json)，含文件树、原文URL和SHA256。

拟题：**可生成世界中的文本探索与料理计划**
在仅文本观察环境中完成探索、原料获取、切制、加热和上菜的组合目标；生成未见房间图与食材加工依赖。
交付：文本交互agent、局内世界模型与计划、命令轨迹和失败分析。

自然难点一：物品位置与容器状态需探索，有限背包和往返路线影响整体计划。
自然难点二：错误切制/烹饪可能不可逆，任务前提与顺序必须从文字规则中正确推断。
正常基线：地图记忆、命令语法解析、符号计划器，以及公开TextWorld料理agent的合法适配。
首个探针：用程序生成walkthrough先验证可解性，然后用符号agent在结构留出任务上测是否已接近满分。
降级/淘汰：若walkthrough或内部facts/recipe元数据泄露给agent则无效；公开固定料理脚本饱和则重设生成规则而非换seed。

独立评分：环境私有维护任务谓词和fail条件，以完成、进度与动作数反馈；不按文本叙事质量主观打分。
生成与划分：房间拓扑、材料/加工配方组合、干扰对象与背包约束分层留出；保留独立生成seed和grammar seed。
谱系/污染：不是IF Archive取一款现成手写游戏；与旧Anchorhead等共享文本冒险/解释器谱系，必须新生成依赖结构和验收，公开Cooking split不能当新题。
离线与计算：需冻结文本编译器/解释器及字典资源；已取生成源码和小测试，未构建解释器、未生成游戏文件。
许可观察：TextWorld根MIT；Inform/Z-machine等随附工具和文本资源另核对，不能从根许可推断全部资源。

证据：[1](https://github.com/microsoft/TextWorld/blob/6d88a0845bc904751d3b7f128d61f21cabdf6f70/textworld/challenges/tw_cooking/cooking.py#L799)；[2](https://github.com/microsoft/TextWorld/blob/6d88a0845bc904751d3b7f128d61f21cabdf6f70/textworld/challenges/tests/test_cooking.py#L15)
证据1：料理生成控制食材数、开门、加热、切制、背包及地图，并分离map/objects/grammar/quest/recipe RNG。
证据2：测试固定世界只改recipe_seed，检查原料变化和空间事实不变，再验证walkthrough可完成。
实际选读：textworld/challenges/tw_cooking/cooking.py:799-843；textworld/challenges/tests/test_cooking.py:15-56
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
