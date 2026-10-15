# F03_KOLMOGOROV · Kolmogorov Extension 4

固定来源：`RemyDegenne/kolmogorov_extension4` @ `7d76e184c3d2138a2741baf923b57e9a01b9cf25`。
具体材料：紧柱集系统、正则content和投射极限测度
拟题：时变状态空间的核到路径律及唯一性证明

交付：从时变Polish状态空间初始分布和可测转移核构造有限维联合律，证明一致性、路径律存在唯一及截断/重索引相容。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 递推核积分与依赖类型坐标限制需要共同满足可测性及投射一致性。
- 有限维到无限路径测度之间有正则性、σ可加性与唯一性条件，有限样本不能代替证明。

正常基线：优先查mathlib Ionescu–Tulcea、Markov路径律和现成KolmogorovAPI。
首个探针：比较同义路径律，先闭合非齐次核的有限维投射一致性和唯一性。
淘汰条件：库已有完整路径律，只需参数改名或别名则淘汰该范围。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：共享旧brownian-motion的概率基础，但不要求Brownian连续版本。源码可能已上游mathlib；原隐藏命题未全取，重叠仍需归一化检查。
离线与计算：Lean4.33.0-rc1和lake锁已取；仅3个定向证明文件，完整依赖闭包、缓存和内核未验。
许可观察：根LICENSE为Apache-2.0。
潜力：high；优先级：hold_baseline。
证据：
- [闭紧柱集紧系统有具体证明](https://github.com/RemyDegenne/kolmogorov_extension4/blob/7d76e184c3d2138a2741baf923b57e9a01b9cf25/KolmogorovExtension4/CompactSystem.lean#L252)；实际阅读 252–287 行。
- [projectiveLimit及其定理已实现，不可当新增能力](https://github.com/RemyDegenne/kolmogorov_extension4/blob/7d76e184c3d2138a2741baf923b57e9a01b9cf25/KolmogorovExtension4/KolmogorovExtension.lean#L99)；实际阅读 99–165 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
