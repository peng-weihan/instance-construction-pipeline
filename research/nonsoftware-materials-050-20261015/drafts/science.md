# 科学与机器学习：10份新素材

完成的是定向来源研究与构题假设，没有构造正式题包、运行候选或测定长程难度。10个独立主仓库均固定SHA，实际阅读范围如下；未做全仓审计。

| ID | 具体科学交付 | 潜力 | 下一步 |
|---|---|---|---|
| [s01_deepxde](../cards/s01_deepxde.md) | 稀疏含噪观测下的源场反演与新边界预测 | medium | hold_baseline |
| [s02_darts](../cards/s02_darts.md) | 跨层级分布变化下的概率预测与一致性 | medium | hold_baseline |
| [s03_wilds](../cards/s03_wilds.md) | 新相机位置上的长尾物种识别与校准 | high | hold_data |
| [s04_deepchem](../cards/s04_deepchem.md) | 结构外推条件下的溶解度预测与不确定性 | medium | hold_data |
| [s05_pybamm](../cards/s05_pybamm.md) | 多工况电池参数识别与留出负载预测 | high | hold_reference |
| [s06_galpy](../cards/s06_galpy.md) | 不完整星流观测下的银河势约束与轨迹预测 | high | hold_reference |
| [s07_eht](../cards/s07_eht.md) | 稀疏干涉观测与校准误差下的形态重建 | high | scope_probe |
| [s08_mne](../cards/s08_mne.md) | 头模型与噪声失配下的神经源重建 | high | scope_probe |
| [s09_survival](../cards/s09_survival.md) | 删失机制变化下的生存曲线预测与校准 | medium | hold_baseline |
| [s10_abtem](../cards/s10_abtem.md) | 多焦面显微图像中的结构与仪器参数反演 | high | hold_reference |

优先小探针：EHT稀疏干涉成像、MNE噪声/头模型失配下源定位。三项反演需先闭合参考与可辨识性：电池、银河势、电子显微。DeepXDE、Darts和生存预测先看简单合法基线；WILDS与DeepChem先看合法数据与隐藏划分。

需要正视的现成功能：DeepXDE公开例给出sin真解；Darts已有MinT；EHT已有闭合量多阶段成像；MNE标准逆解在干净合成条件下已有强表现。因此不能以“实现这些功能”作为新任务剩余工作。

数据与谱系：未使用旧MODFLOW/Harmonica/OGB/NeurIPS2021单细胞来源。独立仓库不等于已证明独立任务家族；原EdgeBench同领域谱系仍需构题时逐项核对。公开小fixture只作探针/规格，不作新hidden的充分依据。

## 真实选读范围

- **s01_deepxde**：`examples/pinn_inverse/elliptic_inverse_field.py` 7–45行（implementation）；`docs/demos/pinn_inverse/elliptic.inverse.field.rst` 7–17行（specification）。
- **s02_darts**：`darts/dataprocessing/transformers/reconciliation.py` 160–217行（implementation）；`darts/tests/dataprocessing/transformers/test_reconciliation.py` 107–136行（test）。
- **s03_wilds**：`wilds/datasets/iwildcam_dataset.py` 16–45行（specification）；`wilds/datasets/iwildcam_dataset.py` 103–145行（implementation）；`dataset_preprocessing/iwildcam/create_split.py` 100–138行（split_specification）。
- **s04_deepchem**：`deepchem/splits/splitters.py` 1519–1570行（implementation）；`deepchem/splits/tests/test_scaffold_splitter.py` 9–36行（test）；`deepchem/molnet/load_function/delaney_datasets.py` 10–30行（specification）。
- **s05_pybamm**：`packages/pybamm/src/pybamm/simulation/simulation.py` 529–557行（implementation）；`packages/pybamm/tests/unit/test_simulation.py` 13–42行（test）；`examples/scripts/SPMe.py` 11–32行（specification）。
- **s06_galpy**：`galpy/df/streamdf.py` 3756–3786行（implementation）；`tests/test_streamdf.py` 14–65行（test）。
- **s07_eht**：`ehtim/imaging/imager_utils.py` 513–543行（implementation）；`examples/example_im_closure.py` 58–80行（specification）；`tests/test_gradients.py` 44–71行（test）。
- **s08_mne**：`mne/minimum_norm/inverse.py` 821–871行（implementation）；`mne/minimum_norm/tests/test_inverse.py` 418–460行（test）。
- **s09_survival**：`sksurv/metrics.py` 654–680行（implementation）；`tests/test_metrics.py` 1017–1043行（test）。
- **s10_abtem**：`abtem/multislice.py` 425–491行（implementation）；`test/test_transmission_function_multislice.py` 16–58行（test）。

静态核验：10项、10个独立主仓库、55份定向源文件、24个选读证据区间；SHA/哈希/行范围错误 0。这不构成运行、评分器或难度验收。

许可已分别查看根许可；外部图像/实验/星表/临床数据不能自动沿用代码许可。除Delaney/BMT小fixture外未下载完整科学数据集；未取模型权重。
