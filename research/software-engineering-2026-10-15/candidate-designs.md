# 软件工程新题：素材与构造设计

本轮只做源码、规范与现有轨迹研究。以下候选均未构造成完整新题，也没有新的求解或计时实验。固定的源码树和少量选读文件位于 `sources/`，每个目录都有 commit、文件 SHA-256 和来源 URL；不是完整 checkout。当前版本用于确定证据范围，未来出题基线应另行确定，不能将“最新”当难度保证。

## 首选：复杂 OpenAPI 模型的端到端客户端生成

- 素材：[`openapi-generators/openapi-python-client`](https://github.com/openapi-generators/openapi-python-client)，固定 `0a283fe21eeaa23046faf622d4ff4b2c826d2edb`，仓库 MIT。
- 已读：README、CHANGELOG、functional_tests/README、实际 union/properties 行为测试；下载 parser 的 merge_properties 模块供后续作者追踪。项目已将生成器与生成代码都视为黑盒，实际导入执行生成结果，具备比字符串快照更可靠的验收基础。
- 真实需求线索：[内联 oneOf/anyOf 对象失败 #1428](https://github.com/openapi-generators/openapi-python-client/issues/1428)、[allOf 嵌套 oneOf 丢失类型信息 #1328](https://github.com/openapi-generators/openapi-python-client/issues/1328)、[组合模型丢字段 #1392](https://github.com/openapi-generators/openapi-python-client/issues/1392)、[3.1 裸 array #1435](https://github.com/openapi-generators/openapi-python-client/issues/1435)。本轮保存了 API 返回的正文与状态；issue 是报告者的现象描述，不证明该固定版本仍可复现，也不证明所有期望都符合标准。
- 同类依据：与原 Schemathesis 题共享“已有开发工具中跨解析、内部模型、执行产物及兼容性的功能演进”机制；项目、产物和新合同不同。这里只能称机制相近，尚不能称统计上已证明同分布。

**拟定交付物：修改后的生成器源码。** 不以提交某个示例 API 的手写客户端完成任务。一个连贯的需求是：使组合模型经过引用解析、内部类型表示、模板生成、导入和序列化之后，仍保留题面明确承诺的字段、类型和缺省行为。

作者应围绕同一类型图定义这些能力，而不是把 issue 标题拼起来：

1. 内联与引用模型身份一致，重复引用、嵌套和命名冲突不产生错误导入。
2. 有明确可区分分支的联合类型与组合字段，端到端编码/解码保持正确；重叠分支如何处理必须先写进合同，不能从某个实现猜答案。
3. 在题面指定的版本范围内区分缺失、显式 null、可选字段和应用层默认值，维持现有 API 的合理兼容性。
4. 以上机制组合后，生成的类型注解、模型、请求和响应路径仍一致；不能只通过生成阶段而在调用阶段崩溃。
5. 对错误 schema 给出定位信息；保持冻结的原有回归行为。

需求依赖图应是“schema 图→规范化表示→类型/模块生成→运行时转换→端点调用”，后续能力会迫使作者修正前层抽象，才有真正的整合难度。

**语义真值：**固定 [OAS 3.1.1](https://spec.openapis.org/oas/v3.1.1.html)，同时列出保留的 3.0 行为。JSON Schema 的 `default` 是注解，验证器不会自动补缺失值；SDK 是否采用它生成函数默认值是应用合同，必须另行说明，不能把 issue 的诉求直接当标准。参见 [JSON Schema 注解说明](https://json-schema.org/understanding-json-schema/reference/annotations)。生成客户端也不必被无意要求成为完整 JSON Schema 验证器。

**评分设计：**按固定语义能力组计分，每组有代表性的执行断言；同组增加随机 case 不改变组权重。检查实际生成、导入、序列化、请求字节及返回对象；不以字段名出现、正则匹配源码或与 gold 文件逐字相同计分。原生回归和逐项 checks 另有 pass/fail，交付的主分依任务书明确为 bounded_continuous。权重、端点与最终公式待合同冻结后进入机器元数据，本文件不冒充已定版 scorer。

**作者 pipeline：**用 DeepSWE C 的新需求→测试→参考实现闭环；借 NL2Repo 的证据→行为合同方法；用 ProgramBench 的受控观察验证生成产物。CLI 作者必须能在真实仓库追踪引用关系、修改内部模型和模板、运行生成产物、修复交互失败。脚本负责固定版本、依赖缓存、生成输入、执行和评分。

**难度退选条件：**固定版本已经实现主要需求；仅预处理 schema 或换一个现成依赖就满足全部合同；多个 issue 归结为一个小修复；规范歧义导致没有唯一可评行为。上述情况应缩减/更换候选，不能靠增加测试数量或隐藏约束掩盖。

## 第二条：DataFusion 在固定内存下优化排序与 Top-K

- 素材：[`apache/datafusion`](https://github.com/apache/datafusion)，固定 `91cd7ffb927b5a4f9fee1907db50a9610759de5b`，Apache-2.0。
- 已读：benchmarks/README 的数据生成、排序、Top-K 与内存测量说明；取得 sort_pushdown 查询、相关 sqllogictest 与 aggregate_memory_spill 测试文件。完整业务执行路径尚未审计。
- 原生证据：官方排序工作负载区分键数量、基数、负载列和已有顺序；有 SQL 正确性集和独立 benchmark。相关源见 [benchmarks](https://github.com/apache/datafusion/tree/91cd7ffb927b5a4f9fee1907db50a9610759de5b/benchmarks) 和 [sqllogictest](https://github.com/apache/datafusion/tree/91cd7ffb927b5a4f9fee1907db50a9610759de5b/datafusion/sqllogictest)。
- 同类依据：与原 ANN QPS、exchange throughput、VLIW 优化共享“语义约束下改善系统性能”的机制；查询引擎和 workload 不同。

**拟定交付物：修改后的真实引擎源码。** 在固定 CPU、线程和内存上，针对一个经 profiling 确认存在空间的排序/Top-K 路径提高性能。先选一个子系统；不要同时要求重写排序、连接、聚合来凑规模。

**自然难点：**计划规则与执行算子的配合；已排序、局部排序和无序输入的不同策略；有界内存和 spill；NULL、并列值、多键顺序；批次和分区边界。哪些难点保留，须由作者基于真实代码和基线证据决定，尚未建立全部困难都存在的事实。

**工作负载：**优先从官方排序查询与生成器提取结构，另造可复现的日志/表数据；冻结分布、规模、倾斜、排序状态、查询族及随机种子。只换 seed 不算一个新题。外部 ClickBench/TPC 等数据与工具需逐项记录来源和许可；本轮没有下载这些数据，不能据仓库 Apache 许可推断外部数据也可重分发。

**评分设计：**固定 workload 的正确结果与资源边界先验收，再对符合条件的实现计算固定公式的性能分，并保留原始时间、吞吐和内存。排序未规定的并列顺序要规范化，数值误差须有合同。避免一个无关语法边界将所有早期实现压成零分：将功能范围收敛到完整可执行子系统；若仍需能力组局部分数，必须在题面和评分表同时规定正确性门槛及权重。

计时必须固定预热、重复、线程、缓存策略和编译选项；变慢不能因归一化方向错误而涨分。弱基线、参考实现和上限是不同概念，上限不能仅因为 gold 存在就写成 gold 性能。ARM/x86 运行差异以后单独验证，不混进当前材料阶段的结论。

**作者 pipeline：**作者 profiling→提出优化假设→实现两个真实可比较策略→验证正确性与资源→冻结范围；脚本构建、重放、计时、输出结构化反馈。DeepSWE 可提供补丁和回归合同，现成三个 factory 都还需新增性能 scorer。

**难度退选条件：**原生版本在候选 workload 已接近目标；一个配置开关即完成；收益主要来自错误结果、预计算或不公平编译；计时噪声大于改进。没有 profiling 与重复计时前，不宣称这个方向已有六小时优化空间。

## 真实状态服务素材：Apache Polaris

- 素材：[`apache/polaris`](https://github.com/apache/polaris)，固定 `f838a62e20e7de72946d250883e8d9b1d6d2f68e`，Apache-2.0。
- 已读 API spec 的目录说明、management 规范的结构和实际 Python 管理集成测试；取得 catalog 集成测试。管理 API 包含 principal、principal role、catalog role 和授权关系，测试包含创建→赋权→查询→清理的真实序列。
- 适用角色：作为改造状态化 API 测试工具的真实目标服务及业务序列来源，不是“把 Polaris 自动算作一道题”。题目还需要明确让求解者改造什么工具、增加什么行为。
- 更强的 RESTler 后继候选可研究：在真实资源依赖与权限生命周期下增加可恢复执行、故障后的状态一致性与有效重放。先审计现有工具是否缺失，定义崩溃前后可观察语义，再决定构造；不能直接假设这些需求都不存在。
- 必须先解决离线构建、稳定 reset、无需真实云凭证的本地存储/认证、一次评分成本。若需要外部云服务才能打分，拒绝该配置。真实服务本身也可能太重，应先选本地可运行的一组业务接口。

它比一个随意写的小 Flask 服务更有真实性，但服务大并不等于求解者有更多改进空间。这条路线暂排在前两条之后。

## 行为重建备选：jq

- 素材：[`jqlang/jq`](https://github.com/jqlang/jq)，固定 `6b53f8031161db96387b64b5f412845cd23491f6`；实际取得 `COPYING`、`tests/jq.test`。
- 许可：COPYING 中核心许可为 MIT，docs 另为 CC BY 3.0，并有第三方通知；GitHub API 给出 NOASSERTION，不能直接拿该字段当具体许可结论。
- 同类机制：与 Git 移植、编译语言系统、CLI 重实现接近；适合 ProgramBench 的行为观察与 NL2Repo 的规格补齐。
- 暂不优先：完整 jq 过大，随意缩成几个过滤器又太小；已有 jaq/gojq 等实现可能形成现成替代路径。依赖、语言、执行环境与产物要求应基于任务真实需求明示；若合法复用已能完成任务，就承认它容易，不靠暗藏禁令制造难度。本轮未构建或测量这些替代实现。

## 素材如何转成独立训练实例

1. 脚本登记 repo/commit、许可证、规范、公开需求、原生测试和构建证据，建立候选卡；当前已经到这一步的源码勘察阶段。
2. 作者读仓库，复现需求，识别共享抽象和依赖，形成 requirement_graph；已有测试/issue 只是证据，合同由明确行为组成。
3. 固定新任务合同、资源与提交文件；另一个验题阶段从合同推导用例，检查作者的实现假设。需要改合同就版本化并重新生成下游。
4. 作者实现 gold 与 starter，脚本完成补丁回放和材料隔离；用自然错误实现、部分实现和边界错误检验评分辨别力。
5. 独立 agent 环境与 verifier 环境只交换快照，验证器每次无状态运行；Harbor task.toml 导出是规范适配层，不能用上游某个 task.yaml 冒充。
6. 公开练习材料和运行时固定反馈集分开；可另留作者质量审计集，但它不改变正式 best-of-run 规则。正式成绩仍是一次运行中全部合法提交的最好成绩，不能换成最后一次或事后重选。
7. 首条 gpt-6.1-sol 六小时试跑记录各提交与 0.5/2/4/6h 检查点。早满、全零、安装等待和真正算法/设计改进分开归因；不能从源码规模预测六小时有效性。符合要求后再补另外两条，遵守用户既定成本策略。
8. 固定合同后才能批量采样。新题要改变实际语义交互、目标子系统或真实 workload；只改变量名、seed、错误信息或题面不是新实例。

训练与原评测集应记录 repo 谱系、原题快照、补丁/函数与测试语义重合、规范/数据来源。换仓库只是第一层隔离；训练效果还需在未见的项目/机制组合上验证，当前材料研究不构成训练收益证据。
