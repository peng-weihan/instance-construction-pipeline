# 三个账号运行汇总

核验时间：2026-10-15 18:41:45 CST。范围为开发机进程和能够关联的云沙箱；数字是确认存活的会话/模型进程，包含等待或待清理状态，不代表每一刻都在发送模型请求。

| 账号 | 确认云端运行 | 确认原生 Codex（含 Docker） | 合计 | 共享登记 lease | 外部预留 |
|---|---:|---:|---:|---:|---:|
| raymone/1 | 4 | 5 | 9 | 6 | 4 |
| raymone/2 | 7 | 2 | 9 | 7 | 0 |
| raymone/3 | 5 | 2 | 7 | 9 | 1 |

## 1 号：确认 9 个

- 本会话六小时评测：科学/机器学习、金融重跑，共 2 条。
- 本会话软件出题：RESTler、uv，共 2 条。
- 其他批次云端：动态 PDP pilot、四足视觉 RL screen，共 2 条；路径在 `/ws/users/ytli/...`。
- 其他 TB2.1 作者：PyAV、SUNDIALS，共 2 条。
- SQLite TB2.1 Docker 内还有 1 个 Codex 进程；对应任务的 progress 已写 `stopped-platform-rejection`，因此不能说它是正常推进中的评测，需要该运行负责人核实。

## 2 号：确认 9 个

- 其他既有 EdgeBench 六小时评测：SharpFullChain ×1、Thorp routing chain ×2、MaxCutFull ×1、HardSphere ×2、PartitionFullChain ×1，共 7 条；均在 `/ws/users/wcgu/edgebench/dev/task/1013/...` 下。
- 其他 TB2.1 作者：HiGHS、ZODB，各 1 条。
- FontTools 原生作者已结束，因此之前的 10 个已降到 9 个。本次 16 个软件候选尚未使用 2 号。

## 3 号：确认 7 个，另有旧登记待核

- 本会话软件出题：WASM、Valkey，共 2 条。
- 其他既有 EdgeBench 六小时评测：Unique Games chain ×2、HardSphere ×1、BorsukFullChain ×1、BinFullChain ×1，共 5 条。
- 9 条 lease 中有 2 条对应的宿主 PID 已结束。PID 3038765 来自本会话此前的 Lean run-6h-002，其当前 learner ledger 标为 destroyed=true；PID 2855005 的具体运行尚未定位。因此不把这两个旧登记说成当前活跃，也不据此直接删除它们或断言所有云端资源都不存在。

## 归属与余量

当前活动表中，**本会话启动的六小时评测只有科学和金融两条**。本次软件候选运行的是作者 CLI，并非六小时解题。其他目录的运行是只读核对，未在本会话启动、接管或停止。账号被多个批次共用不能当成所有任务都由本会话发起。

每账号现有调度上限仍为 10。登记 lease、外部预留和现场观察是三种证据，不能把登记总数直接叫做实际运行数。1 号按当前登记加预留无新增名额；2 号按现场数字看尚有 1 个余量，但两条原生作者未纳入 canonical lease，调度器仍在保护性等待；3 号按登记加预留无新增名额。外部预留中的未匹配部分及旧登记是否可释放，尚未完成核实，不能当成实测繁忙。

[原始脱敏核对记录](reports/three-account-summary-20261015T104145Z.json) / [本批全部 16 个作者任务调度](ALL_POOL.md)。
