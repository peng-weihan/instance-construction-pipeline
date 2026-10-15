# 首批两个软件工程题包草案

这两份是已实际构造并带作者本地检查证据的草案；容器/ARM/六小时难度验收尚未完成。

- [OpenAPI SDK 题面](01_openapi_streaming/task/instruction.md) / [材料](01_openapi_streaming/task/MATERIALS.md) / [作者结果](01_openapi_streaming/AUTHOR_RESULT.json)：参考五次 1.0，cheap 0.60；保留打磨。
- [Tree-sitter 题面](14_tree_sitter_incremental/task/instruction.md) / [材料](14_tree_sitter_incremental/task/MATERIALS.md) / [作者结果](14_tree_sitter_incremental/AUTHOR_RESULT.json)：starter 仅改全量重解析为 0.46861；使用参考完整 API 的重解析对照为 1.0（不可冒称独立廉价求解）。当前暂缓六小时标定，保留构造结果供审阅。

每份包含 environment、verifier、tests、solution、source/score/build 元数据及作者工具和原始本地检查证据。JSON 中的绝对远端路径保留作为实验来源，不能假装成本地重跑命令。模型身份和轨迹计数参见[执行报告](../../runs/software-authoring-016-20261015-r1/PROGRESS.md)。

原始压缩包已对照远端 SHA-256 验证；未复制账号鉴权。
