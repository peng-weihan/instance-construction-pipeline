# S01_DEEPXDE · DeepXDE 反问题示例

- 主来源：[lululxvi/deepxde](https://github.com/lululxvi/deepxde/tree/99b6620386d18cefb1549dddb7b7fe468cfad607)。
- 固定版本：`99b6620386d18cefb1549dddb7b7fe468cfad607`。
- 来源单元：Poisson未知源场示例、问题规格和PDE数据接口；作为生成器原型，非现成高难题。
- 评估：`medium`；优先级 `hold_baseline`。

**拟题：稀疏含噪观测下的源场反演与新边界预测**
给定多组边界激励和稀疏状态观测，识别低维可辨识源场族，输出源场及未见边界条件下的解和不确定度。源场频谱、测点布局和噪声联合变化，具体生成器需新建。
交付：可离线调用的反演/预测程序、参数或场估计、置信区间与验证记录。

**困难的因果来源**
- 二阶微分会放大观测噪声；拟合状态准确不保证源场正确，必须选择正则化并验证识别稳定性。
- 测点缺失与激励变化使某些模式不可辨识；多实验联合估计和新条件预测需要共享物理约束。

基线：有限差分/有限元正演＋线性Tikhonov或样条正则化＋交叉验证；另跑现成PINN，允许成熟库。
首轮探针：在公开1D示例之外，比较正则化线性解、PINN和高精度正演参考；确认源场族可辨识且基线有合理提升空间。
淘汰/降档：若仅恢复公开sin(pi*x)，或样条/线性逆解已覆盖所有合理目标，降为简单科学练习；不靠训练轮数制造难度。

独立评分：独立高精度正演检查留出状态误差、可辨识频段源场误差、PDE/边界残差和区间覆盖；先固定规范化与各指标权重。
生成与划分：自建不同源场谱族/边界激励/测点布局；按函数族和噪声机制划分，隐藏真实场与参考网格，开发只给少量完整样例。
独立性与谱系：不同于旧MODFLOW污染源任务的领域与生成机制，但同属逆问题；原EdgeBench科学PDE谱系须查任务级重复；换seed不算新家族。
离线/计算：已取源码、规格和许可共5文件；无数据/模型训练。CPU小网格原型可先探针，GPU训练非必要；环境轮子和参考正演尚未闭合。
许可观察：根LICENSE为LGPL-2.1文本；自建生成数据的权限与代码再分发义务需分别记录。

**实际选读证据**
- [现成示例只有一维正弦状态、联合u/q输出和加权PINN训练](https://github.com/lululxvi/deepxde/blob/99b6620386d18cefb1549dddb7b7fe468cfad607/examples/pinn_inverse/elliptic_inverse_field.py#L7-L45)；本地 [选读 7–45 行](../sources/s01_deepxde/files/examples/pinn_inverse/elliptic_inverse_field.py)。
- [公开问题已直接给出真解，不能将照抄示例作为高难任务](https://github.com/lululxvi/deepxde/blob/99b6620386d18cefb1549dddb7b7fe468cfad607/docs/demos/pinn_inverse/elliptic.inverse.field.rst#L7-L17)；本地 [选读 7–17 行](../sources/s01_deepxde/files/docs/demos/pinn_inverse/elliptic.inverse.field.rst)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
