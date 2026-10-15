# 06_wasm_validation：类型验证、间接调用与模块链接的VM

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/WebAssembly/spec/tree/d910f03bd6d6477656fc5070b5098e8f909305d3)；commit `d910f03bd6d6477656fc5070b5098e8f909305d3`。

许可观察：document/core 为 W3C 文档许可；interpreter 和 test 为 Apache-2.0。根 LICENSE 不是单一 Apache 许可。

## 已有能力与拟出的题

规格仓库已有参考解释器、valid 模块与大量 assert_invalid/assert_trap 测试。当前源码 SHA 不在本报告中等同于 v1.0.0 tag；旧小样只实现 i32 的窄 VM。

从明确冻结的 WebAssembly 子集合同构造类型验证、模块实例化与执行器，覆盖 structured control、stack-polymorphism、tables/call_indirect、imports 和内存边界。

原题类别参照：arc_compiler_runtime / dependent_type_checker：从规格构建带验证的执行系统。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 模块验证、链接、实例化、解释执行的实际源码

- 显式列出支持 opcode 和导入 ABI；未支持特性必须稳定拒绝

## 参考与迭代评分

隔离的官方解释器与固定 V8/其他实现交叉对照；生成合法/非法的结构化模块并缩减差异。两个参考不一致先剔除争议输入。

拟评分维度：

- 类型验证含不可达代码

- 控制栈与函数调用

- table 和间接调用

- 链接/实例化阶段

- 内存/数值边界及 trap 分类

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- i32/control 跑通后处理类型多态、分支合流和非法模块

- 加入多模块导入、间接调用及实例化时失败的阶段一致性

最强廉价基线：测已有 VM 绑定或 wasm 执行库 wrapper 能覆盖多少；若交付 API/正常依赖允许其完整通过，应放弃此 profile，不能临时禁止工具。

先做的否证探针：先冻结指令/ABI 子集，拿旧 i32 实现跑新增 validation + linking 用例，确认新增分数来自真实能力而非多造同类算术题。

构造风险：

- 完整 WASM 规范远超小样范围；必须先收敛可实现子集

- 旧负数除法缺陷只伤很少样例，需按语义维度重审权重

- 源码 SHA 与所谓 v1 标签需要分别记录

## 实际取得的源码证据

- [独立类型验证实现](https://github.com/WebAssembly/spec/blob/d910f03bd6d6477656fc5070b5098e8f909305d3/interpreter/valid/valid.ml#L89)；本地 [`sources/06_wasm_validation/files/interpreter/valid/valid.ml:89`](../sources/06_wasm_validation/files/interpreter/valid/valid.ml)。

- [间接调用的非法模块用例](https://github.com/WebAssembly/spec/blob/d910f03bd6d6477656fc5070b5098e8f909305d3/test/core/call_indirect.wast#L790)；本地 [`sources/06_wasm_validation/files/test/core/call_indirect.wast:790`](../sources/06_wasm_validation/files/test/core/call_indirect.wast)。

- [控制栈测试](https://github.com/WebAssembly/spec/blob/d910f03bd6d6477656fc5070b5098e8f909305d3/test/core/unwind.wast#L212)；本地 [`sources/06_wasm_validation/files/test/core/unwind.wast:212`](../sources/06_wasm_validation/files/test/core/unwind.wast)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/06_wasm_validation/manifest.json)。[完整 Git 文件树索引](../sources/06_wasm_validation/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

旧 profile：samples/software-multiline-001/03_wasm；223 case 的旧分数仅适用于旧 i32 profile。

