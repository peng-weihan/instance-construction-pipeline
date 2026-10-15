# F10_COMPCERT · CompCert — Optimization Correctness

固定来源：`AbsInt/CompCert` @ `e276a3f881669252e2a5c4b5fec06f51f7143161`。
具体材料：RTL常量传播transf_instr及前向模拟正确性证明
拟题：新局部优化规则的语义保持证明链

交付：在给定RTL语义和明确的新优化规则下，证明抽象值可靠性、寄存器/内存匹配、单步模拟及程序前向模拟；实现规则本身保持小范围，评分主体是证明。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 未定义值、地址/内存扩展和数据流近似共同决定规则何时可用，数学整数等价不自动成立。
- 分支后继变化和可消去步骤要求良基度量及匹配关系，局部指令结果正确不足以推出可观察行为保持。

正常基线：允许CompCert已验证Constprop和现有strength reduction证明；先试现有通用模拟框架或已实现同义规则。
首个探针：先确认确为新增且语义正确的规则，闭合一条涉及内存/控制流的步骤模拟；构题前跑原参考健康构建与Print Assumptions。
淘汰条件：规则已被现有优化/引理覆盖而仅需实例化，或题目难点只在安装编译器，则缩减/淘汰；许可不允许目标用途则不打包。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：现有软工素材登记未见同仓；交付为Rocq证明因此归形式验证。公开完整Constpropproof是作者参考，新增规则和目标签名要独立审查，不能假称未有常量传播证明。
离线与计算：已取configure、Makefile、VERSION及优化/证明/Smallstep文件；完整目标架构、Rocq/OCaml/Menhir环境和内核未验证。
许可观察：根LICENSE为INRIA非商业许可或AbsInt软件协议；README明确非自由软件。研究评估用途不等于可任意训练/商业再分发，先hold_license。
潜力：high；优先级：hold_license。
证据：
- [变换指令依赖抽象寄存器及内存分析并可能改后继](https://github.com/AbsInt/CompCert/blob/e276a3f881669252e2a5c4b5fec06f51f7143161/backend/Constprop.v#L166)；实际阅读 166–200 行。
- [程序正确性以带良基度量的forward_simulation证明](https://github.com/AbsInt/CompCert/blob/e276a3f881669252e2a5c4b5fec06f51f7143161/backend/Constpropproof.v#L581)；实际阅读 581–625 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
