# 14_tree_sitter_incremental：增量解析、错误恢复和节点位置一致性

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/tree-sitter/tree-sitter/tree/8ca548849fc8dbefd699edcec26546bb14112820)；commit `8ca548849fc8dbefd699edcec26546bb14112820`。

许可观察：MIT；使用的各语言 grammar 是独立仓库，必须另固定 commit/许可。

## 已有能力与拟出的题

Tree-sitter 已有完整增量 parser、tree_edit、changed_ranges 与 Rust binding；受控缺口尚待构造，不声称发现上游缺陷。

恢复 Tree-sitter 在编辑后重用旧树、修正节点范围及错误恢复的关联实现，保留 API 和确定的 grammar，验证连续多次编辑后的解析一致性。

原题类别参照：regex_automata_repair / rust_multicrate_reconstruction：核心状态与跨层恢复。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- lib/src/parser.c、tree.c 和必要 stack/绑定路径

- 提供能初始完整 parse 的 starter，再逐步恢复增量路径，避免完全无法解析的死起点

## 参考与迭代评分

固定未改动版本作差分参考；每次编辑额外从头完整 parse，独立核对语法树、byte/point 与不变量。语法树一致不代表 changed_ranges 已正确，需单独检查。

拟评分维度：

- 初始 parse 保留

- 单次/多轮 edit

- UTF-8/UTF-16 与 byte/point

- changed_ranges 合同

- 错误恢复与节点生命周期

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 普通插删之后处理多字节位置、跨节点 edit 与旧树复用

- 处理错误节点、连续编辑及 external scanner 状态恢复

最强廉价基线：每次从头 parse 可以轻易通过只查最终 AST 的 grader；先实现此基线，检查 changed-range/API 与合理工作量指标是否仍有真实缺口。

先做的否证探针：用整树重解析 baseline 对照多轮 edit 与 changed_ranges；先冻结 grammar 及其真实生成文件，不靠代码行数推断难度。

构造风险：

- 性能计分若需要时间端点必须另实测，不能用树大小伪造速度

- grammar 尚未完整冻结下载

- 公开 core 源码可能被直接复原，需跨状态组合而非单补函数

## 实际取得的源码证据

- [公开编辑入口](https://github.com/tree-sitter/tree-sitter/blob/8ca548849fc8dbefd699edcec26546bb14112820/lib/src/tree.c#L97)；本地 [`sources/14_tree_sitter_incremental/files/lib/src/tree.c:97`](../sources/14_tree_sitter_incremental/files/lib/src/tree.c)。

- [changed range 计算](https://github.com/tree-sitter/tree-sitter/blob/8ca548849fc8dbefd699edcec26546bb14112820/lib/src/tree.c#L114)；本地 [`sources/14_tree_sitter_incremental/files/lib/src/tree.c:114`](../sources/14_tree_sitter_incremental/files/lib/src/tree.c)。

- [实际编辑回归素材](https://github.com/tree-sitter/tree-sitter/blob/8ca548849fc8dbefd699edcec26546bb14112820/crates/cli/src/tests/parser_test.rs#L461)；本地 [`sources/14_tree_sitter_incremental/files/crates/cli/src/tests/parser_test.rs:461`](../sources/14_tree_sitter_incremental/files/crates/cli/src/tests/parser_test.rs)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/14_tree_sitter_incremental/manifest.json)。[完整 Git 文件树索引](../sources/14_tree_sitter_incremental/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

