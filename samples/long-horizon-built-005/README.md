# 六类长程任务小样：构造版 005

2026-10-14。六题均已打包真实起始素材、题面、参考实现源码、评分器源码、机器可读评分元数据，以及 agent/verifier 两个独立构建上下文。状态为 **构造源码齐备，待运行验证**。目标交互预算为 6 小时；未采集这六题的模型轨迹，未测 oracle/nop 分数，未证明六小时增长。

| 类别与题面 | 已取得的素材及任务规模 | 实际构造内容 | 长程潜力的关键待证项 |
|---|---|---|---|
| [软件：RESTler 可恢复执行](restler_resilient_execution/instruction.md) | 固定 RESTler 仓库；七组跨模块需求；公开/反馈/审计检查 7/36/7 项 | 重试、截止时间、异步、资源租约、诊断与回放参考实现；外侧控制器检查真实调用 | 组合故障能否拉开分数，基础接口是否过快饱和 |
| [科学：分层污染源反演](layered_aquifer_source_lab/instruction.md) | MODFLOW 示例作为背景；原创场景及合成观测 96/96/180 条；十个参数 | 独立前向程序、读取公开观测的反演参考、隐藏预测评分 | 可辨识性、数值一致性、多轮反演的改进空间 |
| [优化：工业异形排样](industrial_nesting_improvement/instruction.md) | PackingSolver 与九份设计；八来源族、27 个订单 | 固定求解预算、独立含孔多边形检查、构建期冻结参考布局 | 基线是否有足够优化余量；当前参考是上游基线，并非强 oracle |
| [数学：布朗运动证明](brownian_multibranch_proofs/instruction.md) | BrownianMotion 工程；五文件、31 个目标及原证明体 | 证明体编辑边界、原证明参考、编译及传递公理检查 | 实际依赖瓶颈、现成定理捷径、原题逐定理去重 |
| [专业工作：跨资产配置](cross_asset_adaptive_allocator/instruction.md) | 八资产历史缓存；训练/开发/反馈/审计 2414/1006/756/752 行 | 因果策略接口、可信账本、成本/约束核验、优化参考策略 | 稳定优于固定配置的空间、隐藏反馈过拟合 |
| [游戏：Wesnoth 策略](wesnoth_frontier_campaign_ai/instruction.md) | 固定 1.18.0 引擎素材；九张原创地图；反馈 12 局、审计 36 局 | 可信合法动作包装器、纯 Lua 策略接口、参考策略与逐局评分 | 场景可玩性、默认 AI 饱和、40 秒单局预算是否合理 |

这些题与原 EdgeBench 保留相似的工作机制，并更换工程、需求、输入或场景。当前不能称为已证实的统计同分布任务，也没有训练效果证据。素材仓库版本与摘要在各题 `source_provenance.json` 中；该文件保留候选阶段记录，当前实现状态以 `evidence.json` 为准。金融价格和工业设计数据的训练再分发权利仍待确认。

## 005 的修复与素材复核

- 游戏：修正 `chance_to_be_hit`。固定引擎的 `defense_on` 表示闪避百分比，被击中概率应为 `100-defense_on`。依据为本地固定版本的 `data/lua/core/units.lua`。新增公开策略协议，说明动作索引每次更新、优先级不保证执行，以及 `checked_move_full` 会结束移动。
- 科学：公开补全网格原点、层边界、显式 Euler、源项时间中点、半开释放区间和分数体积约定；不公开隐藏源参数或完整前向求解器。
- 金融：补全 `user_state` 的传递/保留语义、首次全现金状态、日期和历史窗口边界；起始代码说明加入必填 `rebalance`；评分器立即拒绝初始化失败。
- 六类均完成固定来源 commit、登记关键文件 SHA256 和公开契约文件存在性核对，结果见 [素材与构造复核](AUTHORING_REVIEW.md) 和 [机器可读证据](authoring_review.json)。报告也记录相近原题、不同之处、候选准入规则、预期改进层次和待运行反例。通过范围限于来源和文件检查，不代表语义去重或难度通过。

## 已有构造内容

- 参考解包含实际实现；评分器接收提交产物并计算成绩。软件、科学和金融的新能力均有参考源码，排样采用原求解器，Lean 保留原证明，游戏有合法动作选择策略。
- 六类评分器从 `public/scoring_metadata.json` 读取评分常量；`score_design.json` 同步保存相同常量。金融题明确：整段回测合法才有 0.25 基础分，非法决策使提交无效，额外分来自效用改进和校准。
- 游戏总评分预算为 1800 秒，覆盖 36×40 秒审计对局；金融为 2400 秒，覆盖最长开发集的 1006×2 秒决策与初始化。它们是预算配置，实际耗时未测。
- 提交工具冻结文件快照及实际 judge image ID，检查结构化反馈，记录历次最佳有效成绩；逐题读取评分预算，超时后清理本次评分容器。它是本地手动提交工具，不是远端正式六小时模型评测框架。

## 检查与复现

[静态检查结果](static_inspection.json)：六题文件清单完整、摘要一致、双构建上下文一致、50 份自有 Python 源码语法可解析、评分元数据一致。没有运行解题程序、评分器、Docker、Lean 编译或 Wesnoth。Lua 语法及运行也尚未验证。

构造代码在 [task_factory](../../task_factory/README.md)，配方与组件摘要在 [construction_recipe.json](construction_recipe.json)。复现到一个尚不存在的新目录：

```bash
.venv/bin/python task_factory/assemble.py --output samples/long-horizon-built-NEW
.venv/bin/python task_factory/inspect_package.py samples/long-horizon-built-NEW
.venv/bin/python task_factory/review_authoring.py samples/long-horizon-built-NEW
```

每题 `README.md` 给出参考解入口、提交目录、双镜像构建命令和证据边界。`public/` 用于 agent；`private/`、`verifier/`、`solution/` 仅供评判或作者使用。`task.toml` 当前明确标为本地契约，尚未映射远端技能中的正式 Harbor 规范。

## 后续对齐

用户提供的远端流程记录在 [工作约定](../../requirements/remote_edge_workflow_2026-10-14.md)。两次 SSH 尝试均未进入认证，远端技能未读；依用户最新要求暂缓连接。本地继续构造，保持他人原始文件不变。

后续先对齐造题和 QC 规范，再解决构建、隔离、确定性与难度问题。正式轨迹指定 `gpt-6.1-sol`、7 号 Codex 二进制、阿里云沙箱、完整 6 小时；先一条，通过或满足增长要求后再补两条。最终还需交付实际使用的评测框架代码，不能用本文的静态检查替代轨迹或验收证据。
