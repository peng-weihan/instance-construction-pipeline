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
    "id": "27_ninja_behavioral_port",
    "route": "M5",
    "repo": "ninja-build/ninja",
    "url": "https://github.com/ninja-build/ninja.git",
    "revision": "b81e306232dfa644e92145c7d2871690017969e8",
    "account": "raymone/5",
    "codex_home": "/ws/users/wcgu/new-codex-group/raymone/5",
    "expected_cli_sha256": "76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30",
    "scope_brief": "按ProgramBench构造真实Ninja核心构建系统的Rust行为兼容重实现，而不是几个flag。比较完整manifest/变量/rule解析、构建依赖与增量状态、depfile/dyndep/pool、response file、多步重建和工具命令的三个合理核心范围；从固定文档/源码/真实探针确定支持边界，目标需要完整状态与文件副作用兼容。gold可用于作者/学生观察，提交必须是真正Rust替代实现；此语言移植目标需在题面明确，不是事后为难度禁用所有库。正常工具/依赖允许，verifier执行考生时不提供可委托的目标ninja程序或原C++实现；参考与期望在可信侧独立获得。构建命令可正常调用编译器/脚本，不能误禁构建系统本来必须的subprocess。对比stdout/stderr/退出码/文件与第二次构建行为，并为可行partial提供固定分组。"
  },
  "route": {
    "name": "行为兼容重实现与语言移植",
    "factory": "ProgramBench + NL2Repo contract + controlled port/reimplementation boundary",
    "anchors": [
      "git_rewrite_in_zig",
      "libexpat_x86_assembly"
    ],
    "source_strategy": "选择真实CLI/库的完整核心行为：不仅参数与stdout，还包括文件/持久状态、错误和多步调用；冻结gold并独立探测。",
    "scope_strategy": "在明确的完整核心范围中交付真正的替代实现，允许正常依赖/工具。重实现目标本身需公开明确；参考可用于观察但不能作为待提交实现被直接委托。",
    "difficulty_strategy": "增加真实兼容面、状态交互、语法/文件格式和可观察错误路径；通过多步场景而非单条命令重复提高工程量。",
    "shortcut_probes": [
      "正常系统工具或成熟库薄包装",
      "目标二进制/完整原实现是否被直接委托",
      "只匹配输出未匹配退出码/文件/状态",
      "典型与未见输入的差分验证"
    ],
    "required_evidence": [
      "完整范围清单",
      "可运行gold",
      "多步独立差分输入",
      "明确合法依赖与真正重实现边界",
      "有代表性的独立强基线"
    ],
    "rejection": "只测几个flag、无真实状态验证、允许的薄包装已全部解决或合同靠临时禁库变难。",
    "original_tasks": [
      "git_rewrite_in_zig",
      "libexpat_x86_assembly"
    ],
    "original_count": 2,
    "public_count": 1
  }
}

本题特定的范围要求：
按ProgramBench构造真实Ninja核心构建系统的Rust行为兼容重实现，而不是几个flag。比较完整manifest/变量/rule解析、构建依赖与增量状态、depfile/dyndep/pool、response file、多步重建和工具命令的三个合理核心范围；从固定文档/源码/真实探针确定支持边界，目标需要完整状态与文件副作用兼容。gold可用于作者/学生观察，提交必须是真正Rust替代实现；此语言移植目标需在题面明确，不是事后为难度禁用所有库。正常工具/依赖允许，verifier执行考生时不提供可委托的目标ninja程序或原C++实现；参考与期望在可信侧独立获得。构建命令可正常调用编译器/脚本，不能误禁构建系统本来必须的subprocess。对比stdout/stderr/退出码/文件与第二次构建行为，并为可行partial提供固定分组。
