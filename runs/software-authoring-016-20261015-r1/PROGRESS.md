# 首批出题进展（2026-10-15）

**两个实际题包草案完成并已取回本地；Valkey 已恢复启动。** 当前通过六小时难度验收的新增题数仍为 0。模型均为用户指定路径的 gpt-6.1-sol/high；这是作者运行，不是六小时教师轨迹。

| 路线 | 实际构造进程 | 本地证据 | 当前判断 |
|---|---|---|---|
| OpenAPI SDK | 17:48:33–18:19:11 CST，正常退出 | reference 五次 1.0；NOP 0.03；cheap 0.60；no-auth 0.84；eager 0.59924 | 草案完成；存在早满风险、同进程观测加固和单 schema 泛化缺口，保留打磨 |
| Tree-sitter | 17:48:33–18:09:42 CST，正常退出 | reference 1.0；NOP 0.14091；starter 只改 full-reparse 为 0.46861；参考版完整 API + full-reparse 为 1.0 | 草案完成；暂缓六小时标定；1.0 对照使用了 gold API，不能当成独立廉价求解证据 |
| Valkey | 18:28:27 CST 已实际启动 | 10 次工具完成，10 次成功命令，进程存活 | 出题中，还没有最终题包结果 |

上述分值来自作者运行留下的原始 score/命令记录；本次父进程核对了 grader/score-spec 哈希及文件存在性，未重新执行评分。两题都已有题面、真实 starter、私有参考、grader、solution、双环境构建源码、许可与 provenance/score/build 元数据；它们的 Docker/Harbor/ARM/六小时成长曲线均未在本批验证。

## 本地实际产物

- [两个题包入口](../../samples/software-authored-016-r1/README.md)。
- [OpenAPI 题面](../../samples/software-authored-016-r1/01_openapi_streaming/task/instruction.md) / [作者检查报告](../../samples/software-authored-016-r1/01_openapi_streaming/task/AUTHORING_REPORT.json)。
- [Tree-sitter 题面](../../samples/software-authored-016-r1/14_tree_sitter_incremental/task/instruction.md) / [作者检查报告](../../samples/software-authored-016-r1/14_tree_sitter_incremental/task/AUTHORING_REPORT.json)。
- [父进程产物/原始分值核对与判断](reports/parent-first-two-evidence-review.json)。
- [最新实时状态快照](reports/live-status.json) / [原始启动与恢复记录](reports/startup.json)。

下载压缩包 154,776,841 字节，SHA-256 `528f88d89f1427abf255a93ec099ebebcba5068a0340ff3dd40fffa3a2eecfaf` 与远端一致；本地关键 grader 和 score-spec 亦与原始分值记录绑定。没有复制账号鉴权。

## 队列恢复

自动接续在 18:09 的容量复核处停下；检查器把外部原生 Codex 的 code-mode 工具子进程额外计成一个模型会话。已在本批自有检查器内按真实父子关系与 start_ticks 归并，仍逐一计数实际 native 模型会话，保留原有外部占用。重新真实审计后于 18:28 启动 Valkey；未停止其他批次、未清理他人 lease、未放宽 10 并发上限。

Valkey 仍在远端个人目录 `/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1/jobs/09_valkey_transactions` 工作。当前快照时间：2026-10-15T10:29:19.850203+00:00；后续状态以该目录 status 与 trajectory 为准。

## 对照来源补充核对

`14_tree_sitter_incremental/author-tools/controls.py:3-10` 显示：`full_reparse_complete_apis` 从完整参考源码构造，再忽略 old_tree；`full_reparse_starter` 才从公开 starter 构造。前者 1.0 只证明正确 API 不需要高效复用也可满足当前合同，不能证明公开信息下修复其余 API 很快。starter 基线实测 0.4686147。已修正初步父进程判断，保留作者原始记录不改。

16 是候选总数；首批累计 3 条作者运行，历史最大并发为 2。OpenAPI 和 Tree-sitter 已结束，Valkey 接续；剩余 13 条未启动。
