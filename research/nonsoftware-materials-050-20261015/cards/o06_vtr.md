# O06_VTR 固定网表与器件约束下的FPGA布局质量优化

- 类别：optimization；潜力：high；优先级：hold_reference。素材研究，未构题/运行/验证难度。
- 主来源：verilog-to-routing/vtr-verilog-to-routing@5c65c868eb4e4d03697010e331d6abaa1cb46d4e。
- 固定版本清单：[manifest](../sources/o06_vtr/manifest.json)。
- 本项素材单元：VPR布局验证、正式region约束与小任务配置；不采用尚未合并的relative macros

## 拟交付与难度

冻结已pack网表、器件和合法region约束，交付块位置或布局策略，在合法布局下改善线长与固定时序指标。
- 交付：可验证.place/位置证书、搜索程序和冻结VPR重算指标。
- 难度来源：资源类型、区域约束和互连拓扑限制离散位置，局部线长改善可能损害关键路径。
- 难度来源：增量代价与完整重算的一致性、温度/移动候选和时间预算产生真实搜索取舍，但默认placer已成熟。

## 验证与划分

- 正常基线：当前VPR默认placer/正常退火与时序选项；现成布局/图划分方案可用。
- 首个探针：先构建健康headless闭包并校验默认结果，确认只使用已实现的region功能，再测默认参数前沿。
- 停止条件：奖励依赖未实现relative_macro_list，或收益只是默认配置差异/环境等待，则停止当前范围。
- 独立评测：冻结可信VPR做独立位置合法性/代价完整重算，另查块唯一性/容量/region；不采用候选上报增量cost。
- 生成与划分：新网表结构族与器件/约束配置，按电路谱系划分；公开power_quick只是配置入口，引用的完整网表/架构未下载。
- 谱系/重叠：与原CPU/硬件优化有领域联系，核心交付是布局解而非修VPR；独立netlist与评价范围仍需建立。
- 离线/计算：完整VPR和架构/网表资产较重，先hold_reference；构建成本不作为求解难度。
- 许可观察：VTR多组件许可汇编，LICENSE.md要求按VPR/ABC/ODIN及benchmark逐项核；不能统一按MIT。

## 选读证据

- [vpr/src/place/placer.cpp:252](https://github.com/verilog-to-routing/vtr-verilog-to-routing/blob/5c65c868eb4e4d03697010e331d6abaa1cb46d4e/vpr/src/place/placer.cpp#L252)：Placer用verify_placement与完整代价检查验证布局不变量。
- [doc/src/vpr/relative_placement_constraints.rst:1](https://github.com/verilog-to-routing/vtr-verilog-to-routing/blob/5c65c868eb4e4d03697010e331d6abaa1cb46d4e/doc/src/vpr/relative_placement_constraints.rst#L1)：当前relative placement文档明确实现未合并，读入后报错；该功能不纳入本候选。
