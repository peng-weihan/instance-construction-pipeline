# S09_SURVIVAL · scikit-survival 删失数据评测

- 主来源：[sebp/scikit-survival](https://github.com/sebp/scikit-survival/tree/ca0c2bd6ed19334d9cb357e309c38d730cac8cdc)。
- 固定版本：`ca0c2bd6ed19334d9cb357e309c38d730cac8cdc`。
- 来源单元：IPCW Brier评测实现、数值回归测试、BMT小fixture及数据接口。
- 评估：`medium`；优先级 `hold_baseline`。

**拟题：删失机制变化下的生存曲线预测与校准**
在模拟多中心带删失结局的训练队列上训练，预测留出中心/时间段的个体生存曲线与置信区间，处理非比例风险和校准变化。
交付：固定时间网格上的生存概率、训练/校准入口和分中心评测记录；不交付临床建议。

**困难的因果来源**
- 删失使真实结局部分不可见，直接当普通回归/分类会产生系统偏差，评测时间窗和删失支持范围必须一致。
- 风险排序好不保证概率校准；中心变化与非比例风险要求比较生存曲线而非只优化C-index。

基线：Kaplan-Meier、CoxPH/惩罚Cox、随机生存森林和合理校准；合成任务允许直接正确设定的参数生存模型竞争。
首轮探针：先用已知生成分布检查IPCW评分与真实完整结局评分一致性，再跑Cox/森林；仅在可识别、独立删失条件下设置主分。
淘汰/降档：若拟题要求从无额外假设的数据恢复信息性删失的不可识别真分布，停止；若正确参数模型很快满分，降低任务难度定位。

独立评分：主用生成器隐藏完整事件时间和真生存函数计算曲线误差/适当评分，观测数据IPCW-IBS与C-index为诊断；固定支持内时间窗并检查单调/概率界。
生成与划分：自建非比例风险、协变量和删失机制组合，按中心/机制划分；训练只给观测时间/事件标记，完整结局和生成参数隔离；不把公开BMT分割作hidden。
独立性与谱系：新主来源，研究产物是统计预测；医疗专业知识组若使用临床证据须区别任务目标。多个模拟队列不另算新来源。
离线/计算：已取6文件含小BMT fixture；未取真实临床大数据。拟CPU模拟队列，Cython/scikit-learn构建依赖未安装，不声称实际可运行。
许可观察：根COPYING为GPL-3.0文本；BMT fixture原始数据来源条款须另核对，当前只作格式/规格证据，正式样题优先自建模拟数据。

**实际选读证据**
- [IPCW由训练删失分布估计，并按case/control与时间点计算Brier误差](https://github.com/sebp/scikit-survival/blob/ca0c2bd6ed19334d9cb357e309c38d730cac8cdc/sksurv/metrics.py#L654-L680)；本地 [选读 654–680 行](../sources/s09_survival/files/sksurv/metrics.py)。
- [数值期望值与反序时间点等评测回归用例](https://github.com/sebp/scikit-survival/blob/ca0c2bd6ed19334d9cb357e309c38d730cac8cdc/tests/test_metrics.py#L1017-L1043)；本地 [选读 1017–1043 行](../sources/s09_survival/files/tests/test_metrics.py)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
