# 素材 → 题目

真实素材：Microsoft RESTler 的固定 revision；三个核心文件、调用者、设置和文档均已落盘。MIT 许可证保留在 public/repo/LICENSE.txt 或上游现有许可证路径。

变换：从 Python AST 选取 9 个完整函数，保留签名与 docstring，删除实际实现。精确行段、移除行数见 private/ablation_manifest.json，完整参考源码见 private/reference。使用 DeepSWE 的“完整功能→消融→私有恢复依据”，借用 NL2Repo 的 AST 契约提取；没有假称运行了三个 factory 的完整控制器。

难度来自异步状态机、跨请求依赖、缓存与 GC 的协同，不来自随机删行。24 个行为检查已具名；还需要把检查实现成隔离的固定时钟/伪 transport 测试，覆盖与长程难度未校准。私有上游测试是出题依据，不能直接当作已验证 oracle。原 benchmark 的代码/数据未用于生成此任务；完整跨库重合检查仍待后续。
