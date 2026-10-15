# O08_BQSKIT 耦合图约束下的量子线路布局与交换门优化

- 类别：optimization；潜力：high；优先级：hold_baseline。素材研究，未构题/运行/验证难度。
- 主来源：BQSKit/bqskit@9324d64a65f147ecffec005a122eb5a491a3fefc。
- 固定版本清单：[manifest](../sources/o08_bqskit/manifest.json)。
- 本项素材单元：GeneralizedSabreAlgorithm/layout/routing与unitary等价回归、tfim小QASM

## 拟交付与难度

给定小规模原线路和硬件耦合图，输出保持语义与初末映射的可执行线路，降低两比特门/SWAP或深度；先冻结门集与单一主目标。
- 交付：QASM线路、初末映射、编译/搜索策略和等价检查记录。
- 难度来源：逻辑到物理映射改变后续门距离，局部少SWAP不保证全局线路低深度。
- 难度来源：门依赖frontier、前后向布局与搜索预算相互约束，必须保持包含置换的线路等价。

## 验证与划分

- 正常基线：原生SABRE布局/路由与Qiskit等成熟合法transpiler，先扫正常passes/heuristic。
- 首个探针：先在小线路全矩阵等价检查下建立强SABRE基线，再比较不同拓扑/线路族的可测剩余门数。
- 停止条件：默认编译已饱和，或错误忽略映射/换门集带来伪改进，则不成题。
- 独立评测：独立模拟或对固定可证门集作严格等价检查，包含initial/final permutation，再验证每个两比特门在耦合图上；规模待测，大电路抽样不冒充严格等价。
- 生成与划分：原创线路族和硬件拓扑联合生成，按电路结构划分，不仅调随机旋转角；tfim只作格式/参考。
- 谱系/重叠：编译器基础设施可共享，但评分是组合映射的解质量；与硬件/优化族谱系交叉显式记录。
- 离线/计算：Python/原生BQSKit依赖；不需真实QPU，但全unitary指数成本需限制和验证。
- 许可观察：根BSD式许可并含LBNL/UC条款，依赖各核；量子服务不作为必要条件。

## 选读证据

- [bqskit/passes/mapping/sabre.py:100](https://github.com/BQSKit/bqskit/blob/9324d64a65f147ecffec005a122eb5a491a3fefc/bqskit/passes/mapping/sabre.py#L100)：SABRE按逻辑到物理映射、耦合图和门frontier推进。
- [tests/passes/mapping/test_sabre.py:1](https://github.com/BQSKit/bqskit/blob/9324d64a65f147ecffec005a122eb5a491a3fefc/tests/passes/mapping/test_sabre.py#L1)：原生测试同时检查包含PI/PF的unitary距离及耦合边合法性。
