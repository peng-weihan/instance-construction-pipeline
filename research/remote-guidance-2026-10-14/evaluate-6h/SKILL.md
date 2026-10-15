---
name: edgebench-evaluate-6h
description: 使用 Harbor 0.23.0 官方 Codex adapter 运行 EdgeBench 六小时评测，支持指定静态出口 Codex 完整包、Docker 或阿里云环境、十分钟评分及原生轨迹归档。
---

# EdgeBench 六小时评测

实际任务加载和执行入口为 Harbor 0.23.0 的 `harbor run --agent codex`。使用未修改的官方 Codex agent；指定二进制的安装、账号绑定和长时监督由环境及外部控制器处理。`sforge-submit` 是兼容提交工具名，不表示必须使用自定义 `SForgeCodex` agent。

后端由用户指定，支持 Docker 和阿里云兼容 E2B；不隐式切换。两种环境均保留题目资源与唯一评分器，隐藏测试、参考解和宿主账号目录不进入解题环境。用户指定静态出口二进制时，先读 [官方 adapter、静态出口与轨迹契约](references/official-codex-static-egress.md)。

强模型为 `gpt-6.1-sol`，正式学习预算 21600 秒，每 600 秒自动捕获并运行同一个权威评分器。正式评测关闭难度早停，分数快慢只用于完整评测后的选题复核；用户明确中止及真实基础设施故障另行记录。较早的首小时<0.2/三小时≈0.4/六小时≈0.5仅是历史设计目标。当前用户确认保留原评分，按三条最好分均分曲线判断：首小时涨幅不超过0.50，2–6h增长达到2h最好均分的10%，即M6≥1.10*M2；不是加0.10或加5分。零分母及真实性/噪声复核见 `/ws/users/wcgu/skills/edgebench-task-authoring/references/growth-judgement.md`。无有效评分、快照或平台故障不是有效零分。交付三条独立正式轨迹；时间宽裕可首条完成后补两条，十小时硬截止需后两条在截止时刻减六小时减收尾裕量前实际开始学习，不能承诺串行6h+6h十小时交付。

## 输入与准备

逐题明确任务绝对路径、`CODEX_HOME`、提交路径、模型域名和云端依赖。未指定 `CODEX_HOME` 时询问用户；不默认账号，不登录、不改账号配置。同一登录态可并发多题，每题独立目录和实例。

Docker 读取下文的正式入口及静态出口参考。阿里云移植另读 [云端任务和评分契约](references/cloud-runtime.md) 和 `/ws/users/aliyun-sandbox-rollout/SKILL.md`；云端仍需真实模板/build、`aliyun.json` 和离线 bootstrap，Dockerfile 不能替代云定义。工作目录为 `/home/workspace/<project>`，产物在 `submission/`；`environment/` 只含公开内容，`tests/` 含私有评分器；候选程序以非 root 身份执行。

每次实际评分检查 `reward.txt` 与结构化报告表达同一归一化分数；不允许原生 reward 二值而周期评分为部分分。

## Docker 正式入口

明确选择已冻结、具备 `run_docker_6h.py` 的评测框架目录和 Harbor Python 环境，不自动选择最新草稿。框架必须使用官方 `--agent codex`，完整校验指定 CLI/helper/package、镜像、题包、实际控制和模型准入证据。启动脚本只转发参数，不修改冻结运行代码：

```bash
/prepared/harbor-venv/bin/python \
  /ws/users/wcgu/edgebench/dev/skills/edgebench-evaluate-6h/scripts/run_pipeline.py \
  --backend docker --framework-root /absolute/path/frozen-framework \
  --task /absolute/path/task --images /absolute/path/images.json \
  --controls /absolute/path/controls.json \
  --partial-controls /absolute/path/partial-controls.json \
  --admission /absolute/path/official-codex-smoke/report.json \
  --codex-home /explicit/account-directory --output /absolute/path/new-run \
  --prepare-only
```

`--prepare-only` 校验并准备，不调用模型。实际启动时去掉该参数并选择新的输出目录；需要复用未变评分组件的旧测量时，额外传当前框架支持的 `--source-component-attestation`，保留旧测量原版本标识。正式模型准入须为实际官方 Codex 会话、成功工具执行和产物验证，不能仅凭 `--version`、登录检查或 curl 成功。

## 阿里云既有入口

以下命令块仅供历史排查，未经当前官方adapter/完整六小时/open-solution分支实际核验，**不得据此启动正式云端评测**。当前通用已核实正式入口为上述Docker分支；切换云端必须提交本题的新冻结入口和实测证据。既有 `cloud_pipeline` 可能仍包含自定义 agent 或难度早停；未经升级及实际验证不能作为上述官方 adapter、完整六小时模式的替代。选择阿里云时在新运行版本中完成相同兼容验证，不改写已有轨迹。

```bash
export PYTHONPATH=/ws/users/wcgu/edgebench/dev/sforge-harbor-adapter:/ws/users/aliyun-sandbox-rollout/scripts:/ws/users/wcgu/edgebench/dev/harbor/src
AS_PYTHON=/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python
"$AS_PYTHON" -m edgebench_harbor.cloud_controls \
  --task /absolute/path/task \
  --profile /absolute/path/task/pipeline-profile.json \
  --codex-home /explicit/CODEX_HOME --codex-version 0.160.0
```

读取输出 `CONTROLS=.../cloud-controls.json`：普通Oracle须真实达到声明奖励上限，NOP须到下限，无trial异常且实例已确认删除。open-solution记录可运行参考的真实原始指标与归一化成绩，不要求参考=1；必须实测当前入口支持该分支。旧cloud_controls若硬编码Oracle=1，先在独立版本补齐open-solution控制，不伪造满分文件或重设锚点。题包、工具链或运行时代码改变后重做受影响控制，不借其他题目的记录。

按参考文件填写 pipeline 配置：`backend: aliyun`、`task`、包内 `profile`、`cloud_controls_manifest`、`codex_version`、`model_hosts`、`strong.model/codex_home`、`score_min: 0`、`score_max: 1`、`max_revisions: 0`。

```bash
"$AS_PYTHON" \
  /ws/users/wcgu/edgebench/dev/skills/edgebench-evaluate-6h/scripts/run_pipeline.py \
  --backend aliyun --config /absolute/path/pipeline-config.json --direct-strong
```

入口调用 `edgebench_harbor.cloud_pipeline`。SDK skill 在 `/ws/users/aliyun-sandbox-rollout/`，实际适配器在 `/ws/users/wcgu/edgebench/dev/sforge-harbor-adapter/`，Harbor 0.23.0 从 `/ws/users/wcgu/edgebench/dev/harbor/` 冻结到本轮目录。已有宿主私有连接配置由 SDK Python 自动加载，不输出密钥。

学习预算与启动、评分收尾分开：以实际学习进程开始计时，21600 秒到点停止该进程及其工具。Harbor 外层超时须覆盖启动与按待评分数量、worker 数和单次 verifier 预算计算的收尾裕量，不能也设为21600秒而提前取消学习窗口。额外时间只用于启动准备或收取评分与证据，不增加解题预算；未评分快照不补零。

实测评分超过十分钟时，可在包内 profile 显式设置 `grading_workers: 3`（整数 1–4，默认 1），各 worker 使用独立 verifier 沙箱，评分器和单次资源预算不变。框架升级后刷新当前运行时的控制证据；已启动的轨迹使用冻结代码，不为升级而重启。

## 输出与负责人交接

Docker 输出使用显式 `--output` 目录及该框架的 run manifest；阿里云既有 pipeline 输出在 `<TASK>/pipelines/<id>/`，冻结任务在 `revisions/v000/task/`，运行在其 `runs/6h/<id>/`。两者都保留实际 jobs、原生轨迹、生命周期及 evaluation 证据。评分目录保留快照、原始 verifier 证据、`history.json`、`best.json`、`scores.jsonl` 和曲线。门槛按快照时间判断，曲线记录反馈实际到达时间。

模型无需主动提交才有周期评分，也可用 `sforge-submit` 获得手动反馈。只回传允许的分数和诊断，不回传隐藏答案、原始私有日志或宿主路径。

完整评测后的难度返修由本题负责人读取真实轨迹、提交、判分及历史，在新题目版本中处理并复核控制。历史云端早停轨迹仅标为短评测，不能充当正式六小时轨迹。

`--resume <pipeline-dir>` 只接管现有监督进程：核实 PID/start ticks，等待原 solver 或收取其已落盘结果，不重复启动。该监督接管不等于原生会话恢复。用户授权的原生resume另核合法会话prefix/工具边界、workspace制品、原session ID、剩余实际预算和短测；跨账号/CLI续段列分段来源与中断证据，不声称同质连续六小时，不混不同题目/修订。

沙箱滑动续期覆盖启动、解题和收尾；每 30 秒回传允许的日志，销毁前采集，销毁后确认控制面 not-found。提前退出 137/124、失去沙箱、续期或快照失败均标异常，不当预算完成。短暂断流或 API 错误自动恢复，且后续执行和有效提交正常时，记录中断、影响时间及恢复证据，不直接否定整轮。持续故障、异常进程退出或长时间无法工作时，保留已有有效快照，但不得以受故障影响的低分证明题目难，应修复后重测。失败次数只作记录，不能作为单独否定整轮的门槛；持续 API 故障默认阈值为 600 秒，运行协议可用 runtime_max_outage_sec 配置。缺少中断时间或恢复证据时标记待人工复核，不虚构中断为 0 秒，不自动判为失败。评分公式及难度分数门槛保持不变。

报告区分原生控制、短轨迹/早停验证、完整六小时完成和题目验收通过；基础设施样例不作为正式难度证据。


## 本批交付依据（2026-10-11）

用户指定的两份交付原文、提取文本和SHA256在 `/ws/users/wcgu/edgebench/dev/requirements/delivery-20261011`。准备交付、判断交付通过或编写交付缺项时，先读 [交付要求与证据清单](references/delivery-20261011.md)。基本题包QC、单次6h校准和完整交付验收分别报告；不得用前两项替代三次以上前沿模型均分、五次同快照及跨架构等交付证据。当前活题包和轨迹不因指南更新而修改；缺项交原负责人在新版本处理。本skill原有运行/付费授权边界保持，task-qc基础审查不自动扩展为完整交付审查。
