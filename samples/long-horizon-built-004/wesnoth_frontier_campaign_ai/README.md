# wesnoth_frontier_campaign_ai

状态：构造源码齐备，未运行验证。阅读 [题面](instruction.md)、[评分契约](public/scoring_metadata.json)、[参考解说明](endpoint_notes.md) 和 [证据状态](evidence.json)。

- public/：agent 可见材料；solution/：作者参考解，不能放入 agent 环境。
- verifier/：可信评分控制器；private/：隐藏标签/参考资产。
- environment/agent 与 environment/verifier 是两个真实、独立的 Docker 构建上下文。agent 上下文不包含 private、verifier 或 solution。
- task.toml 是明确标注的本地契约；合同的 Harbor schema 尚未提供，未冒充正式兼容。

后续显式验证时构建：`docker build -t wesnoth_frontier_campaign_ai-agent environment/agent` 和 `docker build -t wesnoth_frontier_campaign_ai-judge environment/verifier`。构建会联网获取依赖，Lean 会构建库，排样会生成冻结参考布局；本轮没有执行这些命令。

agent 运行必须加 `--network none`。开始工作之前运行 `python tools/start_run.py --run-state run/state.json` 固定计时起点。提交 submission 目录的内容，例如 `python tools/submit.py --judge-image IMAGE_DIGEST --submission SNAPSHOT --run-state run/state.json --record run/curve.jsonl`。启动器冻结提交副本和实际 judge image ID，每次创建新的离线 judge。启动器明确为 bubblewrap 内层 worker 提供命名空间所需的容器权限，未提供 unsandboxed fallback。没有 Docker socket 挂载。

参考解入口：solution/policy.lua。参考解的输出/源码按相同提交契约交给 grader，不直接写分数。镜像构建过程将记录真实依赖版本；构建前不能声称已经取得这些版本的双架构可运行证据。
