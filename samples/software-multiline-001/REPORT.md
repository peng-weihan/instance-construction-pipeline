# 六条软件工程造题路线：首轮实际结果

用户要求一次性多尝试路线。本轮由三组 gpt-6.1-sol 作者并行构造六条，覆盖五种原题机制。**四条完成作者侧本地评分闭环，两条得到明确的部分实现/构建缺口；本批没有启动六小时解题轨迹，也没有验收合格题。**

本地闭环指真实源码/规范→题面→starter→参考产物→行为评分→部分/错误实现对照。它不代表 Docker、Linux隔离、Harbor运行、ARM或长时难度已经通过。原有科学与金融两个运行不属于本批，新造题工作未修改它们。

## 六条分别做到了哪里

| 路线 | 实际源码与产物 | 本地实测 | 本轮筛选 |
|---|---|---|---|
| [01 OpenAPI](01_openapi/AUTHORING_REPORT.json) | 完整固定上游；修改真实schema composition处理；实际生成、导入、同步/异步调用客户端 | reference 1；starter/空提交0；两near-miss各5/6；原生unit 321 passed/4 skipped、生成代码执行80 passed | 构造成功；约130行通用预处理已闭合当前profile，退选当前范围的六小时准入 |
| [02 RESTler](02_restler/AUTHORING_REPORT.json) | 实际CLI→BFS driver→原子保存/加载，跨进程generation2→3；固定Polaris真实服务素材 | 原生组件reference6/6，starter2/6，反例3/6与5/6；**正式分数null、valid=false且无reward** | 部分构造；真实HTTP/服务重置/资源生命周期和完整参考尚未闭合 |
| [03 Wasm](03_wasm/AUTHORING_REPORT.json) | Python字节码解释器；V8独立真值；223 frozen cases、8组 | reference重复1；starter.125；NOP0；no-store .8125、unsigned-div .999233；实际solution注入后1 | 可运行profile小样；仅i32，无类型验证/table/imports，存在早满风险，hold |
| [04 DataFusion](04_datafusion/AUTHORING_REPORT.json) | 完整固定真实引擎；SortExec/TopK/merge探针；12正确性与6性能workload；两真实源码反例补丁 | 独立oracle与SQLite12/12一致；补丁dry-run可应用；**未运行DataFusion，性能及分数全部null** | 素材与评分骨架；未建依赖/二进制、未测baseline/强参考/性能锚点，hold |
| [05 TOML](05_toml/AUTHORING_REPORT.json) | 完整真实Rust workspace；parser/edit/writer中的四函数受控恢复；实际逆补丁与离线vendor | reference35/35，得1；starter.020408；Unicode/decor反例.866667/.6；缺提交有效0、缺compiler无效无reward | 构造成功；范围主要是string helper，长期价值高风险，暂缓 |
| [06 jq](06_jq/AUTHORING_REPORT.json) | 官方jq-1.7.1源码真实构建；84 CLI cases、8组，含stream、组合、作用域、递归、归约与错误 | reference重复1；starter.327083；NOP0；两partial .271528/.299306；实际solution重建后1 | 具备下一阶段审查价值；复杂组合覆盖、简单替代、Linux行为及六小时难度仍待验证 |

上述reference/partial分数均是作者对照，**不是教师模型六小时解题成绩**。02的6/6只是原生checkpoint组件，不能当完整正式score=1；04的SQLite一致性也不能当DataFusion正确性或速度证据。

## 这轮筛选改变了哪些判断

**OpenAPI：真实issue不自动变成长任务。** 新参考将复杂模型先降低为生成器已支持的表示，约130行就覆盖冻结的六组。这个实现不是关键词或输出硬编码，实际生成客户端和原生回归均通过；因此当前范围没有足够理由投入六小时。下一修订应研究真正需要改运行时/模板/生命周期的SDK roadmap，而非增加同构schema。已保存[实际issue路线提案](01_openapi/r2/ROADMAP.md)，它尚未实现。

**RESTler：要读可达代码。** saver中有旧pickle保存/加载逻辑，但入口提前返回使其失活。作者已把恢复接到真实CLI和BFS，证明不应仅按接口名称退选。另一方面，原生组件可恢复不等于真实请求与服务状态可恢复：Polaris本机没有Java runtime，真实构建命令失败；完整请求日志、幂等和资源生命周期参考也未实现。正式grader明确拒绝评分，避免把一个小组件成功包装成整题满分。

**Wasm：闭环可信，当前范围仍小。** Python参考与独立V8的223项比较一致，但这只是明确限定的i32 profile。一个负数除法错误实现仍达.999233，说明现有能力分配/取样对该缺陷不敏感；保留原始分数，不为曲线好看改权重。更深的验证、间接调用、导入/链接要另立修订后再验证。

**DataFusion：源码、探针和oracle是三层证据。** 本轮保留真实算子和Rust crate，没有偷换为几十行排序程序。独立oracle已核对，但探针尚未编译，依赖路线与计时规则尚无运行证据。所需工具链可从官方取得，不能说它不存在；稳定tag50.0.0（Rust1.86）及49.0.2（1.85.1）也已固定为替代候选，记录在[版本筛选](04_datafusion/authoring/alternative-version-screening.json)。当前MSRV1.95、建议toolchain1.99，与已装的本地1.90不同；主要状态是未构建/未测，而不是证明无法构建。

**TOML：跨三个crate不自动代表跨层难题。** 当前缺口主要是string decoder和表示/输出helper，tokenizer、parser状态与AST/container编辑大部分仍存在。私有逆补丁能恢复gold是消融构造的性质，不是solver可获得的捷径。这里的早满风险是范围筛选假设，尚无公开简单baseline满分或盲解耗时证据；暂不优先付六小时成本。

**jq：当前最完整的行为重建候选。** 参考来自实际编译的官方源码，不是Apple jq自述版本或自造expected。工作环境没有目标实现，judge只有冻结expected，没有可供candidate调用的jq oracle。仍需独立审查跨语义组合、完整profile合同、外部依赖与捷径；84个case和一个成功reference都不构成六小时难度证明。

## 流程与规范检查

- 六条都有source-card、实际题面、starter、reference或诚实标注的draft、评分代码、来源/评分/构建元数据、分离work/judge上下文和准备脚本；完整程度以表中语义状态为准，不按目录数量算合格数。
- 对远端实际Harbor0.23.0源码执行了只读`TaskConfig`验证。六份TOML全部通过，且没有会被Pydantic静默忽略的未知根/agent/environment/verifier字段；验证时输入未变。[配置证据](schema-validation.json)
- 父级静态追踪12个Dockerfile的COPY源，没有发现缺源或越界构建上下文；所有基础FROM都已固定digest。实际镜像未build，自建work/judge镜像尚无已运行digest，这不是跨架构通过。[静态检查](parent-static-review.json)
- 根tests与judge实际COPY版本由作者做逐文件一致性核对；collector记录元数据、部分grader镜像摘要和作者报告，不执行候选，不颁发QC通过。[批次机器记录](BATCH_STATUS.json)
- 普通错误、空提交与基础设施错误分别处理；03/06已实测语法错有效0、损坏fixture无效且无reward，05已实测缺compiler无效且无reward。02/04保留无效状态，不以假0混入未来曲线。
- Linux UID/权限、镜像实际启动、原生Harbor与周期评分一致性、ARM、五次复评、六小时增长、三条轨迹和交付验收均未完成。

## 下一阶段的并行优先级

1. **jq：**独立审题、增加有依据的组合/边界辨别检查、排除简单完成路径，再做容器基础准入。它具备完整本地行为闭环，但尚未达到可直接开启正式六小时的状态。
2. **RESTler：**闭合真实服务运行/重置与请求状态，完成恢复/幂等/资源生命周期参考和独立判据，避免停留在pickle组件。
3. **DataFusion：**选择固定版本与工具链，真正编译并先测当前baseline；存在稳定优化空间后再冻结锚点，否则更换子系统/workload。
4. **OpenAPI、TOML、Wasm：**保留本轮可复用构造pipeline，扩展真实语义范围时另做修订。不能仅增加case、删更多无关代码或调整分数来制造长时性。

上述是并行推进优先级，不把后两条的材料潜力当已验证性能空间，也不把前一条本地成功当六小时通过。后续仍遵守先一条完整六小时、符合要求后补两条的既定策略。
