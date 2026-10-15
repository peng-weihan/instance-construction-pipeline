# F02_BROUWER · Brouwer / Scarf

固定来源：`math-xmum/Brouwer` @ `f9dc162170e8711f78059a87edcd38ffc44a1bfb`。
具体材料：单纯形Brouwer、有限乘积回缩和公理审计入口
拟题：凸多面体回缩及连续自映射不动点证明

交付：在独立有限约束多面体表示上证明非空紧凸条件、与单纯形/乘积的连续回缩关系及自映射不动点存在性，明确空维数和边界。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 离散Scarf、紧性子列和坐标和约束连接，单纯形结论不能直接当任意表示结论。
- 投影嵌入需要兼顾分母为零、连续性及回缩恒等式。

正常基线：允许Brouwer_Product及mathlib紧凸不动点定理，先试短回缩适配。
首个探针：固定依赖版本检索同义定理，闭合非单纯形多面体的回缩；后续执行上游AxiomAudit。
淘汰条件：只需现有紧凸Brouwer直接实例化或简单类型别名则降为短题。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：替换与原medium_prime_number_theorem重叠的PNT源；证明产物不是求Nash策略。公开Brouwer/Nash证明污染需按子图隔离。
离线与计算：Lean4.33.0、lake锁、MIT许可、Scarf/Brouwer/示例/审计已取；AxiomAudit只读未执行。
许可观察：根LICENSE为MIT；论文或蓝图另用需单独核权。
潜力：high；优先级：hold_baseline。
证据：
- [Brouwer终点有具体子列和坐标证明](https://github.com/math-xmum/Brouwer/blob/f9dc162170e8711f78059a87edcd38ffc44a1bfb/Gametheory/Brouwer.lean#L734)；实际阅读 734–770 行。
- [乘积终点通过连续投影嵌入回缩实现](https://github.com/math-xmum/Brouwer/blob/f9dc162170e8711f78059a87edcd38ffc44a1bfb/Gametheory/Brouwer_product.lean#L662)；实际阅读 662–678 行。
- [上游提供公理审计入口，本轮没有执行](https://github.com/math-xmum/Brouwer/blob/f9dc162170e8711f78059a87edcd38ffc44a1bfb/Gametheory/AxiomAudit.lean#L1)；实际阅读 1–32 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
