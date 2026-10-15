# 六类任务的构造与打包

这里维护本批六个任务的实际参考实现和评分器。它是当前 agent 完成领域设计后的可复现构造配方；不声称仅靠规则脚本就能自主挖掘并设计下一批高质量难题。

最新构造结果：[built-007](../samples/long-horizon-built-007/README.md)。评分器从随题机器可读元数据加载评分常量；静态检查核对设计说明、评分元数据、文件清单、构建上下文与预算覆盖。这些检查不执行候选程序或评分器。

`components/` 按领域保存普通源文件；`assemble.py` 从固定素材候选生成新目录，补齐参考解、具体检查、题面、评分元数据、提交工具及两个独立环境的构建上下文。旧目录不会被覆盖。

```bash
.venv/bin/python task_factory/assemble.py --output samples/long-horizon-built-NNN
.venv/bin/python task_factory/inspect_package.py samples/long-horizon-built-NNN
.venv/bin/python task_factory/review_authoring.py samples/long-horizon-built-NNN
```

以上只执行构造和静态检查，不调用模型、不运行参考解/评分器、不构建 Docker。`base_image.lock.json` 是从官方 registry 获取的多架构 manifest 摘要。镜像构建时再获取编译器和依赖，记录实际版本；双架构运行、重建一致性和评分确定性仍需后续验证。

领域分工：

- 软件：参考实现接入真实 RESTler 设置、请求发送与异步路径；工作流接入动态依赖登记。可信控制器负责故障响应、时间和 transport 记录，避免仅采信被测进程报告的通过率。
- 科学：稀疏算子前向参考和读取公开观测的反演程序；评分器只接收参数，不执行候选推断代码。
- 排样：真实求解器参考、构建期冻结布局、独立 polygon/holes 几何核验。当前参考同基线，不能当作已证实的强 oracle。
- Lean：精确证明体边界、保留原证明、重新构建与传递公理检查。编译和依赖难度尚未运行核实。
- 金融：因果 JSON-lines 政策接口、独立成本/现金/持仓账本、约束核验和有实际优化工作的参考政策。
- 游戏：固定 Wesnoth 引擎和可信 CA，纯 Lua 策略选择合法动作；参考策略执行招募、占村和攻击排序。

已读取远端 Harbor 0.23.0 适配契约，当前产物 `task.toml` 仍为本地契约，尚待原生接入。市场价格和工业设计数据的再分发授权仍是正式训练交付门槛；当前包用于本地构造审阅。软件类已完成直接 Docker 参考与 starter 评分（1.0 / 0），见独立远端验证报告；Harbor 原生 Oracle/NOP、本批模型分数和六小时曲线仍未测。

`authoring_profiles.json` 记录六类素材来源、准入规则、构造方法、原题对应关系与反例设计。`review_authoring.py` 核对已登记来源的版本和关键文件摘要，生成逐题出题复核；不执行反例或宣称任务同分布。
