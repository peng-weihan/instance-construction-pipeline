# 六类题目的“素材 → 任务”小样

当前交付回答两个问题：**能获取什么真实出题素材；怎样把这些素材变成有具体工作内容的题目。** 共六题，每类一题。所有题均为 `constructed_unverified`，不含解题轨迹、运行成绩或 Harbor 验收结论。

| 类别 | 实际取得的素材 | 已构造的任务 | 可直接审阅 |
|---|---|---|---|
| 系统与软件工程 | Microsoft RESTler 固定源码、调用者、设置、上游测试 | 恢复异步轮询、create-once 与缓存保存的完整生命周期；9 函数、324 行实现被消融 | [题面](restler_resource_lifecycle/public/instruction.md) · [素材变换](restler_resource_lifecycle/SOURCE_TO_TASK.md) |
| 科学问题与 ML | MODFLOW 3D 输运示例与解析模型说明；独立构造的前向模型和观测 | 14 参数有限时长方体污染源反演；108 条公开观测、96/180 条私有目标 | [题面](finite_release_groundwater_inverse/public/instruction.md) · [素材变换](finite_release_groundwater_inverse/SOURCE_TO_TASK.md) |
| 组合优化 | PackingSolver 源码、OpenCutList 真实非凸零件 | 改进通用条带排样算法；9 组设计、每组 8–100 件，公开/反馈/最终按设计族划分 | [题面](industrial_irregular_strip/public/instruction.md) · [素材变换](industrial_irregular_strip/SOURCE_TO_TASK.md) |
| 专业知识工作 | French 官方 49 行业日收益，固定 202608 数据版本 | 八份组合委托的滚动风险校准；公开 6,553 行，私有 1,006/1,508 行 | [题面](industry_portfolio_risk_lab/public/instruction.md) · [素材变换](industry_portfolio_risk_lab/SOURCE_TO_TASK.md) |
| 形式化数学 | BrownianMotion 完整证明库、Lean 依赖锁文件、数学背景 | 补全 Hölder 连续修正链的 16 个证明，移除约 440 行证明体 | [题面](kolmogorov_holder_modification/public/instruction.md) · [素材变换](kolmogorov_holder_modification/SOURCE_TO_TASK.md) |
| 游戏与模拟器 | microRTS 真实引擎、Java API、策略样例 | 构造资源竞争机器人；9 张新地图、4 类对手、双座位配对评分设计 | [题面](microrts_resource_frontier/public/instruction.md) · [素材变换](microrts_resource_frontier/SOURCE_TO_TASK.md) |

## 怎么审阅

每题的 `public/` 已有实际起始材料和题面。`private/` 是出题方持有的参考源码、完整证明、生成真值、后续时间数据或私有场景，**不能将整个任务目录挂载给解题 agent**。`construction.json` 记录来源 URL、完整 revision、关键文件 SHA、构造方法、与原题的差异；`file_manifest.json` 对整个任务包逐文件固定摘要。

`public/evaluation_contract.draft.json` 明确提交文件、3 小时预算、快照评分、无状态 verifier、有界分数公式、具名反馈、取历史最好提交等设计。它是本地出题草案，未伪装成尚未收到正式 schema 的 `task.toml`。最终 Harbor 映射、双环境构建和依赖闭包在下一阶段补齐。

## pipeline 已走到哪里

本批实际执行了：官方来源获取 → 固定源码/原始数据 → 阅读功能/数学/领域结构 → 选取工作单元 → 消融、目标转换、观测生成或时间切分 → 公开/私有材料分包 → 题面与评分设计 → 静态材料清点。

可重放构造配方是 [construct_category_samples.py](../../scripts/construct_category_samples.py)，需使用本批锁定的材料版本，输出必须为新目录。构造器只做文件处理与合成观测生成，不执行任务求解或验收。`category-pilot-001`、`002` 保留构造失败产物，`003` 为修订前草稿；本批交付使用 `004`，并将 knight_body / knight_armor 归到同一最终分区。这次没有另起 CLI 模型，出题语义由当前交互 agent 阅读材料后制定，脚本负责可重放变换。不能把这个脚本称为已完成的自动候选挖掘/自主出题 agent。

参考三套 factory 的具体部分：RESTler 与 Lean 使用 DeepSWE 的完整功能消融/私有恢复依据；优化与游戏使用 ProgramBench 的固定参考源码和接口契约；各题采用 NL2Repo 的结构提取、题意与接口绑定以及公开/私有拆分。没有调用它们的 Docker、Oracle 或验收流程。后续规模化需要 constructor agent 来选择依赖闭合且有意义的工作单元，规则脚本负责固定版本、搬运、变换和检查，不能仅凭一个随机 seed 扩充题数。

## 本轮结论与仍需补足的材料

六类都找到了可落盘的素材，也都形成了有具体操作对象的题目。软件和数学有现成完整实现/证明作为参考；科学题有自定义前向模型和生成真值；优化和游戏有真实引擎；专业题有真实时间序列和可计算指标。

材料可获得不等于训练使用权已全部解决：French/CRSP 数据、OpenCutList 零件数据及 MODFLOW 示例的再分发声明仍需核对；其余也应随交付保留许可证，microRTS 是 GPL-3.0。此批用于本地小样审阅，不能直接标成已清权训练发行包。

“原题相近”目前是机制层面的设计判断。科学题采用新的无限域模型，游戏更换了引擎，专业任务尚未读到原镜像内完整题面；这些差异均逐题记录。未验证原 benchmark 的完整隐藏材料重合，未证明相同难度或 3 小时学习曲线。按当前要求，未运行解题模型、Lean/CMake/Java 构建、回测、比赛或评分器。

完整清点见 [index.json](index.json) 和 [material_inventory_check.json](material_inventory_check.json)。后者仅检查文件、摘要、接口文本、数据分割和地图格式，不能当作运行验证。
