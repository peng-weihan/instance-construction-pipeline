# S02_DARTS · Darts 层级时序生成与协调

- 主来源：[unit8co/darts](https://github.com/unit8co/darts/tree/05192e9b9e7ed5d0bcabc27543424bd2776b3ce4)。
- 固定版本：`05192e9b9e7ed5d0bcabc27543424bd2776b3ce4`。
- 来源单元：MinT协调实现、协调测试和时序生成器；任务数据拟自建。
- 评估：`medium`；优先级 `hold_baseline`。

**拟题：跨层级分布变化下的概率预测与一致性**
给定多地区/产品层级时间序列与可用协变量，预测多步分位数或联合样本，同时保持聚合一致性；在季节、协变量效应和残差相关变化下验证。
交付：可重训预测管线、留出时窗的联合预测样本/分位数、层级一致性和校准报告。

**困难的因果来源**
- 逐条序列校准后再投影可能改变覆盖率；必须同时处理概率质量与聚合一致性。
- 短历史和相关残差使MinT协方差估计不稳；滚动验证若越过时间边界会泄漏未来信息。

基线：季节朴素、ETS/线性全局模型、BottomUp和现成MinT，使用训练窗残差估计协方差；不能把已有协调功能当缺失。
首轮探针：在不同层级图和结构断点上比较季节朴素＋BottomUp、全局回归＋MinT，判断合理目标是否已有轻量方案满足。
淘汰/降档：若只要求数值求和一致而不要求留出预测质量和校准，或一段MinT调用已满足全部合同，降档。

独立评分：隐藏滚动起点上评WIS/CRPS或pinball、分组覆盖、点误差；样本级聚合残差作可行性门槛，阈值先用基线校准。
生成与划分：用可审计季节/自回归/协变量生成机制组合层级，按生成机制与未来时间切分；不以随机打散时间点做测试。
独立性与谱系：新主来源；时序预测与旧金融策略任务共享技术但交付是预测分布而非配置策略。层级结构和机制变化才构成新实例。
离线/计算：已取5文件含生成器，无预训练模型或完整真实数据。先CPU中等规模滚动验证，概率深模属可选方案，尚未安装运行。
许可观察：Darts根LICENSE为Apache-2.0；示例所用外部旅游数据不随代码许可自动授权，本拟题优先自建数据。

**实际选读证据**
- [MinT已实现OLS、结构权重和残差协方差等方案](https://github.com/unit8co/darts/blob/05192e9b9e7ed5d0bcabc27543424bd2776b3ce4/darts/dataprocessing/transformers/reconciliation.py#L160-L217)；本地 [选读 160–217 行](../sources/s02_darts/files/darts/dataprocessing/transformers/reconciliation.py)。
- [现有测试覆盖多个MinT方法，说明协调本身是现成功能](https://github.com/unit8co/darts/blob/05192e9b9e7ed5d0bcabc27543424bd2776b3ce4/darts/tests/dataprocessing/transformers/test_reconciliation.py#L107-L136)；本地 [选读 107–136 行](../sources/s02_darts/files/darts/tests/dataprocessing/transformers/test_reconciliation.py)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
