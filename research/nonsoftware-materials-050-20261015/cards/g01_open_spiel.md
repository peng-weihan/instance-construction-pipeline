# G01_OPEN_SPIEL · OpenSpiel / Goofspiel

状态：潜力 medium / hold_baseline；素材研究，未构题/运行/难度验收。
来源：[google-deepmind/open_spiel](https://github.com/google-deepmind/open_spiel/tree/48401890ee9857e611678302371378175a8e4c6b)
固定版本：`48401890ee9857e611678302371378175a8e4c6b`
来源单元：Goofspiel同步竞价规则与测试；整个OpenSpiel集合只计一个来源
材料：[manifest](../sources/g01_open_spiel/manifest.json)，含文件树、原文URL和SHA256。

拟题：**不完全信息同步竞价策略**
给定合法观察接口，交付能在未见牌序和对手混合池中持续分配手牌、估计对手并控制风险的竞价策略；固定有限牌组范围。
交付：策略入口、配置、离线对局记录和策略/消融说明；不要求实现游戏引擎。

自然难点一：每次竞价永久消耗手牌，使当前得分与未来高价值轮次竞争。
自然难点二：同步出价且可隐藏对方历史，必须维护信念并应对平局与对手变化。
正常基线：随机合法、按点牌同值竞价、手牌贪心，加原生CFR/搜索算法的正常适配。
首个探针：先用现成CFR和简单混合策略在小牌组闭合；比较隐藏对手族上的增益及过拟合。
降级/淘汰：若标准CFR适配或固定同值规则在全部合同分布已达到目标，则降为短任务；不能靠禁用算法制造难度。

独立评分：判题器私有化运行原规则，检验动作合法和终局收益；交换座位、配对种子，对混合对手汇总均值及尾部收益。
生成与划分：牌序、牌数与对手策略族分层，留出对手混合方式而非仅新seed；隐藏judge不向策略暴露全state或牌堆。
谱系/污染：不同于已有RPG/RTS引擎；OpenSpiel多游戏不重复计数。公开竞价算法/解需检索，公平纳入基线。
离线与计算：C++/Python绑定需预构建，表格观察无图像资产；小牌组CPU可先测，较大状态的训练预算未验证。
许可观察：根LICENSE为Apache-2.0；第三方依赖另查。

证据：[1](https://github.com/google-deepmind/open_spiel/blob/48401890ee9857e611678302371378175a8e4c6b/open_spiel/games/goofspiel/goofspiel.cc#L418)；[2](https://github.com/google-deepmind/open_spiel/blob/48401890ee9857e611678302371378175a8e4c6b/open_spiel/games/goofspiel/goofspiel_test.cc#L30)
证据1：同步出价检查合法手牌，唯一最高者得点，平局弃点，随后消耗牌。
证据2：原生测试覆盖多人、收益口径、不完全信息和有限轮数。
实际选读：open_spiel/games/goofspiel/goofspiel.cc:418-465；open_spiel/games/goofspiel/goofspiel_test.cc:30-59
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
