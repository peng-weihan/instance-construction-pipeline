# F05_LOGIC · Foundation — First-order LK

固定来源：`FormalizedFormalLogic/Foundation` @ `c3eb37ae896dc8f1d239ba1511e74d9f25e9d158`。
具体材料：一致序列偏序、典范forcing、Henkin项模型反模型
拟题：语言扩张下的反模型与紧致性证明链

交付：在固定一阶语言/证明系统接口下证明保守语言扩张、有限可满足性到模型存在性和反模型见证的可迁移性；不得把原Gödel不完备性当新目标。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 语法替换、自由/绑定变量和语言嵌入必须与项模型语义相容。
- 典范forcing、泛滤子、Henkin见证到真实结构求值需要逐层桥接，单条一阶自动化不覆盖元定理。

正常基线：允许现有LK完备性、compactness及语言重命名引理，先查目标是否已被短推论覆盖。
首个探针：比较库内紧致性/保守扩张结果，闭合一个新语言扩张的forcing与求值交换图；后续审目标递归公理。
淘汰条件：完全可由现成compactness或consequence定理一行推出，或目标定义不忠实/前提不可满足，则淘汰范围。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：与原godel_incompleteness_formalization同属逻辑但选LK反模型子图，避开不完备性/停机簇；是否同原隐藏源或同义目标待核，公开proof必须作者侧隔离。
离线与计算：Lean4.35.0及lake锁已取；CanonicalModel/CounterModel和导出模块定向读取，mathlib缓存及完整公理闭包未执行。
许可观察：根LICENSE为Apache-2.0。
潜力：high；优先级：hold_baseline。
证据：
- [一致序列偏序及forcing明确依赖不可证性](https://github.com/FormalizedFormalLogic/Foundation/blob/c3eb37ae896dc8f1d239ba1511e74d9f25e9d158/Foundation/FirstOrder/LK/Completeness/CanonicalModel.lean#L10)；实际阅读 10–54 行。
- [项模型forcing lemma连接结构求值，继而构造可满足性反模型](https://github.com/FormalizedFormalLogic/Foundation/blob/c3eb37ae896dc8f1d239ba1511e74d9f25e9d158/Foundation/FirstOrder/LK/Completeness/CounterModel.lean#L173)；实际阅读 173–220 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
