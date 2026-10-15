# K04_STOCKPYL 供货中断下的多级库存政策与经营方案

- 类别：knowledge；潜力：high；优先级：scope_probe。素材研究，未构题/运行/验证难度。
- 主来源：LarrySnyder/stockpyl@0bae176c9671ad73bbe1f2fbe34f503fdf48349d。
- 固定版本清单：[manifest](../sources/k04_stockpyl/manifest.json)。
- 本项素材单元：多级仿真step/一致性检查、(s,S)成本测试和实例定义

## 拟交付与难度

给定原创供应链、需求/供货历史与经营约束，交付补货政策、服务/成本/现金占用评估及压力情境经营建议；不要求实现仿真器。
- 交付：政策参数/可调用决策、逐期台账、服务与成本指标及决策报告。
- 难度来源：节点订单、运输在途和中断影响未来服务，单节点局部成本最优可能使上游/下游失衡。
- 难度来源：成本、缺货服务和库存占用存在领域取舍，需要对新情境给出一致的业务解释与可复算账本。

## 验证与划分

- 正常基线：原生base-stock/(s,S)/精确单级算法、简单参数搜索与常规模拟优化，允许库存工具。
- 首个探针：健康仿真+base-stock及参数搜索先覆盖一个多级中断案例，确认剩余跨场景政策价值。
- 停止条件：一组原生policy参数已足额完成全部合同，或所谓高难只靠更长随机仿真，则重设。
- 独立评测：可信仿真按相同随机外生轨迹评估成本/服务，并独立检查库存流守恒和台账；业务建议与公开指标约束一致，非纯语言打分。
- 生成与划分：原创网络/BOM/lead-time/中断和需求过程联合生成，按结构/供货机制拆分；不能只复用教材实例换seed。
- 谱系/重叠：与组合优化/游戏策略有机制交叉，本候选主交付是领域方案与证据；若只计最低成本应改归优化。
- 离线/计算：CPU Python/SciPy依赖；实例JSON已存但关联完整仿真依赖未构建，未跑多种子评估。
- 许可观察：根MIT；教材衍生实例数字和描述再分发/训练条款另核，原创案例优先。

## 选读证据

- [src/stockpyl/sim.py:199](https://github.com/LarrySnyder/stockpyl/blob/0bae176c9671ad73bbe1f2fbe34f503fdf48349d/src/stockpyl/sim.py#L199)：step依次处理中断、需求、订单、发运和成本，支持外部order override。
- [tests/test_ss.py:1](https://github.com/LarrySnyder/stockpyl/blob/0bae176c9671ad73bbe1f2fbe34f503fdf48349d/tests/test_ss.py#L1)：(s,S)原生回归对具体教材实例成本做数值断言。
