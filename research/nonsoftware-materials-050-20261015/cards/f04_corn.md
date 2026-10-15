# F04_CORN · CoRN Constructive Analysis

固定来源：`rocq-community/corn` @ `ada7c0b497ff15dd67cf7932c6f20e143a2aee2f`。
具体材料：构造性Taylor余项、变量代换积分规则及可计算积分示例
拟题：带可证明误差界的构造性求积证书

交付：对具有显式导数界和连续模数的函数，证明分段求积误差界、区间代换的证书组合及有理输出区间包含真实积分；交付核可检证明而非拟合数值。
证明产物：固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。

复杂性来源：
- 构造实数的apartness、偏函数定义域见证和区间次序必须贯穿代换与Taylor余项。
- 局部误差到分区总误差及有理包围证书需要连接分析定理与可计算表示。

正常基线：使用CoRN已有Taylor、IntegrationBySubstition、Integrate及标准数值证明自动化，先试直接生成证书。
首个探针：固定opam版本后跑上游健康编译，再对一个非多项式小函数证明局部/全局误差桥；读取既有可计算积分接口是否已全覆盖。
淘汰条件：现有求积器已提供完整同义证书，只需调用和打印结果，或题目只是大精度计算等待，则下调。

独立评测：grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。
生成与划分：按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。
谱系/污染：新仓库；与原lean_analysis领域可能相邻但Rocq构造分析目标不同，原隐藏命题未知仍需比较。替换不闭合的E8 Sphere-Packing源；不是把公开Taylor定理改名当原创。
离线与计算：已取opam Coq>=8.19,<9.1或dev、math-classes/elpi/bignums规格和3个证明/示例；尚未解出全依赖锁或执行示例，构建等待不计难度。
许可观察：根LICENSE和opam标GPL-2.0；派生题包须保留相应许可与归属，不能整体改MIT。
潜力：high；优先级：scope_probe。
证据：
- [积分变量代换的全部定义域和连续性假设显式列出](https://github.com/rocq-community/corn/blob/ada7c0b497ff15dd67cf7932c6f20e143a2aee2f/ftc/IntegrationRules.v#L24)；实际阅读 24–72 行。
- [Taylor余项存在性有具体构造性证明](https://github.com/rocq-community/corn/blob/ada7c0b497ff15dd67cf7932c6f20e143a2aee2f/ftc/Taylor.v#L195)；实际阅读 195–235 行。
- [示例展示有理近似和统一连续积分接口，本轮未执行](https://github.com/rocq-community/corn/blob/ada7c0b497ff15dd67cf7932c6f20e143a2aee2f/examples/IntegrationExamples.v#L22)；实际阅读 22–50 行。

状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。
