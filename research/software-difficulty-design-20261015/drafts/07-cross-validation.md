# 综合核对记录

三份分析草稿和 36 题表完成后进行合并。分析采用指定任务材料与关键实现的定向阅读；各草稿记录实际范围，未套用完整上游仓库的覆盖率声明。

- 主分析独立重算 36 题索引与卡片 ID 集合：36/36，缺失、额外、重复均 0；主类数量 13/12/6/3/2；公开 JSON 数量 12。
- 原题抽查：实际 Schemathesis TODO 第 15 行的 independent improvements 及 19–26 行八目标；论文 HTML 的 Arc、CPU full flow、Zstd、cfzip 设计说明。
- 候选抽查：OpenAPI cheap.py 第 1–27 行实际使用 HTTPX 行迭代；Tree-sitter controls.py 第 3–15 行从完整上游复制 API 再添加 old_tree=NULL。综合报告未把参考派生消融称为独立快速求解。
- 新方案核对：SDK cursor 重放和 GET/POST 边界、EdgeKV checkpoint 切点和故障模型、DataFusion 未测性能锚点均保留明确合同和状态。
- 综合报告不要求所有任务都大 LOC、强耦合或禁依赖；保留 roadmap 独立目标和单文件性能题反例。
- 检查新增目录全部 Markdown 本地链接，无缺失目标；修正论文 G.4 锚点为 A7.SS4。来源摘要与机器覆盖结果在 ../validation.json。

没有执行新候选、构建、容器、付费模型或性能测量。题包草案、作者参考、独立基线和长程难度证据在报告中分别表述。
