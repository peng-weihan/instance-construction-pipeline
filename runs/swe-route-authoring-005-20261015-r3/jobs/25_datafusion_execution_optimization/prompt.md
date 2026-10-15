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
    "id": "25_datafusion_execution_optimization",
    "route": "M3",
    "repo": "apache/datafusion",
    "url": "https://github.com/apache/datafusion.git",
    "revision": "10343c18292fc3a9ca62b59c8bb530169fe79b82",
    "account": "raymone/6",
    "codex_home": "/ws/users/wcgu/new-codex-group/raymone/6",
    "expected_cli_sha256": "76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30",
    "scope_brief": "从真实DataFusion执行链筛一个完整的性能任务：多分区/TopK/merge/spill/内存协调、不同数据分布或算子交互，至少比较三个真实瓶颈。不是给旧sort题启用随意公式，更不能仅保留identity fast path。上一版正确性starter=reference=0.25，0.75性能关闭；已有正确input-order metadata会让SortExec跳过有序输入，这个强B必须保留。先证明普通batch/阈值/metadata/已有算法组合之上仍有真实收益，再冻结独立性能奖励、目标资源和代表性workload。性能奖励若不能稳定闭合则明确held，不交可roll/可训练状态；禁止为了造难选弱B或只挑参考占优数据。可以只读复用我们自己的固定material-src/vendor构建材料并复制入当前job，禁止依赖旧job的私有答案作为学生可见素材。"
  },
  "route": {
    "name": "正确性约束下的系统性能优化",
    "factory": "DeepSWE source/refactor discipline + ProgramBench differential checks + dedicated performance controller",
    "anchors": [
      "ann_vector_search_qps",
      "exchange_core_throughput",
      "integer_compression_codec",
      "ffmpeg_swscale_reimplementation",
      "vliw_kernel_optimization"
    ],
    "source_strategy": "从真实端到端workload、profile、性能回归与公开强配置发现瓶颈。先做调参/metadata/普通库基线，再寻找其上的收益。",
    "scope_strategy": "优化完整执行链或有深度的核心算法，不按文件数强行扩展。代表性负载覆盖真正相互牵制的分布、规模、资源和算法路径。",
    "difficulty_strategy": "提高算法/表示/资源取舍的深度。先证明可达增益明显超过噪声，并检查简单dispatch/配置是否吞掉空间。",
    "shortcut_probes": [
      "最强普通配置与已有metadata",
      "现成高性能库和简单混合dispatch",
      "同快照配对重放/独立计时",
      "缓存固定结果能否绕过任务真实目标"
    ],
    "required_evidence": [
      "正确性oracle",
      "强起点与真实可达参考",
      "独立测量和资源契约",
      "启用且有公式/锚点的性能奖励",
      "代表性在线候选重复评分"
    ],
    "rejection": "性能奖励禁用、starter已达有效上限、波动可解释收益或强普通基线已支配。不得弱化基线或只挑参考占优负载。",
    "original_tasks": [
      "ann_vector_search_qps",
      "exchange_core_throughput",
      "ffmpeg_swscale_reimplementation",
      "integer_compression_codec",
      "notebook_lossless_compression",
      "vliw_kernel_optimization"
    ],
    "original_count": 6,
    "public_count": 5
  }
}

本题特定的范围要求：
从真实DataFusion执行链筛一个完整的性能任务：多分区/TopK/merge/spill/内存协调、不同数据分布或算子交互，至少比较三个真实瓶颈。不是给旧sort题启用随意公式，更不能仅保留identity fast path。上一版正确性starter=reference=0.25，0.75性能关闭；已有正确input-order metadata会让SortExec跳过有序输入，这个强B必须保留。先证明普通batch/阈值/metadata/已有算法组合之上仍有真实收益，再冻结独立性能奖励、目标资源和代表性workload。性能奖励若不能稳定闭合则明确held，不交可roll/可训练状态；禁止为了造难选弱B或只挑参考占优数据。可以只读复用我们自己的固定material-src/vendor构建材料并复制入当前job，禁止依赖旧job的私有答案作为学生可见素材。
