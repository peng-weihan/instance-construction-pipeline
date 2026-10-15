# S03_WILDS · WILDS iWildCam

- 主来源：[p-lambda/wilds](https://github.com/p-lambda/wilds/tree/472677590de351857197a9bf24958838c39c272b)。
- 固定版本：`472677590de351857197a9bf24958838c39c272b`。
- 来源单元：iWildCam 2.0元数据合同、相机位置/序列切分器和评分实现；图像未下载。
- 评估：`high`；优先级 `hold_data`。

**拟题：新相机位置上的长尾物种识别与校准**
在允许的图像和标签上训练模型，预测未见相机地点的物种，输出类别概率和按地点分析；可选使用无标签适应但须与纯监督合同分开。
交付：冻结推理入口、训练配置、类别概率、分组误差与校准结果。

**困难的因果来源**
- 背景、光照和设备与物种相关，普通ERM容易学习地点捷径，到了新地点失效。
- 稀有类和同一触发序列的近重复帧共同作用，随机图像切分会虚高得分且掩盖宏平均性能。

基线：预先离线打包且许可明确的常用视觉预训练模型＋ERM/重采样＋温度校准；不通过禁止预训练虚造难度。
首轮探针：先取得合法完整数据与地点/序列元数据，再跑固定强ERM及背景裁剪基线，量化留出地点宏F1和稳定方差。
淘汰/降档：数据链接、再分发许可或离线权重无法闭合时暂停；若轻量线性探针已过目标，下调范围，不凭图像量判断难度。

独立评分：按官方宏F1和准确率复现基础评分，另固定地点分组汇总与概率校准指标；标签仅在独立grader读取，提供开发反馈。
生成与划分：从真实数据按地点、序列和时间留出，近重复帧整组隔离；这是固定数据的评测任务，新训练/测试分布仍需合法数据支持，不声称合成图像已等价。
独立性与谱系：新主来源，区别旧单细胞跨站点预测；都属于分布泛化，不应把WILDS不同站点当多个独立来源。公开benchmark/模型污染需要审计。
离线/计算：已取5源码/许可文件，无图像和模型；源码标示压缩包11,957,420,032字节。完整训练可能需GPU，成本未测，不计下载时间为难度。
许可观察：代码MIT；数据类明确声明CDLA-Permissive-1.0，仍须跟实际下载版本和来源条款核对，不能用MIT覆盖图像。

**实际选读证据**
- [186类物种、相机位置域、数据许可和2.0下载体量均在类合同中](https://github.com/p-lambda/wilds/blob/472677590de351857197a9bf24958838c39c272b/wilds/datasets/iwildcam_dataset.py#L16-L45)；本地 [选读 16–45 行](../sources/s03_wilds/files/wilds/datasets/iwildcam_dataset.py)。
- [位置grouper与官方宏Recall/F1、准确率评测实现](https://github.com/p-lambda/wilds/blob/472677590de351857197a9bf24958838c39c272b/wilds/datasets/iwildcam_dataset.py#L103-L145)；本地 [选读 103–145 行](../sources/s03_wilds/files/wilds/datasets/iwildcam_dataset.py)。
- [按序列跨日一致性检查并写ID/OOD分割，不能随机打散图片](https://github.com/p-lambda/wilds/blob/472677590de351857197a9bf24958838c39c272b/dataset_preprocessing/iwildcam/create_split.py#L100-L138)；本地 [选读 100–138 行](../sources/s03_wilds/files/dataset_preprocessing/iwildcam/create_split.py)。

状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。
