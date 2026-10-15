# F09_GRAPH · Graph Theory — Minors and Treewidth

固定来源：`rocq-community/graph-theory` @ `322e352b72c4ca3f153e5f80123c5020a0d40620`。
具体材料：minor映射、树分解及K4-free↔treewidth≤2证明
拟题：树宽二消元证书的可靠性与完备性

交付：定义有限图消元/分解证书，证明校验器接受则无K4 minor且有宽度≤2树分解，并从适用消元步骤构造完整证书；交付一般正确性证明而非只求一张图。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- minor支集的连通不交与分解袋覆盖条件需要在删除/补边/合并中保持。
- 存在性定理到可检消元证书需要显式构造与不变量，单个SAT解不能完成泛化定理。

正常基线：允许现有excluded_minor_TW2、图分解和有限反射自动化；先试库内算法/证书接口。
首个探针：从简单环及含二点分离集图验证证书定义，再证明一个删除/补边步骤的双向不变量并查有无同义checker。
淘汰条件：库已提供完全相同可计算证书及正确性，只需包装；或规格把bag size≤3错写树宽≤3，需先修定义。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：新主来源；与FourColor共享作者生态，但本簇不依赖平面Wagner可选FourColor包。避免把现有存在性定理删body后直接调用其推论。
离线与计算：Coq>=8.19、MathComp>=2.5、HB>=1.5及dune构建规格、meta和3个证明已取；未解精确依赖锁/跑内核。
许可观察：README与opam声明CeCILL-B，但固定树没有其链接指向的根LICENSE；须补原版许可文本和权链后发布派生包。
潜力：high；优先级：hold_license。
证据：
- [minor正反映射显式要求连通、互不相交与边见证](https://github.com/rocq-community/graph-theory/blob/322e352b72c4ca3f153e5f80123c5020a0d40620/theories/core/minor.v#L1)；实际阅读 1–31 行。
- [K4-free到袋大小≤3的树分解已有分离集归纳证明](https://github.com/rocq-community/graph-theory/blob/322e352b72c4ca3f153e5f80123c5020a0d40620/theories/core/excluded.v#L376)；实际阅读 376–425 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
