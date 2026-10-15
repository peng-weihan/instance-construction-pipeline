# 调研范围与计划

用户确认：重点研究任务模板与批量新实例生成，而非只复现既有题目。

输出：中文研究报告、公开51题逐题分类CSV、完整134题领域/公开性索引、论文与官方数据快照、可复用的实例设计蓝图。

追加范围：根据用户后续指示，将 `/Users/raymone/Desktop/01_Research/swe-factory` 完整复制到 `upstream/swe-factory`，分析 NL2Repo、DeepSWE A/C/B、ProgramBench 的实例构造、验题、交付与复用边界。三位模块分析员分别复核一条工厂链；原目录和复制的源码、原始规约、历史运行证据保持原样。

分析范围以问题为中心：任务组成与可生成机制、work/judge/score契约、相关基准的实例生成方法；不分析GUI可视化和模型接入实现。标准源码分析用于核心契约，不以全仓库覆盖为目标。

并行分工（repo-analyzer 技能要求）：
- task_taxonomy：51条任务定义，统计、机制分类、可生成轴、资产公开性。
- harness_design：TaskSpec、评分、选择、容器化提交契约与集成指南。
- generation_methods：Reasoning Gym、ALE-Bench、RE-Bench、MLE-bench的一手论文及造题方法。
- 主分析：EdgeBench论文、完整134题索引、源文件归档、结论交叉核验与报告整合。

报告逻辑：官方领域分类 → 为生成而设的机制分类 → family/instance/case三层单位 → 生成路线与三种首批模板 → 验题、难度及泛化协议 → SForge落地与实施顺序。
