# 形式数学与形式验证：10个新主来源

本组把软工库存之外的“证明产物”单独展开：代数、拓扑、概率、构造分析、数理逻辑、数学物理、组合图论、有限群与编译优化语义。分类依据是交付内核可检证明；CoRN的数值例子、CompCert的代码只作为定义/规格和作者参考，不将求数值或编译器实现本身计作目标。

当前共有10个不同主仓库、81个固定SHA原始文件。仅定向阅读下表区间，没有全仓覆盖或健康编译。本轮所有`task_constructed/runtime_verified/difficulty_verified`均为false。普通库、自动化和已经存在的同义定理均是正常基线；若短适配完成合同，应直接下调候选。

## 候选与实际阅读

| ID | 主来源与拟题簇 | 实际选读文件和行区间 | 当前优先级 |
|---|---|---|---|
| F01 | [Equational Theories](https://github.com/teorth/equational_theories)：多类型等式推导、自由模型与完备性 | `MagmaLaw.lean:21–62`；`Completeness.lean:130–173`，均在`equational_theories/` | hold_baseline |
| F02 | [Brouwer](https://github.com/math-xmum/Brouwer)：多面体回缩和不动点 | `Gametheory/Brouwer.lean:734–770`；`Brouwer_product.lean:662–678`；`AxiomAudit.lean:1–32` | hold_baseline |
| F03 | [Kolmogorov Extension 4](https://github.com/RemyDegenne/kolmogorov_extension4)：核到路径律及唯一性 | `KolmogorovExtension4/CompactSystem.lean:252–287`；`KolmogorovExtension.lean:99–165` | hold_baseline |
| F04 | [CoRN](https://github.com/rocq-community/corn)：构造性求积误差证书 | `ftc/IntegrationRules.v:24–72`；`ftc/Taylor.v:195–235`；`examples/IntegrationExamples.v:22–50` | scope_probe |
| F05 | [Foundation](https://github.com/FormalizedFormalLogic/Foundation)：LK反模型与语言扩张 | `Foundation/FirstOrder/LK/Completeness/CanonicalModel.lean:10–54`；`CounterModel.lean:173–220` | hold_baseline |
| F06 | [Physlib](https://github.com/leanprover-community/physlib)：Poisson代数、Jacobi与守恒律 | `Physlib/ClassicalMechanics/HamiltonianMechanics/PoissonBracket.lean:50–91,195–237` | hold_reference |
| F07 | [FourColor](https://github.com/rocq-community/fourcolor)：超图拼接与边界着色迹 | `theories/proof/coloring.v:65–122`；`combinatorial4ct.v:1–30` | hold_baseline |
| F08 | [Odd Order](https://github.com/math-comp/odd-order)：互素群作用及固定点不变量 | `theories/BGsection1.v:1–24,60–99`；`wielandt_fixpoint.v:452–490` | hold_license |
| F09 | [Graph Theory](https://github.com/rocq-community/graph-theory)：树宽二消元证书正确性 | `theories/core/minor.v:1–31`；`excluded.v:376–425` | hold_license |
| F10 | [CompCert](https://github.com/AbsInt/CompCert)：新RTL优化规则语义保持 | `backend/Constprop.v:166–200`；`Constpropproof.v:581–625` | hold_license |

区间是实际读取范围；保存了部分完整源码文件并不等于完整文件逐行分析。F04值得先做小范围参考闭合，但不能从构造实数的编译或计算慢推断长程困难。F01/F02/F03/F05/F07主要风险是现成一般定理已覆盖目标；F06主要风险是新增目标还没有闭合参考。所有10项都尚未形成可投放题包。

## 版本、许可及迁移

五个Lean源均保存`lean-toolchain`、`lakefile`和`lake-manifest.json`；五个Rocq源（F04及F07–F10）保存opam或configure/Makefile构建规格。Physlib与Foundation等工具链版本不同，不能共享一个不加锁的最新版mathlib环境。Rocq opam仅是约束范围，尚未解成完整依赖锁。

F06由`HEPLean/PhysLean`迁移到`leanprover-community/physlib`，F07由`math-comp/fourcolor`迁移到`rocq-community/fourcolor`，已经通过官方GitHub跳转确认；旧别名保留在revision/manifest中且不重复计数。F01/F03/F05/F06根许可为Apache-2.0，F02为MIT，F04为GPL-2.0，F07为CeCILL-B。

F08/F09固定树未见根`LICENSE`文件：F08的opam/源码头声明CeCILL-B，F09的README/opam声明CeCILL-B但其根许可链接没有对应文件。需要补齐文本和权链，不能宣称未知即无许可。F10根许可为INRIA非商业协议或AbsInt协议；官方README明确非自由软件。研究评估授权不自动覆盖商业训练和派生题包再分发，因此三项均hold_license。

## 原任务谱系与弃选来源

明确避开原Carleson、PFR、FLT、sphere eversion、NF、combinatorial games、Brownian motion等已知来源；同时避开原`medium_prime_number_theorem`、`godel_incompleteness_formalization`、`cup_product_formalization`、`erdos392_formalization`、`turing_machine_halting_proofs`的主目标。原形式任务的完整隐藏目标/依赖包并未全部取得，不能据名称比较保证命题归一化后的零重叠。

初选`AlexKontorovich/PrimeNumberTheoremAnd`与原素数定理方向明显重叠，替换为F02；只保留元数据，不计正式来源。F05保留仓库但改选一阶LK反模型簇，避免Gödel/停机目标。

初选`Sphere-Packing-Lean`与sphere eversion并非同一项目，但固定SHA`de0ce2b6d5a6622ddae2c409987cb45f678b8cf9`的`SpherePacking/MainTheorem.lean:16`直接使用`sorry`，其LPBound和PeriodicPacking也有缺口。已改用F04 CoRN；球堆积材料只保留为弃选证据，不计正式10项。不能因为末端`by`块存在就宣称主结论或依赖闭包完成。

`rocq-community/coquelicot`不存在；官方opam指向GitLab INRIA主源，不把GitHub同名第三方镜像充作官方来源。本组选择官方GitHub可锁定的CoRN作为分析材料。

F03与旧Brownian共享概率基础，F05与旧Gödel共享数理逻辑生态，F07–F09共享MathComp；因此10个主来源不等于10个完全独立数学技能族。CoRN与原analysis领域的隐藏命题重叠也需后续目标比对。

## 证明状态与后续关口

对正式10项**仅已获取**的`.lean/.v`文件做词法扫描，未命中`sorry/axiom/admit/Admitted`（扫描含注释，不解析语法）。这不是传递闭包无公理、内核通过或命题正确的证明：依赖中可能存在公理，结构参数也可能前提过强。F02的`AxiomAudit.lean`只说明上游提供审计入口，本轮未执行。F07的组合四色子簇与其经典实数公理化入口必须分开审依赖；F06的Jacobi在源码中明确是TODO，新目标尚无健康参考。

所有候选的共通关口是：先固定命题签名和合理假设，构造健康作者参考及最小starter；再运行普通自动化/同义定理检索基线；最后用独立声明和干净内核评测。不能只删除一个定理body却仍导入它的等价版本，不能用许多自然数或改变量名造出伪独立实例。

需要后续执行的检查包括：递归`#print axioms`或`Print Assumptions`、求解环境中的导入/命题同义泄漏、命题与自然语言的忠实性、假设可满足性，以及超时是否来自证明探索而非依赖编译。尚未执行这些检查，也没有模型求解或六小时难度证据。
