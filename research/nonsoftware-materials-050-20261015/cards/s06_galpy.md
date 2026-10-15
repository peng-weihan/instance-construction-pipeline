# S06_GALPY · galpy 潮汐星流动力学

- 主来源：[jobovy/galpy](https://github.com/jobovy/galpy/tree/9f11deffca05346bebafd4da0e77da2e6b7ec54d)。
- 固定版本：`9f11deffca05346bebafd4da0e77da2e6b7ec54d`。
- 来源单元：streamdf采样实现、银河势/轨道参考fixture和action-angle实现。
- 评估：`high`；优先级 `hold_reference`。

**拟题：不完整星流观测下的银河势约束与轨迹预测**
给定带选择效应、异方差误差和缺失径向速度的合成星流星表，联合约束低维银河势与祖先轨道，预测留出流段的天空位置/速度分布。
交付：推断程序、参数后验样本或置信域、留出星流预测与误差诊断。

**困难的因果来源**
- 银河势与祖先轨道/剥离时间存在退化；只拟合天空轨迹可能得到错误动力学，需要速度和展宽共同约束。
- action-angle近似、坐标/单位转换和观测选择会改变似然，完整六维真值拟合不代表缺失观测下可泛化。

基线：galpy现成正演＋有界多起点优化/采样，先固定若干nuisance参数；简单轨道拟合作为低成本竞争基线。
首轮探针：比较简单轨道、streamdf和独立轨道积分参考在可辨识参数子集上的预测与校准，测量生成/拟合成本。
淘汰/降档：若真值势无法由观测辨识、近似误差主导评分，或单轨道拟合已满足全部合理目标，缩小/重设任务而非扩大样本量。

独立评分：独立积分器检查留出轨迹/速度分布、预测似然和后验覆盖；按等价可辨识组合评分，不硬要求恢复退化单参数。
生成与划分：改变势族、轨道倾角、破坏时间、缺失/噪声和选择窗；按物理族而非仅seed划分，公开Bovy2014参数只作健康例。
独立性与谱系：新天体动力学来源；不将多个星流或旧fixture重新命名计多素材，需复核原EdgeBench天文拟合谱系。
离线/计算：已取7文件含两份README和license，无真实星表，无数值运行。CPU有限低维探针优先，精细streamdf/action-angle和C扩展成本未实测。
许可观察：根LICENSE为BSD-3-Clause条款；代码测试中的合成参数与外部Gaia等观测数据许可必须分开，本拟题先自建星表。

**实际选读证据**
- [采样频率本征方向、角度扰动和剥离时间后合成星流状态](https://github.com/jobovy/galpy/blob/9f11deffca05346bebafd4da0e77da2e6b7ec54d/galpy/df/streamdf.py#L3756-L3786)；本地 [选读 3756–3786 行](../sources/s06_galpy/files/galpy/df/streamdf.py)。
- [固定银河势、轨道、速度弥散和破坏时间的可复核合成fixture](https://github.com/jobovy/galpy/blob/9f11deffca05346bebafd4da0e77da2e6b7ec54d/tests/test_streamdf.py#L14-L65)；本地 [选读 14–65 行](../sources/s06_galpy/files/tests/test_streamdf.py)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
