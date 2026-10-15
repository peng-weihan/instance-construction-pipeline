# RESTler 007 远端 Docker 冒烟验证

2026-10-14，首个软件类小样已在开发机完成双镜像构建与真实容器评分。最终运行状态为 `smoke_completed`。任务、参考实现和评分器沿用冻结的 007 版本，修复仅在我们自己的运行脚本中进行。

| 提交与检查集 | 分数 | valid | 具名检查 |
|---|---:|---|---:|
| 参考解 / 公开集 | 1.0 | true | 7/7 |
| 参考解 / 隐藏反馈集 | 1.0 | true | 36/36 |
| 参考解 / 隐藏审计集 | 1.0 | true | 7/7 |
| 原始 starter / 隐藏反馈集 | 0.0 | true | 0/36 |
| 空提交 / 隐藏反馈集 | 0.0 | false | 0/1 |

最终尝试耗时约 134 秒，包含缓存构建、沙箱预检查、参考提交生成和五组控制评分。这不是解题耗时，也不是模型表现。原始 starter 是不修改公开代码的对照；空目录是另一项输入契约反例，不以空目录替代 NOP。

## 实际环境与证据

- 远端目录：`/ws/users/raymone/edgebench/restler-007-smoke-20261014/run-001/results-004`。
- 平台：Linux x86_64；Docker Server 29.1.3。不是 ARM 运行证据。
- 完整归档及 1464 个任务文件校验通过。任务清单 SHA-256：`3fb71947a579b50ecfe4a51752c81ec81c705fd49fc6bb87257f4f88357415b2`。
- 实际运行脚本：[smoke_nested_sandbox.py](../../remote_smoke/restler-007/smoke_nested_sandbox.py)，SHA-256：`454cd228962209207f5b171f21df23101730c81a5da861a146d9cc069217c974`，已与远端脚本核对一致。
- 主要原始证据：[运行状态](attempt-004/run_status.json)、[公开评分](attempt-004/reference_public.json)、[隐藏反馈评分](attempt-004/reference_feedback.json)、[审计评分](attempt-004/reference_audit.json)、[starter](attempt-004/starter_feedback.json)、[空提交](attempt-004/empty_feedback.json)。实际镜像 ID 和配置保存在运行状态中。
- agent 和 verifier 运行都使用 `--network none`；仅构建阶段使用 host 网络下载公开依赖。
- 题目自带 runtime 的沙箱启动预检查通过：候选命名空间看不到 `/judge`，`CapEff=0`。这是一项预检查，不是完整隔离审计；非 root 身份等正式要求仍待适配。

## 三次失败尝试与修复

1. `attempt-001`：构建网络访问 Ubuntu HTTP 源超时。宿主机访问成功；改为构建阶段 host 网络后通过。没有改评分网络策略。
2. `attempt-002`：bubblewrap 用户映射失败。外层可信 verifier 容器原先只授予 SYS_ADMIN；补充 SETUID、SETGID、SETFCAP 后映射可启动。
3. `attempt-003`：Docker 默认系统路径限制阻止新 PID 命名空间挂载 `/proc`；增加 `systempaths=unconfined` 后真实 runtime 预检查通过。配置仅用于这次可信 verifier 容器，候选仍由 bubblewrap 隔离并移除 capabilities。未修改宿主系统策略或他人文件。

三次基础设施失败保留原日志，没有转换成题目零分。最终运行的原始报告也未回填或改写。

## 结论边界

这次证明了软件类首题的镜像可构建、参考提交可评分、当前检查集可达到满分、无修改代码对照得零分，并能返回结构化诊断。其他五类尚未完成远端容器验证。

当前是直接 Docker 辅助验证，未运行原生 Harbor Oracle/NOP；没有模型调用、没有六小时轨迹、没有证明持续涨分、没有完成五次同快照确定性或 ARM 验证。空提交 `valid=false` 仍是本地契约，后续需映射为远端 Harbor 要求的普通失败有效零分。正式六小时运行前还需适配 Harbor 0.23.0 的目录/schema、原生与周期奖励一致性、600 秒自动快照，以及官方 Codex adapter 的 Aliyun 入口。
