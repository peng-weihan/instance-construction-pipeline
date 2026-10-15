# F01_EQUATIONAL · Equational Theories

固定来源：`teorth/equational_theories` @ `1aec8a7acf223b7c56e4830977b6e90d4ef1924b`。
具体材料：MagmaLaw推导、自由magma商模型、Birkhoff完备性
拟题：多类型等式逻辑的自由代数与完备性簇

交付：对有限多类型算子签名形式化项代换、可导关系和商代数，证明可靠性、自由模型通用性质与完备性；单类型magma仅作作者参考。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 带类型代换与同余商必须兼容变量扩张，不能用有限真值表替代一般命题。
- 商运算良定义、求值同态和通用性质构成连续依赖链。

正常基线：查mathlib通用代数/等式逻辑同义定理，允许simp、aesop和正常检索。
首个探针：正规化目标，尝试通用定理短适配，再证明双类型求值与代换交换引理。
淘汰条件：现成多类型完备性可直接实例化，或改名即可复用全部参考，则淘汰此范围。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：主来源未在旧登记中；公开单类型完整同义定理必须隔离，不能只删除body却继续import同义结果。新增签名不自动证明新难度。
离线与计算：已取Lean4.29.1、lake锁、根许可和3个证明/定义文件；完整mathlib缓存、离线构建和内核未验。
许可观察：根LICENSE为Apache-2.0。
潜力：high；优先级：hold_baseline。
证据：
- [推导系统含代换、同余和传递规则](https://github.com/teorth/equational_theories/blob/1aec8a7acf223b7c56e4830977b6e90d4ef1924b/equational_theories/MagmaLaw.lean#L21)；实际阅读 21–62 行。
- [现有单类型Birkhoff完备性已有证明项，不是尚缺能力](https://github.com/teorth/equational_theories/blob/1aec8a7acf223b7c56e4830977b6e90d4ef1924b/equational_theories/Completeness.lean#L130)；实际阅读 130–173 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
