# 软件工程首批真实出题进程

**已启动两条 gpt-6.1-sol/high 原生 Codex 出题会话，第三条排队。** 本轮任务是构造题包，不是六小时教师解题运行。

- 实际开始：2026-10-15 17:48:33 CST。
- 本次核验：2026-10-15T17:49:47.104368+08:00。
- 指定 Codex home：`/ws/users/wcgu/new-codex-group/raymone/3`；实际调用其 `bin/codex`，CLI 0.160.0，显式指定 gpt-6.1-sol/high。
- 独立远端工作根：`/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1`。
- 1/2 号存在另一个 TB 批次的原生出题进程，先避开；3 号经真实 host/SDK/Docker 检查有两个名额。保留所有原有 lease 与 external reservation，只新增本批两个有身份的占用，未停止其他进程。

| 任务 | 状态 | 已完成工具项 | 成功命令 | 原生 PID |
|---|---|---:|---:|---:|
| 01_openapi_streaming | 出题中 | 8 | 7 | 764331 |
| 09_valkey_transactions | 排队 | 0 | 0 | — |
| 14_tree_sitter_incremental | 出题中 | 9 | 9 | 764332 |

OpenAPI 与 Tree-sitter 已经有真实模型驱动的命令完成记录；不仅是二进制版本或 PID 检查。它们正在读源码、选择具体合同/缺口和搭建任务；尚未完成题包或通过六小时难度校准。作者要求保存素材许可证/哈希、真实 starter、私有参考、独立评分、两个 informative near-miss 与材料/难度报告。

Valkey 在任一初始任务退出、其本批模型占用得到实际释放后，由常驻调度器重新做真实容量检查，再自动启动；检查失败会保留排队状态，不能绕过共享并发上限。没有按分数/难度停止模型的规则。作者与解题评测是两个阶段。

## 证据与后续读取

- [实际状态快照](reports/live-status.json) / [原生启动记录](reports/startup.json) / [具体启动计划](reports/launch-plan.json)。
- 原生会话的每条 JSONL 轨迹保存在远端各 `jobs/<id>/trajectory.jsonl`，题包目标在同目录的 `task/`，完成摘要目标为 `AUTHOR_RESULT.json`。鉴权不随本地证据或交付包复制。
- 本地 `launcher/` 保留本次实际使用的容量检查、进程监督、状态和提示词生成代码。构造者不能改共享原始文件、再启动模型/subagent/云沙箱或六小时求解。
- 刷新状态：用现有 SSH 连接执行远端 `python3 <工作根>/authoring/status.py`，只输出本批身份、工具计数和阶段，不输出账号凭据或完整命令结果。

本报告是上述时间点的核验结果；后续状态以远端进程及新增证据为准。
