# F08_ODDORDER · Odd Order — Coprime Actions

固定来源：`math-comp/odd-order` @ `ba734c020d9f7dce5758fa822904dea29e2624ba`。
具体材料：BGsection1有限群结构定义及可解Wielandt不动点恒等式
拟题：互素群作用的正规列分解与固定点不变量

交付：对带G稳定正规列的有限可解群建立中心化子阶的分解和加权固定点乘积恒等式，证明商群/正规子群桥接及所需互素条件；不把奇数阶定理整段恢复作为默认题。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 群作用、商群中心化子和互素阶条件在归纳每层都要保持。
- 加权固定点计数与模表示/同态结构共同作用，整数代数化简只处理末端。

正常基线：允许现有solvable_Wielandt_fixpoint、MathComp coprime quotient centralizer及群自动化，先试直接推论。
首个探针：对两层非平凡正规列写出精确目标并尝试现有恒等式；审查新增分解是否仅是现有定理重复。
淘汰条件：直接套Wielandt加bigop即可闭合全合同，或删互素条件使命题错误，则重设范围。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：独立主仓库但与其他Rocq项共享MathComp；不覆盖原FLT/数论主目标。公开proof已有同义加权恒等式，必须将其当基线而非新发现。
离线与计算：实际Rocq opam规格和兼容包、_CoqProject、3个证明文件已取；依赖尚未完全版本锁定，未构建/检查递归假设。
许可观察：当前树无根LICENSE文件；opam和BGsection1头声明CeCILL-B。完整许可文本与打包权链需补齐后再发布题包。
潜力：medium；优先级：hold_license。
证据：
- [源码头声明CeCILL-B并列所覆盖群论结果](https://github.com/math-comp/odd-order/blob/ba734c020d9f7dce5758fa822904dea29e2624ba/theories/BGsection1.v#L1)；实际阅读 1–24 行。
- [p稳定与正规生成等结构有显式定义](https://github.com/math-comp/odd-order/blob/ba734c020d9f7dce5758fa822904dea29e2624ba/theories/BGsection1.v#L60)；实际阅读 60–99 行。
- [Wielandt固定点乘积恒等式有具体正规子群/商群归纳证明](https://github.com/math-comp/odd-order/blob/ba734c020d9f7dce5758fa822904dea29e2624ba/theories/wielandt_fixpoint.v#L452)；实际阅读 452–490 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
