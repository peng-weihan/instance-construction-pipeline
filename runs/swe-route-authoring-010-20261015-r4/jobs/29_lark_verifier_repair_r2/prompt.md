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
    "id": "29_lark_verifier_repair_r2",
    "route": "M2",
    "repo": "lark-parser/lark",
    "url": "https://github.com/lark-parser/lark.git",
    "revision": "9a4fb9c7458e8155636773a3cded0016d52516da",
    "account": "raymone/5",
    "codex_home": "/ws/users/wcgu/new-codex-group/raymone/5",
    "expected_cli_sha256": "76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30",
    "scope_brief": "最高优先级修复零实现可打印worker成功帧获得1.0的已复现评分漏洞。参考、私有期望、比较逻辑必须在可信父进程/隔离空间；不把私有断言和预期放进候选解释器，不相信候选自报pass/fail。把旧exploit复制为必须失败的回归，增加合法行为相同的正确实现/真实partial控制，防止只按输出标记或文件名封堵。保留完整grammar→lexer→parser→tree/transformer→组合/诊断合同，不通过删难测能力缩小任务。复查普通库包装0.72的剩余工程空间。完成可信行为评分、完整题包及镜像/原生双入口控制；源码/测试/包内git和字节码不得漏出目标实现。",
    "source_job": "/ws/users/raymone/edgebench/swe-route-authoring-005-20261015-r3/jobs/24_lark_system_reconstruction",
    "work_kind": "repair_and_complete_new_copy"
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
最高优先级修复零实现可打印worker成功帧获得1.0的已复现评分漏洞。参考、私有期望、比较逻辑必须在可信父进程/隔离空间；不把私有断言和预期放进候选解释器，不相信候选自报pass/fail。把旧exploit复制为必须失败的回归，增加合法行为相同的正确实现/真实partial控制，防止只按输出标记或文件名封堵。保留完整grammar→lexer→parser→tree/transformer→组合/诊断合同，不通过删难测能力缩小任务。复查普通库包装0.72的剩余工程空间。完成可信行为评分、完整题包及镜像/原生双入口控制；源码/测试/包内git和字节码不得漏出目标实现。


本批执行补充（用户已明确要求同时10条出题，以下取代旧提示中不完整的操作边界）：
- 本会话是明确授权的gpt-6.1-sol原生CLI作者。完成素材、题面、完整参考、可信评分器和可运行题包；不要把计划当交付，也不要因为允许held而跳过可修复工程缺口。
- 允许当前job内正常构建/测试，以及有唯一job标签的独立Docker agent/verifier镜像构建和model-free Oracle/NOP/partial Harbor检查。禁止启动任何教师模型、额外CLI agent、子代理、云沙箱；禁止修改共享daemon、共享镜像tag、原始skill/旧题包/其他job。Docker容器不能挂载账号目录或docker.sock。
- work/judge分开；评分服务不是常驻；所有得分完全取自文件快照。评分常量、分母、权重机器可读，native reward与周期score同权威。环境依赖要闭合，留意此前Sphinx缺git、正式CLI缺strace的教训，不把依赖异常写0分。
- 作者本地跑的控制是构造证据，不是6h模型难度证据。初始旧SWE题出现3.5～14分钟满分；因此真正在题目里增加完整系统能力与兼容面，不靠等待、加同构case、降低B或重映射历史分数。
- 保护评分权威：私有expected/断言不与candidate在同一个解释器内；不能信candidate打印的pass计数/worker成功帧。编译/导入/执行均按不可信候选降权、隔离私有数据，可信侧比较实际行为。添加打印伪造成功、读取已知私有路径、写reward、残留子进程等针对性控制，并留真实证据。
- 构建最多-j2/CARGO_BUILD_JOBS=2；每次大编译/镜像前检查磁盘。不要拷贝旧target/build/cache/虚拟环境；从固定源码和依赖重建。独立使用自己的输出/镜像/容器，无全局prune。旧素材可只读参考，需闭包复制到本题才能计交付。
- 对普通任务交完整合法参考，而不是用不符合语言/约束的上游gold冒充满分solution。开放优化题可按规范声明open-solution并交可运行强参考/真实分值；不能人为拉到1.0。
- 输出完成/缺口均给明确可执行下一步和证据；不把静态gate通过写accepted。没有ARM/6h证据就写未验证。

本题是返修新版本。旧输入只读：/ws/users/raymone/edgebench/swe-route-authoring-005-20261015-r3/jobs/24_lark_system_reconstruction。部署后当前job下 previous-input/ 是不含构建缓存的素材/题包副本，之前的报告只作历史输入。请先读 previous-input/AUTHOR_RESULT.json、SCOPE_CARD.json、REQUIREMENTS.json、task/instruction.md，建立 REPAIR_PLAN.json。保留previous-input不变，在当前job/task及其他当前输出创建新版本；不得修改旧job。逐项解决本题scope_brief中的缺口，再重放实际控制。复制进来的旧成功报告不可冒充本轮执行。

先读 /ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/guidance 下的作者规范、三套factory原始规约、范围要求、actual Harbor schema。源码语义以固定revision为准；新仓库至少先比较三个完整范围。静态检查：PYTHONPATH=/ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/controller python3 -m edge_factory.swe gate --job /ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/jobs/29_lark_verifier_repair_r2 --output /ws/users/raymone/edgebench/swe-route-authoring-010-20261015-r4/jobs/29_lark_verifier_repair_r2/STATIC_ADMISSION.json 。它不能代替真实运行。可只读参考 /ws/users/raymone/edgebench/swe-rollouts-005-20261015-r5/framework 中的实际Harbor/独立判分代码，在本题复制需要的无凭据部分后使用；不要写入那里的运行目录。
