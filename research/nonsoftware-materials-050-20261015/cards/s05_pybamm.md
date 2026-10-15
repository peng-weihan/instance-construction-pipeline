# S05_PYBAMM · PyBaMM 电池物理模型

- 主来源：[pybamm-team/PyBaMM](https://github.com/pybamm-team/PyBaMM/tree/8996ec6479b9e2a79686e17956f6dfce8eaa301b)。
- 固定版本：`8996ec6479b9e2a79686e17956f6dfce8eaa301b`。
- 来源单元：SPMe正演示例、实验仿真敏感性代码和仿真健康测试。
- 评估：`high`；优先级 `hold_reference`。

**拟题：多工况电池参数识别与留出负载预测**
从多温度/电流激励下的电压时间序列识别限定的可辨识参数组合和初始SOC，预测未见脉冲负载下电压与容量；输出参数不确定性和失配诊断。
交付：离线校准程序、参数/可辨识组合、预测曲线与区间、工况验证记录。

**困难的因果来源**
- 扩散、动力学和初始SOC会产生相似电压效应，低训练误差不代表参数可识别，需要跨工况激励与正则化。
- 电压截止事件改变轨迹长度与梯度；源代码已提示事件时间敏感时敏感性不准，优化器与评分须处理事件。

基线：现成SPMe正演＋多起点有界最小二乘/全局优化，先拟合少数参数；允许已有PyBOP等合法封装参与基线。
首轮探针：构造独立高精度DFN或不同网格参考，做局部敏感性/似然剖面；确认真值可辨识和SPMe正常优化已有多大误差。
淘汰/降档：若同一正演器同网格生成后少量最小二乘立即全解，或要求识别本不可辨识单参数，重设合同；不把求解器编译等待算难度。

独立评分：独立参考工况的电压/容量误差、区间覆盖、事件时间与物理界限；不可辨识场合按预测/参数组合评分，避免唯一原始参数硬判。
生成与划分：按化学参数族、温度、SOC范围和电流形状划分；参考与拟合模型网格/误差机制隔离，隐藏测量噪声与留出工况。
独立性与谱系：新电化学主来源，不复用MODFLOW数据；与其他科学反演共享方法但物理状态、事件和交付不同，需查原EdgeBench电池任务谱系。
离线/计算：已取6文件含测试，无实测电池数据，无候选运行。优先CPU有限参数/SPMe探针，DFN参考可离线预计算；CasADi/IDAKLU等依赖未验证。
许可观察：根LICENSE.txt为BSD-3-Clause条款；内置文献参数集及第三方实验曲线仍需记录各自来源，拟优先生成新数据。

**实际选读证据**
- [已有实验步骤参数化，并明确事件敏感性不准确的情形](https://github.com/pybamm-team/PyBaMM/blob/8996ec6479b9e2a79686e17956f6dfce8eaa301b/packages/pybamm/src/pybamm/simulation/simulation.py#L529-L557)；本地 [选读 529–557 行](../sources/s05_pybamm/files/packages/pybamm/src/pybamm/simulation/simulation.py)。
- [解析衰减方程精度和电池模型参数离散化健康测试](https://github.com/pybamm-team/PyBaMM/blob/8996ec6479b9e2a79686e17956f6dfce8eaa301b/packages/pybamm/tests/unit/test_simulation.py#L13-L42)；本地 [选读 13–42 行](../sources/s05_pybamm/files/packages/pybamm/tests/unit/test_simulation.py)。
- [SPMe从几何/参数/网格到求解的完整正常正演链](https://github.com/pybamm-team/PyBaMM/blob/8996ec6479b9e2a79686e17956f6dfce8eaa301b/examples/scripts/SPMe.py#L11-L32)；本地 [选读 11–32 行](../sources/s05_pybamm/files/examples/scripts/SPMe.py)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
