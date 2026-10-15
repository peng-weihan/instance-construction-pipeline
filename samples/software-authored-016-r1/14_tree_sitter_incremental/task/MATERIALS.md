本实例是原生 tree-sitter 核心的受控恢复任务。它不是新的上游缺陷报告，也没有使用原始 EdgeBench 隐藏测试。

来源为 https://github.com/tree-sitter/tree-sitter ，完整 checkout 固定在 `8ca548849fc8dbefd699edcec26546bb14112820`。作者目录 `material-src/tree-sitter` 保留完整 Git checkout；`authoring/source-manifest.json` 按 tracked 文件记录 SHA-256。源码 MIT 许可和 `lib/src/unicode/LICENSE` 的 Unicode/ICU 许可均保留。私有 `verifier/private/reference.tar` 是此 commit 的完整、未修改 Git 导出；不是几份选读文件。

Grammar 独立来源为 https://github.com/tree-sitter/tree-sitter-python ，MIT，tag v0.23.6 经远端解析固定为 `bffb65a8cfe4e46290331dfef0dbf0ef3679de11`。完整 checkout 在 `material-src/tree-sitter-python`，公开和 judge 均包含其原始 `src/parser.c`、`src/scanner.c`、JSON 元数据、头文件、许可及原生 corpus。没有重新生成 grammar，也没有依赖未冻结的 HEAD。

转换是先复制完整工作树，去掉 `.git`，然后只消融四个原生 C 文件的关联行为：`parser.c` 的 scanner/first-leaf 复用兼容检查，`subtree.c` 的变更标记及子坐标变换，`tree.c` 的 included-range 编辑，以及 `get_changed_ranges.c` 的 edited-subtree 比较条件。完整初始解析保留。其余源码、API 头文件、native tests、bindings 和许可证逐字保留。`solution/restore.patch` 是干净逆补丁，真实 `solve.sh` 已在作者本地目标上执行，并与完整原始工作树逐文件比较一致。没有把参考的完整核心藏在 starter vendor、Git 历史、二进制或其他副本中。公开 grammar 的 parser.c 是语法表，不是 tree-sitter 核心参考。

新增部分是原生 C API 探针、编辑序列、确定性隔离 grader、评分元数据和 Harbor 包装。探针直接链接考生 `lib/src/lib.c` 和固定 grammar。每轮检查 edited tree、included ranges、旧树副本、保存的 node handle、增量树、另一个 parser 的 full parse 及 changed ranges。它不是另写的 AST 实现。12 个初始解析检查改编自原 grammar corpus 的原始输入和期望 named-node 结构；比较时去掉 corpus 中可选字段标签，完整字段行为另由原生树快照检查。原始 corpus 文件本身没有修改。33 个编辑场景为本任务原创，其中 3 个 scanner 安全反例来自固定 seed 的作者构造期探针，不是上游隐藏数据。

Oracle 有三层。第一层用未消融的固定核心生成、冻结 API 逐节点输出和精确 changed ranges，grader 只读取这些私有输出，考生不接触参考执行程序。第二层每次参考增量解析必须等于独立 parser 的从头解析，45 个场景中的所有编辑轮均已验证；这层可以发现复用错误，但并不独立证明 tree-edit/changed-ranges，后两者依靠第一层的未改动实现。第三层有 grammar 人工原生期望及不计分的作者审计：人工 named tree、按输入文本独立计算的每节点 byte/point、相同语法类别替换无 changed ranges、结构变化必须报告范围。它避免只检查自实现的往返一致性，但仍不等于完全独立的第三方语义审查。

公开部分为完整 starter、固定 grammar/corpus、API 说明、3 个原生编辑输入和 C 探针、评分组与公式。周期反馈部分为冻结的 45 场景 / 198 个具名检查，只反馈检查结果而不返回私有期望树；公开的三个输入也是其中子集。另有 3 个不计分 `private/author-audit` 场景，用于作者质量审计，不参与选择考生提交。构造期 scanner 搜索是在最终冻结前补充反馈测试，不能冒充独立保留集。作者审计的初版解析空 section 存在 bug，失败证据已保留，修正后 3 个场景均通过。

两个构建上下文完全分开。work 仅 COPY 公开文件；judge 的私有目录 0700。编译身份 UID 65534、运行身份 UID 65533，与读取期望及写 reward 的 root 控制器分离。编译固定原生对象时没有考生源码；编译考生源码和运行二进制均降权，清理进程组并限制资源。真实私有文件打开、reward 写入、汇编器 `.incbin` 已做本地负探针。容器构建和网络隔离运行尚未执行，不能把本地权限探针称作完整安全认证。

主分没有性能项。源码本来公开，能恢复上游代码是显著泄漏/早饱和路径；完整 API 的 full-reparse 实测已经满分。题包因此仅供审阅和后续否证，六小时难度 held_for_evidence。没有隐藏正常工具、增加操作计数奖励或编造速度锚点来规避该风险。
