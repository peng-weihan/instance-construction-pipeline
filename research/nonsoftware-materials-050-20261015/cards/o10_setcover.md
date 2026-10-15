# O10_SETCOVER 覆盖结构族上的集合覆盖解质量优化

- 类别：optimization；潜力：medium；优先级：hold_data。素材研究，未构题/运行/验证难度。
- 主来源：fontanf/setcoveringsolver@6b24f8cb0a8e5baa6849283e5250aa4a3bd09aff。
- 固定版本清单：[manifest](../sources/o10_setcover/manifest.json)。
- 本项素材单元：显式覆盖计数/成本证书与已有greedy/LNS/CP-SAT方法；数据CSV是目录而非完整实例

## 拟交付与难度

先限定unicost set cover，提交覆盖全部元素的集合ID子集，在冻结预算下减少集合数。
- 交付：集合证书、搜索程序、覆盖与目标值核对。
- 难度来源：集合高度重叠时贪心容易进入局部最优，移除/重新覆盖需要联合交换。
- 难度来源：reduction、局部搜索与大邻域时间分配对结构族敏感，但已有贪心/CP-SAT很强。

## 验证与划分

- 正常基线：原生所有适用greedy、LNS、MILP/HiGHS和OR-Tools，允许按公开结构选择。
- 首个探针：先建立授权实例或原创incidence生成器，再比较完整现成算法前沿；不使用目录CSV代替实际运行材料。
- 停止条件：现成组合已饱和，或所谓新实例只是PACE文件改名/重排，则退出当前方向。
- 独立评测：独立检查集合ID唯一/合法及并集覆盖，并重算集合数；小宇宙穷举，不能信candidate covers计数。
- 生成与划分：按incidence相关性、稀疏/密集和可行结构生成新族，原PACE/GECCO分发条款未确认；不能只新seed。
- 谱系/重叠：与旧packingsolver同作者/optimizationtools依赖谱系，但不是同一主来源；必须按底层实例结构去重。
- 离线/计算：C++及依赖预置；download_data.py指向外部Google Drive压缩包未执行，当前无完整benchmark数据。
- 许可观察：根MIT；外部数据与最优答案文件许可未确认，候选hold_data。

## 选读证据

- [include/setcoveringsolver/solution.hpp:40](https://github.com/fontanf/setcoveringsolver/blob/6b24f8cb0a8e5baa6849283e5250aa4a3bd09aff/include/setcoveringsolver/solution.hpp#L40)：Solution接口将完整覆盖作为可行性，成本与元素计数独立记录。
- [README.md:1](https://github.com/fontanf/setcoveringsolver/blob/6b24f8cb0a8e5baa6849283e5250aa4a3bd09aff/README.md#L1)：README已有多种贪心、MILP/CP-SAT和LNS，不把它们冒称新方法。
