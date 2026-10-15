# 07_arrow_ipc：嵌套类型和字典演化的IPC读写器

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/apache/arrow/tree/ca5564e007a209e251b9d4648af4bc6a53c68c4f)；commit `ca5564e007a209e251b9d4648af4bc6a53c68c4f`。

许可观察：Apache-2.0，保留 NOTICE；独立互通数据仓库另固定许可。

## 已有能力与拟出的题

Arrow 本身已有这些格式能力与跨语言 integration runner。必须选择合适的轻量 starter 或新增 API，不能在完整 Arrow 上要求再实现原样 reader。

实现可被嵌入的增量 Arrow IPC 读写器，处理分段输入、嵌套 nullable 类型、dictionary delta/replacement、多 record batch 与损坏流，输出明确消费进度和诊断。

原题类别参照：stream_processing_engine / 自建数据系统：格式与状态交互。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 进程内增量 API 加独立 CLI

- 公开明确 stream/file 的不同字典规则、支持类型和内存合同

## 参考与迭代评分

固定独立语言的 Arrow producer/consumer 做互通，辅以手工最小消息和变形测试；不能 candidate 写什么再用自己读回就算正确。

拟评分维度：

- Schema/RecordBatch 及 nested/null 布局

- dictionary 生命周期

- 分块/截断输入

- stream/file 互通

- 内存与诊断合同

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 标量 reader 之后解决嵌套 offsets、validity 与共享字典

- 完善 delta/replacement、截断恢复及真正增量消费

最强廉价基线：直接用 pyarrow/Arrow Rust 的正常 wrapper 是必须先测的强基线；若 API 与资源合同没有实际差异，这条路线应淘汰。

先做的否证探针：冻结公开 API 后，用一个现成 Arrow binding 实现最薄版本；只有出现合理合同下的真实缺口才构造。

构造风险：

- 成熟库包装即满分的风险非常高

- 尚未取得 arrow-testing 的完整固定数据包，只取得格式/runner 依据

- 增加类型数量不能替代长程证据

## 实际取得的源码证据

- [字典消息与 delta 字段](https://github.com/apache/arrow/blob/ca5564e007a209e251b9d4648af4bc6a53c68c4f/format/Message.fbs#L129)；本地 [`sources/07_arrow_ipc/files/format/Message.fbs:129`](../sources/07_arrow_ipc/files/format/Message.fbs)。

- [正式格式依据](https://github.com/apache/arrow/blob/ca5564e007a209e251b9d4648af4bc6a53c68c4f/docs/source/format/Columnar.rst#L1215)；本地 [`sources/07_arrow_ipc/files/docs/source/format/Columnar.rst:1215`](../sources/07_arrow_ipc/files/docs/source/format/Columnar.rst)。

- [跨语言互通 runner](https://github.com/apache/arrow/blob/ca5564e007a209e251b9d4648af4bc6a53c68c4f/dev/archery/archery/integration/runner.py#L84)；本地 [`sources/07_arrow_ipc/files/dev/archery/archery/integration/runner.py:84`](../sources/07_arrow_ipc/files/dev/archery/archery/integration/runner.py)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/07_arrow_ipc/manifest.json)。[完整 Git 文件树索引](../sources/07_arrow_ipc/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

