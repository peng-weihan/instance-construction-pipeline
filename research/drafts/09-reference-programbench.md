# ProgramBench 工厂对 EdgeBench 造题的启发

这套本地实现最值得复用的是“构造主张必须被控制器重新执行验证”的流水线。它能把已有 CLI 的行为变成有来源、有负对照、可重建的测试任务；要变成 EdgeBench 式长期规格重建或性能优化题，还需要独立的求解运行、反馈集、性能计量和难度校准。

本文只读 `upstream/swe-factory/`，未修改参考仓库、运行模型或 Docker。下文完整路径相对该参考仓库，`pipeline.py` 等源码短名均指 `programbench_factory/` 中同名文件；“原规格”指本地只读 `programbench.md`，它本身是逆向整理的复现规约，不等于上游官方实现。

## 1. 三种证据不能混为一谈

| 对象 | 本轮核实到的事实 | 结论边界 |
|---|---|---|
| 原规格 | 定义固定 CLI 版本 → 构建参考程序 → 黑盒观察 → 从零行为重建；R1/R2/R3 分级（`programbench.md:9–40`） | 规格含“原实现”“复现约定”“扩展”三类，不能全部称为原系统功能 |
| 本地实现 | `Pipeline.run()` 串联源码获取、builder、控制器 build/probe/QC 和可选 Docker 重建发布（`programbench_factory/pipeline.py:29–165`） | 存在代码说明实现了入口，不说明真实环境已经跑通 |
| 历史产物 | `runs/programbench-demo-02/summary.json` 为 `qc_passed`、`R1`、11/12 测试有效、host、synthetic、无模型/Docker，R2/R3/published 都为 false | 证明人工 C CLI 示例完成本地 R1；不能称为生产发布 |
| 历史失败 | `runs/programbench-demo-01/construction/summary.json` 在 QC 因测试 ID 无映射失败 | 保留失败可定位流水线断点，不能只统计目录数 |
| 历史组件测试 | 两份 `runs/factories-verification*/verification.json` 均记录 173 tests、0 failure/error/skip，无真实模型/Docker | 是既有报告，不是本轮重跑结果，更不是 ProgramBench R2/R3 证据 |

**分级准确含义：** R1 为完成构造期产物与 dummy/gold QC；R2 为独立重建参考程序并让有效集合重新通过；R3 为真实解题方 cleanroom、替代实现提交及隐藏评分全过程。当前代码可以把成功的 R2 标为 `status=published`，同时明确 `r3_verified=false`（`pipeline.py:147–159,246–248`）；因此 published 不代表 R3。

## 2. 从参考 CLI 到发布：实际代码主链

```mermaid
flowchart LR
    A[固定仓库与 commit] --> B[builder 交付 recipe / probes / tests]
    B --> C[控制器从冻结源码 build gold]
    C --> D[每个 probe 两次字节观测]
    D --> E[展平测试并建立 ID 映射]
    E --> F[独立 dummy / gold QC]
    F --> G[来源关联 / 核心分组 / gold 重跑]
    G --> H[R1 任务包]
    H --> I[独立 Docker build 与重建 gold]
    I --> J[有效测试重放与交付检查]
    J --> K[原子发布 R2]
    K --> L[待另接 R3 求解与隐藏评分]
```

| 阶段 | 输入与保留工件 | 控制器门禁 | 代码证据 |
|---|---|---|---|
| 候选与 builder | candidate、固定源码、角色轨迹；builder 给 `build.sh`、Dockerfile、分支测试和 manifest | 参考原文件不可改；声明离线 CLI 资格；许可证路径/依据、必要文件齐全 | `pipeline.py:35–58`；`prompts/builder.md:1–38` |
| 从干净输入构建 | 原始源码 + 明确 build assets；`build_manifest.json` 含源码、命令、运行时和 binary/build-script hash | 不沿用 agent scratch 的可执行文件；重跑 build；产物名/可执行位正确 | `pipeline.py:59–82` |
| Probe | argv、stdin/input files；`observations.json` 保存 base64 stdout/stderr、退出码、文件状态与 timeout | 每个声明 case 在新目录运行两次；稳定性精确比较；必须有 `--help` | `probe.py:18–55`；`pipeline.py:168–187` |
| Flatten | branch → 12 位 hash；dotted ID ↔ pytest native ID ↔ 原始测试位置 | 顶层同步无 decorator 测试；拒绝不支持的结构、重复定义和空 branch | `quality.py:12–59` |
| Dummy/gold QC | 独立工作区执行空脚本和真实参考程序，保留原生报告；`quality.json` | 只有 dummy 明确 failed 且 gold passed 才保留；至少 8 个；保留 ignored 原因 | `pipeline.py:190–202`；`quality.py:62–83` |
| R1 包装 | `tests.json`、`task.yaml`、`meta.json`、`eval/run.sh`、source-cleaning/provenance manifests | 至少一个有效核心 branch；有效测试关联现存 probe；gold 新目录重跑稳定 | `pipeline.py:96–150` |
| R2 重建 | 固定 recipe、全新 image、新 gold hash、QC 与 cleanroom 报告 | 基础镜像 digest/完整 SHA；实际 checkout 证据；有效集合 dummy/gold/gold-repeat 重放；文件与权限检查 | `delivery.py:12–65`；`pipeline.py:204–247` |
| 发布 | staging → `published/<identity>`；最终 summary | 仅 Docker backend 且 rebuild 全通过才原子改名发布；失败带 stage/reason 保留 | `pipeline.py:151–165` |

实际 builder 会在一次会话里准备 build、probes 和 tests；随后控制器重新 build/probe 并检验交付物。因此这是对生成提案的再验证，不是控制器在观察完成后自动合成测试。测试与 probe 的关联目前检查 manifest 中的 ID 存在性；gold 通过和 dummy 失败补充行为证据，但尚不能自动证明每条断言覆盖了题目语义（`pipeline.py:99–106`）。

原规格描述的旧门禁只对 help 做两次归一化比较；本地代码对所有已声明 probe 做精确字节比较，且没有通用归一化器（`programbench.md:300–306`；`probe.py:54`；`pipeline.py:183–186`）。这更适合确定性 CLI；随机程序或包含时间字段的输出需要在新模板明确稳定条件，不能直接照搬为通用 grader。

`eval/run.sh` 运行全部测试并使用 `|| true`；有效测试集合必须结合 JUnit 和 `tests.json` 解释，shell 退出 0 不是得分（`pipeline.py:137–145`；`programbench.md:582–595`）。这一点在迁移时应保留为评分接口约束。

## 3. 可以直接复用的工艺，与需要补充的能力

| 工艺 | EdgeBench 规格重建任务 | EdgeBench 性能任务 |
|---|---|---|
| 固定版本 + 独立 build manifest | 复用，以 gold 作为可观察的行为规范 | 复用，gold 作为正确性参考和初始实现；性能参考需另校准 |
| 字节级 probe 与期望来源记录 | 复用并扩成允许 agent 调用的实验接口 | 用于定义精确兼容行为，避免通过改变语义“加速” |
| ID 映射、有效集合与忽略原因 | 复用到隐藏覆盖评分；题面语义缺口需另外审查 | 复用作 correctness gate，不把通过率直接当 speed score |
| dummy/gold 双对照 + gold-repeat | 作为最小质量门禁；加入 help-only、恒定输出和近似实现对照 | 加入丢数据、边界错一位等 near-miss；正确后才准计时 |
| 独立镜像重建与原子发布 | 复用其证据链，适配 SForge 的环境与文件契约 | 复用，并冻结编译器、硬件、线程、输入与测量方法 |
| 失败阶段与原始证据保留 | 复用，区分生成失败、环境失败、候选不合格 | 复用，额外区分 correctness fail、measurement invalid、性能无改进 |

“复用”指设计与局部模块可借鉴，不是现有 ProgramBench 包可直接装入 SForge。它导出 `task.yaml/Dockerfile/eval`，需要转换为 EdgeBench 当前实际任务接口；R3 求解生命周期与性能 grader 也不在本模块中。

**必须新增的四层。** ①独立的公开反馈集、最终隐藏集和结构 OOD 集，并冻结 case 分配；②能接收 agent 产物的 R3 runner，保存 artifact hash、实验时间和反馈；③相同正确性下的连续质量指标，性能任务用独立计时、预热、多次重复和固定资源；④基于弱/中/强解与 15 分钟/1 小时/4 小时曲线的难度校准。以上都是迁移提案，未实现、未实跑。

现有 `difficulty()` 使用 `flags + 4×subcommands + branches + kept//30` 决定标签，是接口规模启发式（`quality.py:86–94`；`programbench.md:612–626`）。它不能替代实际求解难度或长期提升空间；100–400 tests、5–10 branches 同样是 builder 提示目标，控制器最低门槛仍是 8 个（`prompts/builder.md:23–25`）。

构造 agent 的 80 步/4096 tokens/工具 150 秒预算控制的是造题过程，不能算成解题 agent 的长期预算。可选 JSON-action 引擎只支持 builder、要求 Docker，保存动作/工具证据，模型观察被截取尾部 4000 字符（`actions.py:26–38,67–136`）；其流程适合复用到造题器，不能冒称已有长时 solver。

## 4. 对三层生成单位的具体映射

题族是“某种 CLI 行为重建/兼容实现”或“保持语义的性能优化”模板；task instance 是固定版本、目标功能面、公开材料、探测权限和预算的冻结组合；probe/test input 是该 instance 内的 case。为同一 bytecopy 再加 100 个随机输入，只增加 case。改变候选 CLI、可观察接口或需支持的规则组合才可能产生新 instance，仍需按代码/行为相似性分组去重，不能默认不同 commit 就独立。

建议先选 3–5 个离线、确定、可低成本构建的 CLI，复用本流程得到 R1 证据，再做真正的 R2 与 SForge 适配。为每个候选分别产出行为重建版和正确性约束下的性能版时，应共享内部 oracle，但独立定义任务目标和统计分组，避免把高度相关双版本计为独立能力覆盖。

## 5. 历史状态复核与阅读覆盖

对 demo-02 的 `construction/observations.json` 做只读汇总：13 个 probe、26 条观测、0 timeout，配对字节观测一致；`tests.json` 的唯一忽略原因是 `dummy_pass`。`stages.json` 终止于 `qc_passed`，没有 independent_rebuild/published。demo 源码也显式 `Runner(backend="host")`、`rebuild=False`，并提供未验证占位 Dockerfile（`demo.py:47,65–67`）。未发现本次抽查范围内的真实 R2/R3 产物；不推断未查看目录的状态。

| 文件/对象 | 类型 | 总行数 | 实读范围/行数 | 覆盖及门槛 |
|---|---|---:|---|---|
| `programbench_factory/pipeline.py` | 核心 | 249 | 1–249 | 100%，≥60% |
| `programbench_factory/quality.py` | 核心 | 94 | 1–94 | 100%，≥60% |
| `programbench_factory/probe.py` | 核心 | 59 | 1–59 | 100%，≥60% |
| `programbench_factory/delivery.py` | 核心 | 65 | 1–65 | 100%，≥60% |
| `actions.py`、`demo.py`、`cli.py`、`__main__.py`、`__init__.py` | 次要 | 213 | 各文件全读 | 100%，≥30% |
| `prompts/builder.md` | 次要文档 | 38 | 1–38 | 100%，≥30% |
| `programbench.md` | 规格文档 | 839 | 1–40、176–190、211–368、451–668、745–803，共590行 | 70.3%，≥30% |
| 合计源码（含注释空行） | 核心+次要 | 680 | 680 | ✅ 100%；未把共享源码算入本模块 |

根 `AGENTS.md`、`README.md`、`docs/factory_reproduction.md` 已全文阅读。历史 JSON 仅提取状态、测试计数和必要观测统计，未展示配置、认证或环境字段。该工厂给出的起点是可信构造链；最终是否成为长期研究任务，仍由新的 R3 试跑和分数随时间的提升决定。
