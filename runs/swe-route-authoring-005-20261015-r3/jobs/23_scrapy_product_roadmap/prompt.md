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
    "id": "23_scrapy_product_roadmap",
    "route": "M1",
    "repo": "scrapy/scrapy",
    "url": "https://github.com/scrapy/scrapy.git",
    "revision": "db2404bb8691d1579f75ca823d5385749b77693c",
    "account": "raymone/4",
    "codex_home": "/ws/users/wcgu/new-codex-group/raymone/4",
    "expected_cli_sha256": "76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30",
    "scope_brief": "构造真实Scrapy产品级roadmap，不能只实现一个持久化journal/重试插件。调查完整crawler engine、调度/请求身份、下载/中间件、item/feed管线、配置与报告之间的真实需求或退化；至少比较三个产品里程碑范围。可在完整固定旧版本上提出新需求，也可在验证过的完整版本上恢复一整组子系统，但必须诚实区分已有能力与新缺口。最终应是多组实质产品能力和跨阶段回归，规模对照原Schemathesis 5～8目标roadmap而非凑相同目标数。服务测试全部本地fixture，不抓真实外网网站。正常现成插件基线若已全解则改选有源码/需求证据的范围。"
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
构造真实Scrapy产品级roadmap，不能只实现一个持久化journal/重试插件。调查完整crawler engine、调度/请求身份、下载/中间件、item/feed管线、配置与报告之间的真实需求或退化；至少比较三个产品里程碑范围。可在完整固定旧版本上提出新需求，也可在验证过的完整版本上恢复一整组子系统，但必须诚实区分已有能力与新缺口。最终应是多组实质产品能力和跨阶段回归，规模对照原Schemathesis 5～8目标roadmap而非凑相同目标数。服务测试全部本地fixture，不抓真实外网网站。正常现成插件基线若已全解则改选有源码/需求证据的范围。
