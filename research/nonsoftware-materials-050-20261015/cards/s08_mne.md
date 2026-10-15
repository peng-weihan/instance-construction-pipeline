# S08_MNE · MNE-Python 电磁源定位

- 主来源：[mne-tools/mne-python](https://github.com/mne-tools/mne-python/tree/7ab5922ca55db650e1c2f91315ecf46b623c8132)。
- 固定版本：`7ab5922ca55db650e1c2f91315ecf46b623c8132`。
- 来源单元：最小范数核构造、逆解API与定位偏差测试；不用外部人类受试数据。
- 评估：`high`；优先级 `scope_probe`。

**拟题：头模型与噪声失配下的神经源重建**
在合成球头/有限源空间中，从受噪声、坏道与轻度头模型失配影响的EEG/MEG观测重建活动源，输出位置、时间波形与置信区域。
交付：离线逆解程序、源活动时间序列、位置/区域置信结果和留出观测预测。

**困难的因果来源**
- 源数远大于传感器数且源可能相关，常规最小范数易泄漏和深度偏差；不能只看传感器残差。
- 导联几何/噪声协方差失配改变逆核，调好单一头模型参数不保证跨坏道和噪声机制稳定。

基线：现成MNE、dSPM、sLORETA、eLORETA和稀疏/beamformer；允许标准MNE调用，不把库API使用当主要工作。
首轮探针：先固定小球头生成器、独立前向矩阵和强逆解超参搜索，测定位/波形误差与可恢复性，比较是否仍有合理改进目标。
淘汰/降档：如果仅同一导联矩阵单源无噪声，现成eLORETA已完成全部目标，或源组合不可辨识却强判唯一位置，重设范围。

独立评分：在可分辨源集合上评位置距离、源/波形匹配误差和不确定度覆盖；另评留出传感器重投影与虚假源控制，允许等价源表示。
生成与划分：生成不同源深度、相关性、SNR、传感器坏道和头模型扰动；按扰动机制/空间区域划分，隐藏真实源；不只更换随机噪声seed。
独立性与谱系：新神经物理来源，区别旧单细胞数据；潜在与脑科学现成inverse样例重合需按生成器/测量/评分查重。合成球头与真实临床能力不等价。
离线/计算：已取5文件含源模拟器，无Freesurfer/MRI、人类数据或外部样本包；拟先CPU小球头，完整环境/参考前向精度未验证。
许可观察：代码根LICENSE.txt为BSD-3-Clause；外部MNE testing/sample数据另有许可，当前未下载，正式题先使用自建合成数据。

**实际选读证据**
- [逆核会按噪声归一化、标签和源方向重排/旋转，源表示影响输出](https://github.com/mne-tools/mne-python/blob/7ab5922ca55db650e1c2f91315ecf46b623c8132/mne/minimum_norm/inverse.py#L821-L871)；本地 [选读 821–871 行](../sources/s08_mne/files/mne/minimum_norm/inverse.py)。
- [现成测试直接量化定位偏差，并显示标准eLORETA等已有很强合成表现](https://github.com/mne-tools/mne-python/blob/7ab5922ca55db650e1c2f91315ecf46b623c8132/mne/minimum_norm/tests/test_inverse.py#L418-L460)；本地 [选读 418–460 行](../sources/s08_mne/files/mne/minimum_norm/tests/test_inverse.py)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
