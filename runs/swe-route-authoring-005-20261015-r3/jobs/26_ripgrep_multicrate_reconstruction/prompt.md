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
    "id": "26_ripgrep_multicrate_reconstruction",
    "route": "M4",
    "repo": "BurntSushi/ripgrep",
    "url": "https://github.com/BurntSushi/ripgrep.git",
    "revision": "3fce3b5bb0236da2df6d99672afb8a719642eca7",
    "account": "raymone/4",
    "codex_home": "/ws/users/wcgu/new-codex-group/raymone/4",
    "expected_cli_sha256": "76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30",
    "scope_brief": "按DeepSWE A/B构造真正的多crate生产能力恢复，对照原Rust multicrate任务。先跑完整固定gold，再调查matcher/searcher/ignore/walk/CLI输出等子系统和依赖。比较三个连贯的大范围行为包，选择API契约、状态与端到端search场景共同支撑的缺失实现；不能只反转少量条件或删几个helper。保留类型/API骨架、周边健康路径、原生回归和跨层部分成果；逆补丁/完整gold私有。学生公开环境不得带回收站、git对象、reference wheel/binary或等价副本。成熟正常regex/encoding库可复用；实际强包装/重算方案若饱和就否定这个恢复合同。不要拿仓库总大小冒充学生工作量。"
  },
  "route": {
    "name": "跨模块或跨crate实现恢复",
    "factory": "DeepSWE A/B with coherent subsystem ablation",
    "anchors": [
      "rust_multicrate_reconstruction",
      "regex_automata_repair",
      "codeflash_repair_performance"
    ],
    "source_strategy": "从完整可验证产品的真实生产子系统及API/依赖图选择大范围行为包，保留干净gold和原始测试。",
    "scope_strategy": "恢复可独立说明的多个生产模块/层次及其集成，保留接口骨架和可工作的周边；不是只反转几个条件。",
    "difficulty_strategy": "首先保证缺失的真实工程量；再考虑共享数据模型、跨crate契约、异常和资源生命周期。既有回归与局部进度同时保留。",
    "shortcut_probes": [
      "上游完整实现是否藏在git/缓存/构建产物",
      "正常库组合/外部工具等价方案",
      "绕过恢复点的full-reparse/重算路径",
      "单个通用补丁是否同时解决全部缺口"
    ],
    "required_evidence": [
      "完整gold健康性",
      "行为级消融与求逆",
      "缺失能力/保留能力图",
      "F2P/P2P和跨层partial",
      "公开资产答案隔离"
    ],
    "rejection": "少量谓词恢复、缺口只是重复适配、原生快捷路径满分或全仓不可工作且无局部反馈。",
    "original_tasks": [
      "rust_multicrate_reconstruction",
      "codeflash_repair_performance",
      "regex_automata_repair"
    ],
    "original_count": 3,
    "public_count": 1
  }
}

本题特定的范围要求：
按DeepSWE A/B构造真正的多crate生产能力恢复，对照原Rust multicrate任务。先跑完整固定gold，再调查matcher/searcher/ignore/walk/CLI输出等子系统和依赖。比较三个连贯的大范围行为包，选择API契约、状态与端到端search场景共同支撑的缺失实现；不能只反转少量条件或删几个helper。保留类型/API骨架、周边健康路径、原生回归和跨层部分成果；逆补丁/完整gold私有。学生公开环境不得带回收站、git对象、reference wheel/binary或等价副本。成熟正常regex/encoding库可复用；实际强包装/重算方案若饱和就否定这个恢复合同。不要拿仓库总大小冒充学生工作量。
