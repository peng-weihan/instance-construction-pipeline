# O01_ORTOOLS 维护窗口与换型间隔下的作业车间调度

- 类别：optimization；潜力：high；优先级：hold_baseline。素材研究，未构题/运行/验证难度。
- 主来源：google/or-tools@100f66e6242ab8bf8d32feb8f3bf086db66ae2b5。
- 固定版本清单：[manifest](../sources/o01_ortools/manifest.json)。
- 本项素材单元：examples/python/jobshop_with_maintenance_sat.py 与 jobshop_ft06_distance_sat.py；不是整个OR-Tools作为一道题

## 拟交付与难度

给定工序、机器、维护窗口和明确换型规则，提交可行排程及可重放求解器，在固定计算预算下缩短makespan。先只组合已公开的非抢占语义，不默认完整柔性工厂。
- 交付：工序开始/结束和机器分配表、求解程序、目标与约束核对记录。
- 难度来源：维护占用与工序先后共同限制机器顺序，局部交换可能使另一条作业链不可行。
- 难度来源：可行排程之后仍有瓶颈移动、邻域选择和求解时间分配的质量取舍，必须实测强CP-SAT基线后的余量。

## 验证与划分

- 正常基线：默认CP-SAT interval/NoOverlap模型、正常预处理与参数调优；允许现成调度器。
- 首个探针：把现成维护模型和距离模型改成统一输入，测结构不同的中小实例；先看合法建模与默认求解是否已饱和。
- 停止条件：薄建模已在预算内普遍最优，或困难主要来自未公开换型定义，则重设该实例族。
- 独立评测：独立逐工序检查precedence、机器不重叠和维护窗口，再重算makespan；小规模穷举交叉验证，连续分数端点待测。
- 生成与划分：另建可行证书驱动的工艺路线/维护生成器，按工艺拓扑和瓶颈类型分族；公开FT06仅用于格式和基线，不作hidden。
- 谱系/重叠：新主仓库；排程是广泛共享机制，不能将FT06改名或只换seed算新任务。与原组合优化任务的隐藏实例仍需核对。
- 离线/计算：CPU Python/原生OR-Tools轮子、固定solver版本；保存的只有例子与许可，完整依赖和实例族未构建。
- 许可观察：根Apache-2.0；源例子许可头需保留，外部调度数据分别核权。

## 选读证据

- [examples/python/jobshop_with_maintenance_sat.py:65](https://github.com/google/or-tools/blob/100f66e6242ab8bf8d32feb8f3bf086db66ae2b5/examples/python/jobshop_with_maintenance_sat.py#L65)：原生示例用维护interval、NoOverlap和工序precedence最小化makespan。
- [examples/python/jobshop_ft06_distance_sat.py:15](https://github.com/google/or-tools/blob/100f66e6242ab8bf8d32feb8f3bf086db66ae2b5/examples/python/jobshop_ft06_distance_sat.py#L15)：FT06变体明确机器间最小距离约束及makespan目标。
