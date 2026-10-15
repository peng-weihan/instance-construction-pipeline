# 类别专用长程软工构造


本轮任务是造出具有足够真实工程量/优化深度的长程软工题，不是把一个小特性包装成大仓库题。
依次完成 MATERIAL_MINING.json → SCOPE_CARD.json → REQUIREMENTS.json → task/ → AUTHOR_RESULT.json。
先阅读 guidance 中三套factory原始规约、原EdgeBench分类/尺度报告、开发机作者规范。
原EdgeBench素材仅供作者理解类型和尺度，不复制其题面/测试/答案到训练环境。

1. 素材：完整获取固定revision、许可、文档、原生测试，保存哈希。审阅至少三个有真实来源的候选范围，逐项记录已有能力、真正缺失的交付、普通强基线、探针、保留/否定理由。只换同一窄feature的三个参数不算三个范围。
2. 工程范围：列出目标系统边界、所有核心交付能力、公开API/生产模块、共享状态及端到端场景。必须说明学生得到什么、还要实现什么；作者写grader/下载依赖/等待编译不计求解工程量。参考原题产品roadmap、完整引擎、多crate恢复、兼容重建，禁止静默收缩成一个helper/journal/retry。
3. 参考和题面：先得到完整可运行的真实参考与清晰可实现合同，再构造starter/规格。产品roadmap应有多组实质目标；系统重建保留正常依赖但不暴露目标实现；消融保留完整gold/求逆/回归，不只删几个条件。模块/LOC/检查数量只描述规模，不能自动宣称难度。
4. 便宜否证：实际测试最强正常工具、配置、库组合和包装。独立方案与gold mutation分开。若合理捷径已饱和，换真正的需求范围或拒绝该候选，不能临时禁库、减弱基线、加无关case/等待或改旧奖励。
5. 评分：公开任务/权重/分母，独立结构化valid/score/checks/raw metrics；原生reward与周期score同一权威值。每项得分对应真实交付，部分实现可局部验证；可使用功能覆盖，不强迫所有题加性能。性能题先做强基线、代表性负载、独立计时、在线候选配对重评；未启用性能或starter达当前上限只能held，不能交“可训练完整题”。
6. 构造：独立agent/verifier构建上下文，公开仅starter/契约/开发反馈，私有参考/评分器/保留集。交完整task.toml、instruction、Dockerfiles、solution、tests、来源/许可/依赖清单、真实控制记录。运行都在当前job下；禁止全局安装、共享配置/daemon操作、清理别人的文件。每个构建最多-j4。
7. SCOPE_CARD遵循guidance/scope-card.schema-example.json。所有evidence是当前job内的实际文件和SHA256；至少包含starter/reference/independent_baseline控制的真实结构化结果。若只是语义探针，标注probe_only，不冒充同一完整grader分数。执行swe gate --job当前目录只得到静态检查，不得称难度/运行验收。
8. 两条后期改进路径必须写具体能力、前置成果、可冻结产物和原始指标变化；不能承诺必需几小时。作者同时写gold/测试存在偏差，独立审查在之后进行。
9. 用户本轮仅授权出题；不得启动教师、云实例、其他模型/CLI agent/子代理，不改已有题和轨迹。实际作者使用gpt-6.1-sol。拒绝/hold是有效结果，但不能因第一个小合同失败就不再调查其他真实范围。


{
  "source": {
    "id": "28_scrapy_complete_r2",
    "route": "M1",
    "repo": "scrapy/scrapy",
    "url": "https://github.com/scrapy/scrapy.git",
    "revision": "db2404bb8691d1579f75ca823d5385749b77693c",
    "account": "raymone/4",
    "codex_home": "/ws/users/wcgu/new-codex-group/raymone/4",
    "expected_cli_sha256": "76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30",
    "scope_brief": "保留六组真实产品能力的完整范围。在新副本独立检查公开契约是否足以解释原生测试的内部结构假设、候选是否能伪造测试输出/修改结果文件，然后实际修复题包和可信评分边界。完整参考、starter、正常插件/包装基线及至少两份真实partial重放。完成独立agent/verifier镜像以及原生Harbor Oracle/NOP和同快照partial双入口验证。已有253用例、参考1.0、B约0.39只是作者旧主机证据，不能照抄为新镜像结果。若范围仍像小feature，依据固定源码扩大真正产品目标并明确新题版本，而不是加同构测试。",
    "source_job": "/ws/users/raymone/edgebench/swe-route-authoring-005-20261015-r3/jobs/23_scrapy_product_roadmap",
    "work_kind": "repair_and_complete_new_copy"
  },
  "route": {
    "name": "产品级多目标演进",
    "factory": "DeepSWE C + NL2Repo specification extraction",
    "anchors": [
      "schemathesis_datagen_pipeline",
      "schemathesis_config_modernization",
      "schemathesis_reporting_observability"
    ],
    "source_strategy": "从真实版本roadmap、多个关联PR/issue、原生接口和集成回归中提取一个完整产品里程碑。先核对已有能力，不把已有功能说成新需求。",
    "scope_strategy": "交付完整产品路线：多组真实能力、共享配置/状态、端到端兼容与错误路径。相对独立但有实际产品价值的目标可以保留。不能收缩成一个retry、journal或helper。",
    "difficulty_strategy": "先增大真实工程覆盖，再增加跨模块设计与兼容难点。需求数量和代码行数只是描述，不自动作为难度门槛。",
    "shortcut_probes": [
      "原生默认配置/公开插件",
      "最强合法包装与小规模配置修改",
      "既有版本是否已完整实现"
    ],
    "required_evidence": [
      "完整产品需求矩阵",
      "已有与缺失能力清单",
      "生产模块与集成场景对应",
      "普通包装和原生起点实测"
    ],
    "rejection": "一项窄扩展覆盖了全部需求，或普通配置/插件已饱和；不要禁用合理工具挽救。",
    "original_tasks": [
      "copier_modular_refactor",
      "entt_graph_module",
      "litestar_infra_refactor",
      "mimesis_modular_refactor",
      "nlohmann_json_modularization",
      "packer_plugin_datasources",
      "pocketbase_backend_architecture",
      "pocketbase_tools_extensions",
      "schemathesis_datagen_pipeline",
      "schemathesis_reporting_observability",
      "schemathesis_config_modernization",
      "vault_sdk_resilience",
      "zstd_api_modernization"
    ],
    "original_count": 13,
    "public_count": 3
  }
}

本题特定的范围要求：
保留六组真实产品能力的完整范围。在新副本独立检查公开契约是否足以解释原生测试的内部结构假设、候选是否能伪造测试输出/修改结果文件，然后实际修复题包和可信评分边界。完整参考、starter、正常插件/包装基线及至少两份真实partial重放。完成独立agent/verifier镜像以及原生Harbor Oracle/NOP和同快照partial双入口验证。已有253用例、参考1.0、B约0.39只是作者旧主机证据，不能照抄为新镜像结果。若范围仍像小feature，依据固定源码扩大真正产品目标并明确新题版本，而不是加同构测试。


本批执行补充（用户已明确要求同时10条出题，以下取代旧提示中不完整的操作边界）：
- 本会话是明确授权的gpt-6.1-sol原生CLI作者。完成素材、题面、完整参考、可信评分器和可运行题包；不要把计划当交付，也不要因为允许held而跳过可修复工程缺口。
- 允许当前job内正常构建/测试，以及有唯一job标签的独立Docker agent/verifier镜像构建和model-free Oracle/NOP/partial Harbor检查。禁止启动任何教师模型、额外CLI agent、子代理、云沙箱；禁止修改共享daemon、共享镜像tag、原始skill/旧题包/其他job。Docker容器不能挂载账号目录或docker.sock。
- work/judge分开；评分服务不是常驻；所有得分完全取自文件快照。评分常量、分母、权重机器可读，native reward与周期score同权威。环境依赖要闭合，留意此前Sphinx缺git、正式CLI缺strace的教训，不把依赖异常写0分。
- 作者本地跑的控制是构造证据，不是6h模型难度证据。初始旧SWE题出现3.5～14分钟满分；因此真正在题目里增加完整系统能力与兼容面，不靠等待、加同构case、降低B或重映射历史分数。
- 保护评分权威：私有expected/断言不与candidate在同一个解释器内；不能信candidate打印的pass计数/worker成功帧。编译/导入/执行均按不可信候选降权、隔离私有数据，可信侧比较实际行为。添加打印伪造成功、读取已知私有路径、写reward、残留子进程等针对性控制，并留真实证据。
- 构建最多-j2/CARGO_BUILD_JOBS=2；每次大编译/镜像前检查磁盘。不要拷贝旧target/build/cache/虚拟环境；从固定源码和依赖重建。独立使用自己的输出/镜像/容器，无全局prune。旧素材可只读参考，需闭包复制到本题才能计交付。
- 对普通任务交完整合法参考，而不是用不符合语言/约束的上游gold冒充满分solution。开放优化题可按规范声明open-solution并交可运行强参考/真实分值；不能人为拉到1.0。
- 输出完成/缺口均给明确可执行下一步和证据；不把静态gate通过写accepted。没有ARM/6h证据就写未验证。

本题是返修新版本。旧输入只读：/ws/users/raymone/edgebench/swe-route-authoring-005-20261015-r3/jobs/23_scrapy_product_roadmap。部署后当前job下 previous-input/ 是不含构建缓存的素材/题包副本，之前的报告只作历史输入。请先读 previous-input/AUTHOR_RESULT.json、SCOPE_CARD.json、REQUIREMENTS.json、task/instruction.md，建立 REPAIR_PLAN.json。保留previous-input不变，在当前job/task及其他当前输出创建新版本；不得修改旧job。逐项解决本题scope_brief中的缺口，再重放实际控制。复制进来的旧成功报告不可冒充本轮执行。

先读 /ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/guidance 下的作者规范、三套factory原始规约、范围要求、actual Harbor schema。源码语义以固定revision为准；新仓库至少先比较三个完整范围。静态检查：PYTHONPATH=/ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/controller python3 -m edge_factory.swe gate --job /ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/jobs/28_scrapy_complete_r2 --output /ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/jobs/28_scrapy_complete_r2/STATIC_ADMISSION.json 。它不能代替真实运行。可只读参考 /ws/users/raymone/edgebench/swe-rollouts-005-20261015-r5/framework 中的实际Harbor/独立判分代码，在本题复制需要的无凭据部分后使用；不要写入那里的运行目录。
