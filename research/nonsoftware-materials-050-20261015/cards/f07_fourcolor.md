# F07_FOURCOLOR · Four Color — Combinatorial Hypermaps

固定来源：`rocq-community/fourcolor` @ `c1d6b1cd5288bea4b067aac13cdde3c18dffe018`。
具体材料：超图排列、面/点着色及four_color_hypermap证明
拟题：带边界迹的平面超图拼接与着色转移

交付：形式化具有指定边界环的超图拼接，证明连接/平面条件保持、边界颜色迹兼容和局部着色到全局着色的转移；四色主定理仅作已知上界。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 超图以edge/node/face排列表示，拼接需保持排列恒等式及拓扑不变量。
- 局部边界色迹与全局邻接约束必须一致，直接枚举一张图不能证明一般拼接。

正常基线：允许现有ring_trace、preembedding、dual及four_color_hypermap，先试标准连接或重标号证明。
首个探针：检索现有边界拼接/着色扩张API，并核验最小非平凡边界的结构及着色转移。
淘汰条件：全部目标可由现有preembedding一条引理给出，或只改变颜色名/有限图size，则不是新的高难题。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：math-comp/fourcolor迁移至rocq-community/fourcolor，只计一次；与F09共享MathComp及可选FourColor依赖，不能当完全独立技能。选组合子库，避免实数公理化拓扑入口。
离线与计算：根许可、Rocq/Coq依赖opam及_CoqProject已取；9个定向文件，完整MathComp锁和上游健康内核未验，有限配置计算耗时不计难。
许可观察：根LICENSE为CeCILL-B，源码头一致；不应按MIT处理。
潜力：medium；优先级：hold_baseline。
证据：
- [面着色、点着色和边界ring_trace有独立定义](https://github.com/rocq-community/fourcolor/blob/c1d6b1cd5288bea4b067aac13cdde3c18dffe018/theories/proof/coloring.v#L65)；实际阅读 65–122 行。
- [四色终点经cube与unavoidability/reducibility得出，不是未知定理](https://github.com/rocq-community/fourcolor/blob/c1d6b1cd5288bea4b067aac13cdde3c18dffe018/theories/proof/combinatorial4ct.v#L1)；实际阅读 1–30 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
