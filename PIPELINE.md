# EdgeBench 训练任务工厂

2026-10-14 新增交付依据：[用户任务书原文](requirements/collection_brief_2026-10-14.raw.txt)及[要求与差距清单](requirements/collection_brief_2026-10-14.requirements.json)。正式目标为 Harbor 双环境任务，至少 3 小时 agent 预算、运行中反复提交和结构化反馈、最终取历次最佳成绩，并逐题提供 oracle/nop/至少三次模型运行等证据。后文描述的是既有开发试点，不能作为新规格验收证明。原文缺失处不自行补写；具体 task.toml schema、类别配额等仍待完整规范。

## 当前主线：原版合同、难度校准与真实 SFT 轨迹

代码在 `training_factory/`。目标产物是“优化通用 C++17 求解器”的完整工程任务，加真实修改/测试/反馈轨迹和验收后的代码；单个 VRP 路线答案不是一条 Agent 训练轨迹。

实际构造链条：

```text
官方镜像与任务合同
  → 仅提取作者侧统计与求解器响应，不复用原始输入
  → 新坐标 / 新需求 / 新时间窗 + 可行证书
  → 原版 C++ 检查器 + 独立 Python 检查器
  → 三次固定预算 PyVRP 校准
  → 按题族匹配原版搜索收益，保留偏差报告
  → 公开工程 / 反馈 56 例 / 独立终评 56 例
  → gpt-6.1-sol 真实开发与聚合反馈
  → 冻结源代码、一次终评、轨迹完整性检查
  → 达标轨迹进入 SFT JSONL；失败留档
```

### 对齐了什么

原版镜像实际使用 **56 个 Solomon-100 输入**，C1/C2/R1/R2/RC1/RC2 数量分别为 9/8/12/11/8/8。镜像文档中的更大规模生成器属于扩展资产，不能据此把扩大客户数当作原版难度。当前任务的反馈与终评分别保持这 56 例的题族比例，公开样本每族 1 例。

- 保留原版 C++17 工程、提交路径、可执行文件名称、三参数 CLI 和输出格式。
- 使用欧氏距离逐边四舍五入到 0.1，保持容量、时间窗、服务时间、回仓时限和车辆上限。
- 保留原版车辆优先的评分公式；报告的是 **0–160 的每例原始分的均值**，不是旧原型的单车节省分。100 表示匹配冻结参考，参考解允许被超过。
- 新数据全部使用整数坐标、新点集；236 例各有独立几何布局，与原始题整例及点集的交集都是 0。官方 56 例只有 4 个不同的几何点集，因此统计校准并不等同于拥有 56 个独立空间分布样本。
- 不复用原始题的点集、节点排列、路线或 BKS 答案。原始数据只留在作者侧做校准。该过程是知晓基准分布的构造，不是完全未接触基准的数据生产。

### 校准证据

第一版 36 例用于诊断；正式候选池为 [aligned-candidates-002](runs/aligned-candidates-002/)，共 236 例。参考解为 PyVRP 0.14.0 的 1,000 迭代 seed 0、6,000 迭代 seed 0 和 seed 1 三次运行中的最好可行解，全部通过原版检查器。它们是有限预算参考，**不声明最优**。

原始 56 例也执行了相同的三次求解预算。筛选时匹配“短预算解相对同组最佳参考的得分”，在看教师结果前固定每个题族、每个 split 的均值偏差上限为 5 分。得到 [difficulty-aligned-selection-001](runs/difficulty-aligned-selection-001/alignment.json) 的 118 例。未筛选候选池在 C1/C2/RC1 上存在明显偏差，不能直接称为同难度数据。

| 题族 | 原始短预算均分 | 筛选后反馈均分 | 筛选后终评均分 |
|---|---:|---:|---:|
| C1 | 100.00 | 99.02 | 98.93 |
| C2 | 99.96 | 99.70 | 99.60 |
| R1 | 91.29 | 91.45 | 91.49 |
| R2 | 93.68 | 93.98 | 94.08 |
| RC1 | 76.35 | 80.39 | 80.51 |
| RC2 | 91.93 | 92.02 | 92.08 |

这些检查对齐了输入合同、若干边际统计、题族权重和一个求解器响应指标；**没有证明联合分布相等，也没有证明 12 小时 Agent 难度相同**。当前只覆盖原版 134 题中的路线优化题族。

### SFT 采集和验收

工作包：[sft-aligned-pilot-002](runs/sft-aligned-pilot-002/)。两条轨迹在同一套任务上独立运行，模型均为 `gpt-6.1-sol`、low 推理档，每条最多 600 秒；这不是两道独立题族。完整日志记录于各 episode 的 `events.jsonl`，命令与响应另存于 `tool_commands/`。

两条均已完成并通过当前 SFT 门禁，发布文件为 [train.jsonl](runs/sft-release-001/train.jsonl)，完整汇总为 [delivery_summary.json](runs/sft-release-001/delivery_summary.json)。发布包还保存逐条可读的最终 C++ 源码和修改补丁。26 项自动化测试通过；2 条记录的模型、轨迹摘要、冻结代码、资产未变和 split 不重叠均已复核。

| 轨迹 | 教师开发时间 | 真实命令数 | 最终代码反馈分（1 秒/例） | 独立终评分（3 秒/例） | 终评可行 |
|---|---:|---:|---:|---:|---:|
| teacher-001 | 453.69 秒 | 10 | 106.11 | 106.58 | 56/56 |
| teacher-002 | 379.05 秒 | 7 | 105.95 | 106.24 | 56/56 |

这些分数高于 100，说明冻结的有限预算 PyVRP 参考可以被超过，不代表达到数学最优。为区分参考偏弱与新题偏易，冻结程序另在原始 56 例上以同样 **1 秒/例** 运行：

| 轨迹 | 原题相对同预算 PyVRP 参考 | 原题相对官方 BKS 表 | 原题可行 |
|---|---:|---:|---:|
| teacher-001 | 105.62 | 93.29 | 56/56 |
| teacher-002 | 104.62 | 92.15 | 56/56 |

相同程序、相同 1 秒预算及同类 PyVRP 锚点下，新题与原题的均分差分别为 0.48 和 1.33 分。这是有限的迁移证据；只有两个相近算法、一个题族，不能推广为整个 EdgeBench 同分布证明。原题审计没有调用模型，也没有把结果反馈给教师，详见 [original-transfer-audit-001](runs/original-transfer-audit-001/summary.json)。官方 BKS 与原版四舍五入距离存在精度口径差异，保留原始 judge 的表值计算方式。

macOS 使用独立 CLI 临时目录与文件队列工具，解决原生命令沙箱无法嵌套的问题。教师与命令执行器均做文件禁读；只向教师返回聚合反馈。工作目录相互禁读。教师命令的写入范围限制在自己的工作目录，评测数据和参考答案位于作者侧。工具执行用真实模型请求，不补写“理想推理链”。临时登录凭据不进入日志/训练集，用完删除副本。

Pilot 反馈每例 1 秒、独立终评每例 3 秒；原版完整预算配置为每例 60 秒且全局 20 分钟。本地 pilot 的分数不能作为原版完整协议成绩。冻结代码之后另做原始 56 例迁移审计，结果不再提供给教师。

SFT 门禁在运行前固定：终评 56/56 可行，原始均分 ≥90，最终提交的反馈相比 starter 提升 ≥20，代码有实际修改，完整真实事件流，无缺失的文件修改记录，文件隔离探针通过。发布阶段额外检查模型、预算、冻结代码/日志摘要以及难度筛选早于教师运行。`file_change` 只有路径而没有可回放修改内容时会拒绝完整轨迹导出。

同一任务的两条轨迹必须划入同一个训练/验证分组；本次没有独立题族验证集。当前实现经过本机编译、双检查器和轨迹验证，Linux Docker/SForge 完整生命周期仍需单独验收。

### 复现入口

Python 3.12；作者侧安装 `training_factory/requirements.txt`。输出目录必须是新目录。

```bash
# 原始起始程序及可信检查器
mkdir -p runs/alignment-calibration-001/tools
clang++ -std=c++17 -O3 data/routing_alignment/original_work/src/solver.cpp -o runs/alignment-calibration-001/tools/original_baseline
clang++ -std=c++17 -O3 data/routing_alignment/original_work/tools/verify.cpp -o runs/alignment-calibration-001/tools/original_verify

# 生成、同预算校准、筛选与打包
.venv/bin/python -m training_factory.calibrate --output runs/new-candidates --source-multiples 4 --public-per-family 2 --iterations 1000 --long-iterations 6000
.venv/bin/python -m training_factory.compare --output runs/new-original-calibration
.venv/bin/python -m training_factory.align --pool runs/new-candidates --original runs/new-original-calibration --output runs/new-selected
.venv/bin/python -m training_factory.pack --pool runs/new-selected --output runs/new-sft --tasks 1

# 显式指定模型和时间，task-id 见输出 tasks/ 目录；当前教师执行器针对 macOS
.venv/bin/python -m training_factory.teacher --task runs/new-sft/tasks/<task-id> --output runs/new-sft/episodes/teacher-001 --model gpt-6.1-sol --seconds 600
.venv/bin/python -m training_factory.release --run runs/new-sft --output runs/new-sft-release
.venv/bin/python -m training_factory.transfer --run runs/new-sft --original-calibration runs/new-original-calibration --output runs/new-transfer --budget 1
.venv/bin/python -m unittest discover -s tests -v
```

核心模块：`generator.py` 生成；`contract.py` 合同与独立检查；`reference.py` PyVRP；`calibrate.py` 候选验题；`compare.py` 原题校准；`align.py` 难度筛选；`pack.py` 工程打包；`teacher.py` 真轨迹和终评；`mcp_bridge.py` 命令队列；`release.py` 入库；`transfer.py` 冻结程序在原题上的迁移审计。

来源：[EdgeBench 官方仓库](https://github.com/ByteDance-Seed/EdgeBench)、[公开数据](https://huggingface.co/datasets/ByteDance-Seed/EdgeBench)、[SINTEF 原始问题说明](https://www.sintef.no/projectweb/top/vrptw/100-customers/)、[PyVRP](https://pyvrp.org/)、[OpenAI 官方 MCP 配置](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。镜像层和文件摘要见 `data/routing_alignment/provenance.json`。

## 历史记录：早期小规模原型（不用于当前 SFT）

已实现一条路线优化题族流水线：参数采样 → 可行证书 → 三份数据划分 → 参考与错误答案验题 → SForge 导出 → 反馈选解 → 一次终评。首批生成 **6 个实例、90 个样本，6 个实例均通过本地质量检查**。

这条原型借用了 SWE Factory 的参考解/空答案对照、独立验题和分阶段证据记录方式。代码位于本项目的 `edge_factory/`，复制来的三个工厂保持原样。

## 本次运行结果

运行目录：[runs/routing-pilot-001](runs/routing-pilot-001/)。原始汇总见 [summary.json](runs/routing-pilot-001/summary.json)，SForge 官方契约检查见 [sforge_contract_validation.json](runs/routing-pilot-001/sforge_contract_validation.json)。

| 配置 | 实例数 | 每个样本的客户数 | 变化机制 |
|---|---:|---:|---|
| uniform_loose | 2 | 24 | 均匀空间分布、宽时间窗 |
| clustered_tight | 2 | 32 | 聚簇分布、紧时间窗 |
| clustered_stop_limit | 2 | 40 | 聚簇分布、每条路线最多 4 次停靠 |

每个实例有 3 个公开样本、6 个反馈样本、6 个独立终评样本。不同实例通过配置与作者 seed 派生不同分布工作包；这里仍是一个题族，不计作六个新题族。

| 算法 | 平均反馈分 |
|---|---:|
| 每客户一辆车 | 0.00 |
| 贪心构造 | 72.23 |
| 贪心加局部搜索 | 74.12 |

每个实例均依据反馈选择并冻结程序后再终评，平均终评分为 **74.50**。本机各实例构造与验题耗时合计约 12 秒。一次 smoke run 保留在 `runs/routing-smoke-001/`，属于开发早期产物；使用上述 pilot 目录作为交付样例。

验证结果：

- 14 项自动化测试通过，覆盖约束边界、60 组生成配置/seed 的可行性与基线改进、12 个小规模精确解对照、错误程序、资产划分和一次终评。
- 每个实例有 12 项质量门禁，10 种错误程序对照均被拒绝；全批次 90 个样本无完全相同的内容摘要。
- 官方 SForge loader 读取 6 份反馈任务与 6 份终评任务；官方 Dockerfile 模板可渲染；官方 parser、归一化和选择器通过 18 份实际导出评测日志检查。

当前机器没有 Docker，结果状态为 `host_verified`。容器内权限/资源隔离与真实 Agent 长时运行尚未验收；本次分数证明基线可区分，尚未证明任务具有 12 小时难度。基础镜像当前使用 tag，部署时可通过 `--base-image image@sha256:...` 固定镜像摘要。

## 一条命令试产

在本工作区根目录运行，使用 Python 3.10 或更新版本；本次用 Python 3.12，核心流水线只依赖标准库。

```bash
python3.12 -m edge_factory run \
  --output runs/my-routing-trial \
  --replicas 2 \
  --public-cases 3 \
  --feedback-cases 6 \
  --final-cases 6 \
  --trusted-host
```

输出目录必须尚不存在。默认用随机 256 位作者 seed，并将其保存在权限为 `0600` 的 `author_secrets.json`。复现本次样例时添加 `--seed pilot-20261014`；固定演示 seed 的数据适合调试，正式盲测应使用私有随机 seed。

只试一个配置可加 `--profiles uniform_loose --replicas 1`。`--trusted-host` 明确用于流水线内置的作者自有基线；本地 subprocess 不构成隔离沙箱。实际 Agent 提交应在验收后的 Judge 容器中执行。

检查一个自有程序的反馈得分：

```bash
python3.12 -m edge_factory evaluate \
  --instance runs/routing-pilot-001/instances/routing_uniform_loose_6693a63fa4d4 \
  --solver runs/routing-pilot-001/instances/routing_uniform_loose_6693a63fa4d4/selected/solver.py \
  --split feedback --trusted-host
```

`evaluate` 只提供 public/feedback 两种 split。构造时已经做过终评的实例，再执行 `finalize` 会失败；变更冻结程序或终评数据也会被拒绝。需要新的实验时创建新的运行目录，保留原有结果。

## 产物和职责

```text
run/
  author_secrets.json           作者私有 seed，不能给求解 Agent
  run_config.json               源文件 SHA256、解释器、配置、执行方式
  summary.json                  批量进度、质量结果、基线得分
  export/
    feedback/                   通过门禁的 SForge 反馈任务与 BENCHMARK.yaml
    final/                      单独的终评任务配置，不能当反馈服务开放
  instances/<task_id>/
    public/                     SPEC、最小 starter、公开样本、本地检查器
    judge/                      可信 checker/evaluator、反馈与终评样本
    author/                     生成证书、小规模精确最优解
    baselines/                  单车、贪心、局部搜索程序
    controls/                   空解、重复客户、超时、伪造评分等错误程序
    selected/solver.py          只根据反馈选择的冻结程序
    reports/                    门禁、基线、导出回放、选择收据与一次终评
    export/                     本实例的导出候选，便于检查失败产物
    events.jsonl                阶段日志
    manifest.json               身份、配置、来源、文件和 case 内容摘要
```

`export/`、`author/`、`judge/` 是作者侧资产。Work 的构建载荷只含 `public/`，Judge 的载荷只含评测器及对应 split；不会把完整工作包发送给 Agent。公开 starter 只实现单客户路线，不包含私有搜索算法。

| 模块 | 实际责任 |
|---|---|
| [generator.py](edge_factory/generator.py) | 按 profile/replica/split/index 派生独立 seed；先构造路线，再反推可行时间窗，打乱客户 ID |
| [checker.py](edge_factory/runtime/checker.py) | 独立核验覆盖、容量、时间窗、停靠数、回仓时间，重新计算成本 |
| [evaluate.py](edge_factory/runtime/evaluate.py) | 逐样本启动程序，限制时间与输出，严格解析 JSON，只向外返回聚合反馈 |
| [quality.py](edge_factory/quality.py) | 小规模穷举路线加集合划分 DP oracle；错误程序对照 |
| [baseline.py](edge_factory/baseline.py) | 三种只读取公开输入合同的基线；局部搜索使用确定性迭代次数 |
| [exporter.py](edge_factory/exporter.py) | 将公开/私有资产编译进带 SHA256 校验的 setup_cmds，导出标准 SForge TaskSpec |
| [pipeline.py](edge_factory/pipeline.py) | 阶段编排、质量门禁、导出回放、反馈选解、一次终评与入库记录 |

## 评分与验题设计

车辆费用与路程组成原始成本。分数是相对单客户路线的成本节省比例：

```text
cost = travel_distance + vehicle_cost × route_count
case_score = 100 × max(0, 1 - cost / singleton_cost)
```

所有样本必须可行，否则提交 `valid=false, score=0`；合法提交按样本等权平均。这个规则给出明确零分基线，允许持续优化，且不依赖参赛程序自报成本或缺失的 best-known 表。100 分并不代表已知可达到的最优值，保存的原始成本支持后续分析。

主要门禁包括：相同作者 seed 重建一致、split 无完全重复样本、全部可行证书通过、独立小规模精确 oracle 对照、10 种错误程序拒绝、所有基线可行、强弱基线至少相差 10 分、搜索不劣于贪心、重复得分一致、Work 仅公开资产、反馈 Judge 不含终评数据、导出后的实际评测器回放一致。

终评锁在执行前排他创建，避免失败后无记录地重复试分；选择收据记录程序和终评数据的摘要。终评成绩不参与构造门禁或基线选择。

## 复查与下一步

```bash
python3.12 -m unittest discover -s tests -v
python3 scripts/verify_sforge_export.py --run runs/routing-pilot-001
```

第二条需要官方 loader 的 `PyYAML` 和 `typing_extensions`，本次使用已安装这两个包的 `python3` 做契约检查。首次运行保存结果，再次运行重新检查并要求结果一致，不会静默覆盖不同结果。该检查没有启动 SForge 服务、构建容器或调用模型。

下一步先在 Linux Docker 环境验证 Work→提交归档→Judge→反馈的实际生命周期，再用短预算 Agent 试跑检查任务是否过易。若要覆盖软件题，可沿相同 `public / judge / author / reports` 合同加入 DeepSWE 构造适配器；当前实现尚未接入真实仓库的软件题生产。
