归一化公式和常量在 public/scoring_metadata.json。整批统一区分“参考算法”和“理论上界”：上界 1 是公式边界，不是已知可达分数。参考实现位于 solution；没有填写任何未运行的 oracle/nop/model 分数。排样的参考布局将在构建 judge 时生成并冻结；其余参考程序随源码交付。实际端点与难度须在后续验证阶段测量。

当前试跑版本已固定全部 27 个实测参考布局、输入哈希和证书哈希。构建时执行 verify_frozen_reference.py，不再重算归一化锚点。参考源码得分仍以 controls 实测报告为准。
