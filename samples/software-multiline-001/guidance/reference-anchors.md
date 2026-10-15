# 参考可以低于满分：官方锚点与本批契约

核验日期2026-10-14。以下是公开题目定义/框架代码证据，不能推出所有题目的Oracle成绩。

- [FFmpeg题定义](https://huggingface.co/datasets/ByteDance-Seed/EdgeBench/blob/main/ffmpeg_swscale_reimplementation.json)：正确性失败奖励0；通过后原始奖励为加速比几何均值，1.0只表示参考C实现速度。配置的log_anchor把14.155映射到43分。该锚点是配置，不冒充本地复现实测。
- [score_rescale.py](https://github.com/ByteDance-Seed/EdgeBench/blob/main/sforge/harness/score_rescale.py)：piecewise_max/min分支将rank30锚到20、rank1锚到80，super_anchor锚到100；归一化截断到0–100。排名锚点之上还可优化，截断满分不是全局最优的证明。

本批原文 `/ws/users/wcgu/edgebench/dev/requirements/delivery-20261011/docx-extracted.txt` 第5.2节要求：普通Oracle证明奖励能达到声明上限；无法定义Oracle的开放题可标open-solution，并附可运行参考/分数表。第4节同时要求强解可达的真实成绩和参考在奖励曲线中的位置。两者并不意味着开放参考必须归一化为1。

制作性能题时，在score-spec中分开存正确性契约、原始指标及方向、公开B、实际R、归一化公式/常量、clip上界、强解可达证据和reference_mode。这里的字段是作者元数据，不擅自塞进Harbor不支持的schema。open-solution依然实际跑参考、NOP、部分解双入口和重复评分，控制程序须诚实支持非满分参考。

当前批次归一化分0–1；上述官方例子是0–100。只用来理解参考锚点，不导入另一套计分，不对已有轨迹做映射。普通Oracle不到它声明上限时补正确性/参考证据；真正开放目标则声明open-solution，不为了凑Oracle=1重设锚点。缺高分可行解仍如实标证据不足，不能以“开放”免除校准。

下载原文和SHA保存于 `/ws/users/wcgu/edgebench/dev/task/1013/_coordination/skill-materials-to-three-traces-20261014-r1/public-reference-anchor-sources/manifest.json`。
