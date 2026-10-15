# K05_CVXPORTFOLIO 含交易成本与流动性的滚动投资研究案卷

- 类别：knowledge；潜力：medium；优先级：hold_data。素材研究，未构题/运行/验证难度。
- 主来源：cvxgrp/cvxportfolio@351c782b9b8b395c1a5f886b77e0d55f1bc9396e。
- 固定版本清单：[manifest](../sources/k05_cvxportfolio/manifest.json)。
- 本项素材单元：MarketSimulator政策信息边界/实际执行成本与交易成本回归，小测试returns/volumes

## 拟交付与难度

在新资产/时间材料或明确合成市场上，交付滚动投资方案、成本后账本、风险归因、稳健性和可复算研究报告；不作真实投资建议。
- 交付：时点可用信息下的策略、逐期交易/现金台账、风险成本表和研究备忘录。
- 难度来源：优化目标中的预测成本与实际成交约束不同，流动性截断/rounding影响现金及后续持仓。
- 难度来源：训练窗口、交易成本和风险暴露共同影响样本外结论，需要时间一致性与压力情境核对。

## 验证与划分

- 正常基线：等权/持有/常规均值方差与原生单/多期优化；强参数搜索允许，简单策略必须参与。
- 首个探针：独立账本重现费用测试，再检查强原生策略是否已在新的信息/数据合同上达到目标。
- 停止条件：只需换目标权重/报告模板，或收益来自未来数据、少收成本、跨episode残留，则不成题。
- 独立评测：冻结独立执行账本核对现金/交易/费用和信息时点，再报成本后风险收益及压力指标；公开可校核指标评估报告，不凭文字印象。
- 生成与划分：需新的授权资产实体和按时点获取数据，或明确标签为合成市场；按实体与滚动时间拆分，测试CSV不作隐藏市场。
- 谱系/重叠：与旧Ken French金融题同族；仓库不同不等于新任务，必须改变研究问题、实体/数据谱系及评分，不能仅换ticker。
- 离线/计算：CPU Python/CVXPY和求解后端预置，无需联网券商；只取小测试CSV，完整市场数据许可/版本未确认。
- 许可观察：根GPL-3.0；外部市场数据及测试CSV底层来源权利另核，不沿用代码许可推断数据许可。

## 选读证据

- [cvxportfolio/simulator.py:260](https://github.com/cvxgrp/cvxportfolio/blob/351c782b9b8b395c1a5f886b77e0d55f1bc9396e/cvxportfolio/simulator.py#L260)：policy仅接收past returns/volumes与当前价格，执行还会因流动性/rounding调整交易并重新算现金。
- [cvxportfolio/tests/test_simulator.py:316](https://github.com/cvxgrp/cvxportfolio/blob/351c782b9b8b395c1a5f886b77e0d55f1bc9396e/cvxportfolio/tests/test_simulator.py#L316)：原生交易成本测试独立展开手续费/价差/冲击公式比较。
