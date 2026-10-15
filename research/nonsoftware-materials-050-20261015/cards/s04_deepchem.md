# S04_DEEPCHEM · DeepChem 分子性质与骨架切分

- 主来源：[deepchem/deepchem](https://github.com/deepchem/deepchem/tree/455d07f3e17e880a4d980b5b0365e4a02b417e14)。
- 固定版本：`455d07f3e17e880a4d980b5b0365e4a02b417e14`。
- 来源单元：Delaney溶解度小数据、加载合同、骨架切分实现与测试；用于可行性探针。
- 评估：`medium`；优先级 `hold_data`。

**拟题：结构外推条件下的溶解度预测与不确定性**
从有实验标签的训练分子出发预测留出结构族的溶解度，输出预测和区间；先用Delaney验证管线，正式高难任务需扩大到有许可且难度足够的实验集合。
交付：分子预处理与训练管线、预测/区间、结构分组误差与有效性审计。

**困难的因果来源**
- 不同骨架的分子仍可能高度相似；仅按骨架名切分不自动形成结构外推，需验证训练/测试结构距离。
- 实验噪声、分子规范化和长尾理化区域共同影响误差，复杂网络未必胜过指纹树模型。

基线：规范化RDKit分子＋ECFP随机森林/梯度树/核回归，校准残差区间；允许DeepChem现成模型作为竞争基线。
首轮探针：在本地小数据上比较随机、骨架和结构距离切分，用强指纹模型检查误差与不确定性是否仍有可改善空间。
淘汰/降档：若只能重跑公开Delaney教程，或无法取得额外合法数据/可靠外推测试，保留为入门样例，不认定长程难题。

独立评分：隐藏分子上RMSE/MAE、各结构距离分组误差、区间覆盖/宽度；独立检查SMILES规范化和训练测试重复，不用单一随机split得分。
生成与划分：先做去重与结构族隔离，再按结构距离/实验批次设计留出；公开小数据有污染风险，正式hidden需新合法测量来源，不能仅换seed。
独立性与谱系：新主来源，非旧OGB图数据；化学结构ML与OGB-mol题的底层数据谱系需额外核对。Delaney小数据只作探针，不另算正式数据家族。
离线/计算：已取6文件含小CSV，无大数据/模型；CPU指纹基线可优先探针，RDKit轮子及完整环境未装。新实验数据未取得。
许可观察：代码根LICENSE为MIT文本；Delaney CSV实验数据的原始权利/再分发条款未由代码许可闭合，正式打包前单独核对。

**实际选读证据**
- [已有按完整骨架组分配train/validation/test的实现](https://github.com/deepchem/deepchem/blob/455d07f3e17e880a4d980b5b0365e4a02b417e14/deepchem/splits/splitters.py#L1519-L1570)；本地 [选读 1519–1570 行](../sources/s04_deepchem/files/deepchem/splits/splitters.py)。
- [测试涵盖骨架数量守恒与无效SMILES处理](https://github.com/deepchem/deepchem/blob/455d07f3e17e880a4d980b5b0365e4a02b417e14/deepchem/splits/tests/test_scaffold_splitter.py#L9-L36)；本地 [选读 9–36 行](../sources/s04_deepchem/files/deepchem/splits/tests/test_scaffold_splitter.py)。
- [公开Delaney目标为实测log溶解度，默认ECFP和scaffold](https://github.com/deepchem/deepchem/blob/455d07f3e17e880a4d980b5b0365e4a02b417e14/deepchem/molnet/load_function/delaney_datasets.py#L10-L30)；本地 [选读 10–30 行](../sources/s04_deepchem/files/deepchem/molnet/load_function/delaney_datasets.py)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
