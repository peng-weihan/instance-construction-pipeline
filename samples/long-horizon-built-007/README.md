# 六类长程任务构造版 007

每类一个构造小样，目标预算六小时。源码、材料、题面、参考实现、评分器与双环境构建上下文已经打包；目标预算不是已经验证的任务难度。旧批次保留。

| 类别 | 任务目录 | 当前运行证据 |
|---|---|---|
| 软件工程 | restler_resilient_execution | 远端双镜像与五组评分控制完成，参考 50/50，starter 0 |
| 科学反演 | layered_aquifer_source_lab | 本地可信组件与公开观测反演，尚无远端容器验证 |
| 组合优化 | industrial_nesting_improvement | 本地几何反例，未运行 C++ 求解器 |
| 形式化数学 | brownian_multibranch_proofs | 尚未执行 Lean 内核验证 |
| 金融策略 | cross_asset_adaptive_allocator | 本地可信策略和账本组件，尚无远端容器验证 |
| 游戏 | wesnoth_frontier_campaign_ai | 本地 Lua 解析/动作探针，未运行游戏引擎 |

证据：[本地组件验证](../../runs/local-validation-003/REPORT.md)、[首题远端验证](../../runs/remote-smoke-restler-007/REPORT.md)。科学题在完成正向实现后反演快速饱和，金融参考的反馈分接近满分；两者仍需难度校准。六题均未运行正式六小时模型轨迹。

现有 task.toml 为项目本地契约。已读取远端主规范，下一阶段需要按 Harbor 0.23.0 接入原生评分与自动周期采样。冻结题包内的构造期 evidence/provenance 保留原状态，后续运行证据以这些独立报告为准，不回写历史文件伪造已验证状态。
