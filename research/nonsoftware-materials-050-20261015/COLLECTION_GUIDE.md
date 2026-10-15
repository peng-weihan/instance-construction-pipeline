# 另外五类任务的50份新素材

目标：科学与ML S01–S10、组合优化 O01–O10、形式数学 F01–F10、专业知识 K01–K10、游戏/模拟 G01–G10，各10个独立主来源。下述字段服务后续构题，不声称已构题/运行/校准难度。

优先新来源，排除已登记 MODFLOW、Harmonica、OGB、ESICUP、Homberger、Ken French、brownian-motion、Wesnoth、microRTS、IF Archive目录和已有NeurIPS2021单细胞来源。可以共享基础库，但不能把同一数据集/项目的10个seed或文件计为10个素材。原EdgeBench任务已用领域/引擎须显式列谱系风险；不把换题面视为独立新题。

分类看产物和评分：科学ML交模型/预测/反演；组合优化交可行解与质量；形式数学交内核可检的证明；专业知识交领域分析/计划与证据链；游戏交策略/交互表现。即使要写代码也不因此归软工。

固定版本：优先官方Git仓库，用本目录acquire_sources_v2.py保存固定commit、完整文件树、定向选读实现/测试或规格/许可。--repo owner/repo --id s01_slug --list REGEX先定位，再--files实际路径。GitHub canonical迁移核对。大型数据/模型不整包下载；明确仅元数据、生成器和小fixture已取，大数据/完整环境未取。网页来源须保存正文及URL/日期/hash，不能只有链接。

每项JSON字段（统一英文keys、中文正文）：
id, category (science/optimization/formal/knowledge/games), name, repo, revision, source_manifest ('sources/id/manifest.json'), source_unit, title, proposed_task, deliverable, difficulty_sources (至少2条因果), baseline, first_probe, stop_condition, grader_plan, generation_and_split, novelty_and_overlap, offline_and_compute, license_observation, evidence (至少2条{path:'sources/id/files/...',line:正整数,claim,url}), read_scope (至少实现和测试/规格两段{path,start,end,kind}), potential (high/medium/unclear), priority (scope_probe/hold_baseline/hold_reference/hold_data/hold_license), card ('cards/id.md'), task_constructed:false, runtime_verified:false, difficulty_verified:false。

每张卡宜20–35行，包含固定版本、资料范围、具体任务/交付、为什么难、正常基线和淘汰探针、独立评分、数据生成/划分与防简单泄漏、许可与离线风险、2–4个证据链接。优先级必须诚实，不为凑数全部推荐。难度不靠禁库、无意义大规模或等待。形式数学不能只删一个已有定理body而import仍可直接调用；公开proof与同义定理检索/污染要评估。专业任务不要全塞金融，要覆盖多个领域，且不把通用工具当具体数据任务。

增量写对应drafts/<category>.json及cards；单次不超过300行/15KB。完成每组后写drafts/<category>.md，列实际选读文件行区间（不是全仓覆盖；不虚构百分比），主分析最终抽查关键结论。所有分组完成后才合并。
