# G02_MINIGRID · MiniGrid / BabyAI

状态：潜力 medium / hold_baseline；素材研究，未构题/运行/难度验收。
来源：[Farama-Foundation/Minigrid](https://github.com/Farama-Foundation/Minigrid/tree/b34a5755dbef71e3f1662552259a94b255c1a8bb)
固定版本：`b34a5755dbef71e3f1662552259a94b255c1a8bb`
来源单元：BabyAI组合指令生成、任务验证器与环境复现测试
材料：[manifest](../sources/g02_minigrid/manifest.json)，含文件树、原文URL和SHA256。

拟题：**带记忆的组合指令执行**
从局部观察和自然语言指令执行寻物、开锁、搬运及先后顺序任务；交付可跨未见房间结构与指令组合泛化的agent。
交付：决策策略、可持久化的局内记忆、开发集轨迹和错误分类。

自然难点一：局部视野要求探索并记住物体、门和钥匙位置。
自然难点二：指令组合与搬运/开锁前提相互作用，单步导航成功不代表整条任务完成。
正常基线：官方可用专家/符号导航方案、BFS地图记忆及简单指令解析；先查能否完整覆盖。
首个探针：用符号地图+BFS+原生验证器跑组合留出，比较解析和探索失误；主动测试reset跨局状态。
降级/淘汰：若固定语法的解析+BFS已覆盖全部自然任务则下调，不把扩大格子数视为长程难度证据。

独立评分：独立任务验证器评完成率、合法动作、步数与超时；不让agent读内部网格/任务谓词。
生成与划分：留出房间连通模式、指令组合、干扰物和锁钥匙依赖；seed与生成结构双重分离。
谱系/污染：非旧RTS/RPG；与大量BabyAI公开基准有污染风险，必须重新定义组合分布和验收，而非换seed。
离线与计算：Python离线生成、符号/低分辨率观察；无需下载图像语料；训练和泛化强度未测。
许可观察：根Apache-2.0；环境和发行依赖另核对。

证据：[1](https://github.com/Farama-Foundation/Minigrid/blob/b34a5755dbef71e3f1662552259a94b255c1a8bb/minigrid/envs/babyai/core/levelgen.py#L59)；[2](https://github.com/Farama-Foundation/Minigrid/blob/b34a5755dbef71e3f1662552259a94b255c1a8bb/tests/test_envs.py#L54)
证据1：任务生成控制锁门、干扰物、可达性和随机指令；gen_mission显式清除跨局locked_room。
证据2：同seed双环境相同动作的测试逐步比较观察、奖励和终止标记。
实际选读：minigrid/envs/babyai/core/levelgen.py:59-90；tests/test_envs.py:54-94
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
