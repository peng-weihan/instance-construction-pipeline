# F06_PHYSLEAN · Physlib — Hamiltonian Mechanics

固定来源：`leanprover-community/physlib` @ `059336966f1c21765a9249ed19dac0f35435f1fd`。
具体材料：Poisson bracket定义、乘法规则及Hamilton流导数定理
拟题：有限维Poisson代数与Hamilton守恒律

交付：对有限维实相空间和足够光滑函数证明规范坐标交换关系、Jacobi恒等式、Poisson括号的导子性质及沿Hamilton流的守恒推论；准确声明二阶光滑性。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 梯度、Fréchet导数、二阶混合导数对称性需要与坐标无关定义兼容。
- Jacobi取消和流上的链式法则必须共享符号约定及光滑性条件，数值轨道不构成证明。

正常基线：允许mathlib辛/Poisson/李代数定理、Clairaut和ring等正常自动化，先尝试现有几何实例桥接。
首个探针：核查当前依赖是否已有Jacobi完整结果；证明三函数的一个有限维混合导数关键项，再做完整Jacobi概念验证。
淘汰条件：现成Poisson实例直接给出所有目标，或新范围只剩ring标准化，则降档；若正则性假设不足必须修规格。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：HEPLean/PhysLean已迁到leanprover-community/physlib，仅计一次。选Physlib核心，不选较低审核PhyslibAlpha；原13无此主目标。Jacobi当前明确TODO，现有流导数仅是已完成参考，未声称新目标已证。
离线与计算：Lean4.35.0、lake锁、根许可和3个力学源码已取；未构建，独立内核、公理闭包和全部光滑性可行性未验。
许可观察：根LICENSE为Apache-2.0。
潜力：high；优先级：hold_reference。
证据：
- [括号按位置/动量梯度定义，Jacobi与规范交换关系明确TODO](https://github.com/leanprover-community/physlib/blob/059336966f1c21765a9249ed19dac0f35435f1fd/Physlib/ClassicalMechanics/HamiltonianMechanics/PoissonBracket.lean#L50)；实际阅读 50–91 行。
- [沿Hamilton流的导数等于Poisson bracket已有证明](https://github.com/leanprover-community/physlib/blob/059336966f1c21765a9249ed19dac0f35435f1fd/Physlib/ClassicalMechanics/HamiltonianMechanics/PoissonBracket.lean#L195)；实际阅读 195–237 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
