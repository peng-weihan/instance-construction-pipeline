# O02_PYVRP 多维容量与可选客户的奖励收集路径优化

- 类别：optimization；潜力：high；优先级：hold_baseline。素材研究，未构题/运行/验证难度。
- 主来源：PyVRP/PyVRP@abe53138ca43bce75ed95c99e37c7452f14e53d2。
- 固定版本清单：[manifest](../sources/o02_pyvrp/manifest.json)。
- 本项素材单元：CostEvaluator、Model及prize-collecting原生回归

## 拟交付与难度

在固定距离/时间矩阵和公开车队约束下选择服务客户及路线，平衡里程与未收集奖励；限定已确认的容量、时间及可选客户子集。
- 交付：逐车路线/服务集合、求解策略和约束可行性记录。
- 难度来源：可选客户的奖励决定是否访问，局部删点既改变距离也改变收益，不能只做最短路线。
- 难度来源：容量、时间和车队类型在跨路线移动时共同变化，惩罚搜索中的好解不等于最终可行解。

## 验证与划分

- 正常基线：现有PyVRP ILS/正常模型参数，OR-Tools或合法MILP；默认成熟求解器也必须参与比较。
- 首个探针：使用未修改PyVRP跑新结构的奖励/容量族，并与简单插入/删除策略比较；检查剩余质量空间。
- 停止条件：默认求解器已满足整体目标，或仅需调一个罚系数便全解，则不包装成长程题。
- 独立评测：独立重算每条路线、访问唯一性、负载/时间和未收集奖励；可行性单独门控，不用penalisedCost替代最终cost。
- 生成与划分：生成新的客户实体、服务奖励和车队结构，按地理/奖励相关性分族；不复用Solomon/Homberger原点集。
- 谱系/重叠：与旧VRPTW属同一车辆路径谱系；独立仓库不证明任务独立，新增奖励选择合同与分布须有实质变化。
- 离线/计算：Python/C++扩展；数据矩阵和全部依赖离线预置。所取测试可能依赖未下载fixture，未执行。
- 许可观察：根MIT，标注HGS-CVRP/HGS-DIMACS谱系版权；数据许可另核。

## 选读证据

- [pyvrp/cpp/CostEvaluator.h:200](https://github.com/PyVRP/PyVRP/blob/abe53138ca43bce75ed95c99e37c7452f14e53d2/pyvrp/cpp/CostEvaluator.h#L200)：最终cost对不可行解返回极大值，deltaCost另计算容量/时间等罚项。
- [tests/test_CostEvaluator.py:135](https://github.com/PyVRP/PyVRP/blob/abe53138ca43bce75ed95c99e37c7452f14e53d2/tests/test_CostEvaluator.py#L135)：原生prize测试将路线距离和未收集奖励相加；可行性测试独立存在。
