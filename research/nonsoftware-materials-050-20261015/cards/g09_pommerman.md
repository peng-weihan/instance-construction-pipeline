# G09_POMMERMAN · Pommerman

状态：潜力 medium / hold_reference；素材研究，未构题/运行/难度验收。
来源：[MultiAgentLearning/playground](https://github.com/MultiAgentLearning/playground/tree/5315f6da378f495737dfe34a4ba7f50c84423ce7)
固定版本：`5315f6da378f495737dfe34a4ba7f50c84423ce7`
来源单元：炸弹棋盘环境、前向模型和官方FFA运行示例
材料：[manifest](../sources/g09_pommerman/manifest.json)，含文件树、原文URL和SHA256。

拟题：**延迟爆炸下的生存与战术规划**
交付能在局部观察、定时炸弹和不同对手下躲避、开路和攻击的策略；限定无图像的棋盘观察与已说明规则。
交付：agent入口、危险时间图/记忆状态、交互回放和战术诊断。

自然难点一：放弹后效果延迟，连锁反应使当前位置安全不等于下几步可逃。
自然难点二：拆障碍、取强化和攻击对手竞争移动时机，短视避险也可能锁死自己。
正常基线：官方SimpleAgent/RandomAgent，危险区时间展开BFS与现成MCTS正常适配。
首个探针：先验证无render运行、所有随机源可设种子、reset清理；再测安全BFS是否已覆盖任务。
降级/淘汰：若必须依赖过时Gym或未封装全局随机态且无法可靠重置则hold；不能把渲染和旧依赖修复算agent难度。

独立评分：私有forward model推进，评分胜率、合法动作和生存；跨座位配对，平局/互毁单列，防只苟活刷分。
生成与划分：留出障碍拓扑、初始道具和对手行为族；维持各出生点可行逃生，不仅随机新棋盘。
谱系/污染：独立定时爆炸底层；与旧RPG/RTS不同，公开Pommerman agent高度可复用，需基线核验。
离线与计算：Python旧Gym生态；示例调用render但拟题可关闭，未运行证明全部依赖支持headless和可复现。
许可观察：根Apache-2.0；游戏美术和可选Docker agent不纳入，若发行资源再查。

证据：[1](https://github.com/MultiAgentLearning/playground/blob/5315f6da378f495737dfe34a4ba7f50c84423ce7/pommerman/envs/v0.py#L148)；[2](https://github.com/MultiAgentLearning/playground/blob/5315f6da378f495737dfe34a4ba7f50c84423ce7/examples/simple_ffa_run.py#L14)
证据1：reset重建棋盘/炸弹/火焰并重置agent，seed接口存在但需追踪所有随机源。
证据2：官方示例支持SimpleAgent和RandomAgent混合，以act/step推进和输出终局。
实际选读：pommerman/envs/v0.py:148-202；examples/simple_ffa_run.py:14-34
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
