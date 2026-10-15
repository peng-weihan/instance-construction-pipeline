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
    "id": "24_lark_system_reconstruction",
    "route": "M2",
    "repo": "lark-parser/lark",
    "url": "https://github.com/lark-parser/lark.git",
    "revision": "9a4fb9c7458e8155636773a3cded0016d52516da",
    "account": "raymone/5",
    "codex_home": "/ws/users/wcgu/new-codex-group/raymone/5",
    "expected_cli_sha256": "76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30",
    "scope_brief": "按NL2Repo方法，从完整可运行Lark参考项目抽出足以重建实质解析工具库/引擎的规格。优先完整的grammar→lexer→parser→tree/visitor/transformer→错误/集成工作链，调查LALR/Earley、文法组合、树转换、位置/错误等真实API；不能只做JSON parser或几个toy表达式。比较三个合理完整系统范围，选择足够大的可运行契约且保留局部进度，不要求完整复刻上游全部可选生态。参考是固定真实源码，不能让模型另造toy gold。学生不见目标实现、git对象、wheel/字节码或副本；正常第三方解析工具不因难度被临时禁止，若包装就完整解决合同则如实否证。工作区是新规格与骨架/空项目，参考不可误装到agent环境。"
  },
  "route": {
    "name": "按规格构建完整系统能力",
    "factory": "NL2Repo + independent specification/reference review",
    "anchors": [
      "arc_compiler_runtime",
      "dependent_type_checker",
      "postgres_wire_on_sqlite",
      "stream_processing_engine"
    ],
    "source_strategy": "从许可明确且可运行的完整语言工具、查询/协议引擎、服务库抽取公开API、状态语义、错误与集成规格；参考来自固定真实实现。",
    "scope_strategy": "任务是完整库/引擎或明确的大型子系统，给规格/依赖/骨架，隐藏目标实现及其副本。覆盖解析/语义/执行或协议/状态/持久化等真实工作链。",
    "difficulty_strategy": "工程广度与核心算法共同增加；通过自然的部分实现支持局部验证，避免全局编译门控导致长期零分。",
    "shortcut_probes": [
      "已安装目标包或源码/字节码副本泄漏",
      "成熟第三方库或系统工具能覆盖多少",
      "简单解释器/最小协议实现的实际覆盖"
    ],
    "required_evidence": [
      "完整行为规格与API清单",
      "规格到参考/独立测试映射",
      "可冻结的中间能力",
      "目标实现隔离与正常依赖边界"
    ],
    "rejection": "仅几个API的玩具替代、规格不足、完整目标实现可直接导入，或无可行partial。",
    "original_tasks": [
      "arc_compiler_runtime",
      "dependent_type_checker",
      "high_performance_object_mapper",
      "juliet_vulnerability_analyzer",
      "odata_query_service",
      "lua_native_compiler",
      "postgres_wire_on_sqlite",
      "quic_transport_stack",
      "stream_processing_engine",
      "tls13_handshake_state_machine",
      "cpu_full_flow",
      "cfzip_compression_engine"
    ],
    "original_count": 12,
    "public_count": 2
  }
}

本题特定的范围要求：
按NL2Repo方法，从完整可运行Lark参考项目抽出足以重建实质解析工具库/引擎的规格。优先完整的grammar→lexer→parser→tree/visitor/transformer→错误/集成工作链，调查LALR/Earley、文法组合、树转换、位置/错误等真实API；不能只做JSON parser或几个toy表达式。比较三个合理完整系统范围，选择足够大的可运行契约且保留局部进度，不要求完整复刻上游全部可选生态。参考是固定真实源码，不能让模型另造toy gold。学生不见目标实现、git对象、wheel/字节码或副本；正常第三方解析工具不因难度被临时禁止，若包装就完整解决合同则如实否证。工作区是新规格与骨架/空项目，参考不可误装到agent环境。
