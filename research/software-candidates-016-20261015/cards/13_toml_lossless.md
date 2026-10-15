# 13_toml_lossless：无损解析、span与结构化编辑的跨层恢复

优先级：**P1**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/toml-rs/toml/tree/ceac6e4412420d5a5c19e4f7293ad005cf1a31b2)；commit `ceac6e4412420d5a5c19e4f7293ad005cf1a31b2`。

许可观察：Apache-2.0 OR MIT；保留所有 crate 的许可及测试数据声明。

## 已有能力与拟出的题

toml-rs 已提供无损编辑和 span 数据；旧小样只去掉四个 helper，恢复范围太窄。新 profile 不能继续只按那四个函数的覆盖计分。

构造跨 tokenizer/parser、span/decor 与 toml_edit 结构修改链的受控缺失实现，恢复注释/空白/原始字符串保真、错误位置和连续编辑兼容。

原题类别参照：rust_multicrate_reconstruction / regex_automata_repair：跨 crate 语义恢复。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 多个实际 crate 的生产代码缺口及保留公开 API

- 改动要跨原始文本→span→结构→输出；不做任意删除文件导致无法起步的题

## 参考与迭代评分

固定完整参考版本在私有 verifier 编译；独立编辑操作脚本检查语义与不变片段，生成新组合/错误边界，避免仅逐字复用上游 tests。

拟评分维度：

- 合法/非法 TOML 语义

- span 和错误位置

- 注释/空白/字符串保真

- dotted key/implicit table/array-of-tables 编辑

- 连续编辑及 serde 回归

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 解析单文档后修补 implicit/dotted table 的编辑交互

- 处理多轮编辑、despan/ownership 与错误位置的一致性

最强廉价基线：检查 starter、vendor、文档和已安装 crate 中是否仍有可直接复制的原实现；再试薄封装现有 toml_edit。若正常可用依赖即可满分，重做缺口合同。

先做的否证探针：先做跨层依赖图与受控缺口清单，证明只恢复旧 helper 不足；用真实多轮编辑观察文本而非只查 AST。

构造风险：

- 原实现公开且可能被记忆，不能把源码恢复自动当成新训练能力

- 新缺口及 reference/starter 差分尚未实施

- 原本狭窄的 35 case 满分不等于新合同可达

## 实际取得的源码证据

- [文本所有权与 span 的联系](https://github.com/toml-rs/toml/blob/ceac6e4412420d5a5c19e4f7293ad005cf1a31b2/crates/toml_edit/src/document.rs#L45)；本地 [`sources/13_toml_lossless/files/crates/toml_edit/src/document.rs:45`](../sources/13_toml_lossless/files/crates/toml_edit/src/document.rs)。

- [隐式 table 行为](https://github.com/toml-rs/toml/blob/ceac6e4412420d5a5c19e4f7293ad005cf1a31b2/crates/toml_edit/src/table.rs#L17)；本地 [`sources/13_toml_lossless/files/crates/toml_edit/src/table.rs:17`](../sources/13_toml_lossless/files/crates/toml_edit/src/table.rs)。

- [真实文本与连续编辑素材](https://github.com/toml-rs/toml/blob/ceac6e4412420d5a5c19e4f7293ad005cf1a31b2/crates/toml_edit/tests/testsuite/edit.rs#L62)；本地 [`sources/13_toml_lossless/files/crates/toml_edit/tests/testsuite/edit.rs:62`](../sources/13_toml_lossless/files/crates/toml_edit/tests/testsuite/edit.rs)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/13_toml_lossless/manifest.json)。[完整 Git 文件树索引](../sources/13_toml_lossless/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

旧 profile：samples/software-multiline-001/05_toml；旧本地参考 1 分，尚无新跨层任务实现。

