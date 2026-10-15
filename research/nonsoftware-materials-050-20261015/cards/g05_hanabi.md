# G05_HANABI · Hanabi Learning Environment

状态：潜力 high / hold_baseline；素材研究，未构题/运行/难度验收。
来源：[google-deepmind/hanabi-learning-environment](https://github.com/google-deepmind/hanabi-learning-environment/tree/54e79594f4b6fb40ebb3004289c6db0e34a8b5fb)
固定版本：`54e79594f4b6fb40ebb3004289c6db0e34a8b5fb`
来源单元：Hanabi规则状态、Python观察/奖励接口与示例
材料：[manifest](../sources/g05_hanabi/manifest.json)，含文件树、原文URL和SHA256。

拟题：**有限提示预算下的协作纸牌策略**
交付只看合法玩家观察的合作策略，在换座位、未知伙伴策略及未见牌序下建立可靠的提示与出牌行为。
交付：agent入口、跨回合信念状态、伙伴适应实验与回放。

自然难点一：看见别人的牌却看不见自己的牌，提示消耗公共资源且必须兼容伙伴解释。
自然难点二：错误出牌耗生命，弃牌不可逆，安全保守与取得高分存在冲突。
正常基线：官方SimpleAgent、可用规则约定与信念采样/搜索算法；正常纳入已有强Hanabi策略。
首个探针：先比较SimpleAgent和公开约定策略的跨伙伴表现，确认观察中不会泄露自己的牌；检查独立种子重放。
降级/淘汰：若目标仅自对弈且公开约定直接达标则降级；不能把不说明伙伴协议的任意失败当难度。

独立评分：私有环境累计真实score差，记录终止和合法动作；区分自合作、同族伙伴与跨族伙伴得分。
生成与划分：留出伙伴族和约定混合，不仅换牌序；只在规则允许范围内变人数/牌组，明确训练可见信息。
谱系/污染：独立协作隐藏信息纸牌，无旧RPG/RTS引擎复用；公开Hanabi策略和解码约定污染风险较高。
离线与计算：C++绑定与Python接口需要预构建；无图片资产；搜索/训练预算和复现尚未测。
许可观察：根Apache-2.0；任何外部伙伴实现另查许可。

证据：[1](https://github.com/google-deepmind/hanabi-learning-environment/blob/54e79594f4b6fb40ebb3004289c6db0e34a8b5fb/hanabi_learning_environment/hanabi_lib/hanabi_state.cc#L250)；[2](https://github.com/google-deepmind/hanabi-learning-environment/blob/54e79594f4b6fb40ebb3004289c6db0e34a8b5fb/hanabi_learning_environment/rl_env.py#L343)；[3](https://github.com/google-deepmind/hanabi-learning-environment/blob/54e79594f4b6fb40ebb3004289c6db0e34a8b5fb/examples/rl_env_example.py#L34)；[4](https://github.com/google-deepmind/hanabi-learning-environment/blob/54e79594f4b6fb40ebb3004289c6db0e34a8b5fb/hanabi_learning_environment/hanabi_lib/hanabi_game.cc#L42)
证据1：提示扣information tokens并更新他人手牌知识，机会事件按剩余牌概率抽取。
证据2：奖励是state.score的前后差且终局可能负，不可错误累计仅正分。
证据3：示例按player_observations逐人决策，只有current_player动作传给step。
证据4：游戏seed=-1时采random_device，显式seed后初始化rng；评测必须冻结该参数。
实际选读：hanabi_learning_environment/hanabi_lib/hanabi_state.cc:250-286；hanabi_learning_environment/rl_env.py:343-366；examples/rl_env_example.py:34-64；hanabi_learning_environment/hanabi_lib/hanabi_game.cc:42-66
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
