# 当前远端启动材料：007

本目录提供冻结题包、校验与启动脚本。用途是直接 Docker 冒烟验证，未接入原生 Harbor，未调用模型，不产生六小时轨迹。

传输 `launch.py` 与 `restler-007-smoke.tar.gz` 到自己的远端目录后执行：

```bash
cd /ws/users/raymone/edgebench/restler-007-smoke-20261014
nohup python3 launch.py --archive restler-007-smoke.tar.gz --run-root /ws/users/raymone/edgebench/restler-007-smoke-20261014/run-001 > launch-001.log 2>&1 < /dev/null &
```

`run-001` 必须不存在。启动器验证归档 SHA-256、文件清单、逐文件大小与摘要后才启动构建。日志在 `launch-001.log` 和 `run-001/results/`，实时状态为 `run-001/results/run_status.json`。

控制包括参考解的公开/反馈/审计三组评分、原始 starter 和空提交。运行阶段禁网；构建阶段需要公开依赖源。只使用自己的目录和唯一命名容器，不挂载模型账号或 Docker socket。

需要人工检查全部逐项评分。当前 smoke_completed 只表示参考反馈正分与空提交被拒绝，不表示参考满分或验收通过。当前空提交 valid=false 的语义仍需按远端 Harbor 契约调整；starter 是真正无修改代码对照，不能用空目录替代。

2026-10-14 最新状态：已重新建立专用复用 SSH 连接，远端确认 SSH 客户端出口为 `134.195.101.72`。完整冻结归档已上传，归档及 1464 个文件摘要全部通过，`run-001` 已进入镜像构建阶段。上次不完整的 overlay 未用于本次执行。尚无评分或模型轨迹结果。

最终结果：`run-001/results-004` 已完成。实际脚本为 `smoke_nested_sandbox.py --build-network host`，包括实际 runtime 沙箱预检查与外层 verifier 所需的用户映射/系统路径配置。参考解公开/反馈/审计均 1.0，starter 0.0，空提交被拒绝。原 `launch.py` 留作第一轮启动证据，直接重用会遇到已记录的环境配置问题。完整证据见 `../../runs/remote-smoke-restler-007/REPORT.md`。
