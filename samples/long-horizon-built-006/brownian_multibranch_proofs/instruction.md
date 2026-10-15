# 布朗运动多分支形式化证明

在固定 Lean/BrownianMotion 工程中补全 targets.json 的 31 个证明，目标预算 6 小时。五个文件覆盖协方差、覆盖数、高斯矩、过程性质和连续修正。允许从任一分支开始，未完成目标保留 sorry。

只修改 BEGIN TASK PROOF / END TASK PROOF 注释之间的证明体，允许在证明内使用 have/let 等辅助构造；其余文件内容、类型签名、定义、import、依赖版本严格冻结。提交目录根含 targets.json 中的五个相对路径，无需提交依赖库。

不能加入 axiom/unsafe/opaque、运行 IO 的命令、宏/elaborator、run_tac 或关闭检查的选项。评分器重新构建固定项目，按目标实际声明的传递公理闭包计分，只允许 propext、Classical.choice、Quot.sound；sorryAx 不得计分。编译失败会反馈错误摘要。

组权重：协方差 .20，覆盖数 .20，高斯矩与过程性质合计 .20，连续修正 .40；每组内按完整证明目标比例给分。参考原证明仅在作者 solution 中，不在 agent 镜像。
