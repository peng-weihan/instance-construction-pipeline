# 软件工程多路线造题小样

本批响应用户“一次性多尝试一些”的要求，用 gpt-6.1-sol 作者分组并行构造六条路线，覆盖五种原题机制。目标是比较真实素材能否变成有明确合同、起始代码、参考和行为评分的任务。没有把六个目录计为六道合格题，也没有在本批启动六小时教师轨迹。

| 路线 | 机制 | 素材与目标 |
|---|---|---|
| [01_openapi](01_openapi/) | 多目标工程演进 | 真实 OpenAPI 客户端生成器的跨层组合语义 |
| [02_restler](02_restler/) | 多目标工程演进 | 真实状态化执行链的持久化恢复与重放 |
| [03_wasm](03_wasm/) | 从规格实现系统能力 | 官方 Wasm 语义下的解释器与规范化陷阱 |
| [04_datafusion](04_datafusion/) | 正确性约束性能优化 | 真实查询引擎的排序/Top-K路径及工作负载 |
| [05_toml](05_toml/) | 跨模块恢复 | Rust TOML workspace 的解析、编辑、输出能力 |
| [06_jq](06_jq/) | 行为等价重实现 | jq CLI 的流、组合、作用域和错误行为 |

来源与初始作者分工在 [routes.json](routes.json)；共同约束见 [AUTHOR_CONTRACT.md](AUTHOR_CONTRACT.md)。每条的最新作者结果、实测控制和缺项在各自 `AUTHORING_REPORT.json`，综合结果将在 `REPORT.md` 记录。未闭合参考或真实性能锚点的路线保留为 hold，而不是伪造分数。

## 可重复的工作流程

1. 真实官方来源→固定 revision/许可/摘要→source-card，指出已有功能、廉价替代路径和最大未知项。
2. 作者阅读真实仓库/规范→明确任务合同→starter、参考分支、实际运行链路与语义测试；不是只拼标题或生成题面。
3. 在本地执行可用的参考、空提交、部分解与近似错误实现；记录真实命令和分数，编译器/依赖缺失单列。
4. 检查格式、双构建上下文、提交快照、评分公式、原始指标和结构化反馈；主机控制不替代镜像/Harbor运行。
5. 比较六条的真实性、闭合程度、廉价解路径、评分辨别力和剩余增长假设，决定 build_pilot / hold_for_evidence / reject。
6. 后续通过基础准入的路线才进入既定的首条六小时校准，符合要求后补两条；保留自然原分和完整学习窗口。

从 edgebench 根目录收集证据：

```bash
.venv/bin/python samples/software-multiline-001/collect.py
```

该命令只读取题目文件和作者报告、生成 `BATCH_STATUS.json`；文件齐全不等于通过。需要已建立的开发机 SSH 连接时，可对实际 Harbor 0.23.0 源码执行只读配置验证：

```bash
.venv/bin/python samples/software-multiline-001/validate_schema_remote.py
```

这只解析配置且检测会被 Pydantic 忽略的未知键，不启动候选/容器/模型，不修改远端源文件；输出不证明镜像或评分运行通过。

## 规范与证据边界

用户指定的 authoring skill 当前快照与本批相关参考在 [guidance](guidance/)，含远端实际 Harbor schema 源码和 SHA-256。原始参考、旧题、旧轨迹和共享账号保持不变。私有参考/隐藏目标不进 work 构建上下文，所有求解制品进入 submission/。

本批明确区分：素材固定、题目构造、主机组件控制、镜像/Harbor验证、六小时难度校准、三条曲线达标和正式交付验收。作者构造轨迹不是六小时解题轨迹；未测的难度、ARM、镜像digest和训练效果都不写成通过。
