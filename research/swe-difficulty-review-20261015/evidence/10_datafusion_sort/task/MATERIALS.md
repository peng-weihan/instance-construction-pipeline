# 素材如何形成当前实例

唯一引擎来源为 https://github.com/apache/datafusion ，固定 commit `10343c18292fc3a9ca62b59c8bb530169fe79b82`，workspace 版本 50.0.0、MSRV 1.86.0。`material-src/` 是真实完整 Git checkout，2516 个源码/许可/文档文件，已核对 HEAD 与候选材料五个文件的 SHA256。原始下载 URL、每文件哈希、源 archive 哈希保存在 `authoring/source-manifest.json`。完整源码（包含原生测试、LICENSE.txt、NOTICE.txt）封装在两个独立构建上下文的 source.tar.gz。没有读取或复制旧任务实现、旧隐藏测试、旧分数或 benchmark gold。

保留上游的 external sort、TopK、spill、memory reservation、streaming merge 能力，不把已有功能称作新增需求。公开 starter 是完整未消融的上游生产代码，额外加入作者编写的 `edgebench_sort` 示例驱动。驱动调用真实 SortExec / TopK / SortPreservingMergeExec / sort_batch，包含固定的五列 Arrow 数据生成和行内容保留检查，不是替代引擎的 Python 排序程序。独立 ingestion buffers 在计时前构造，避免巨型原数组的零拷贝切片使内存预算失真。LIMIT 0 走与 SQL 优化等效的 EmptyExec。首轮发现的驱动错误和原始失败日志仍保存在 job 的 authoring/evidence/baseline-initial-*，最终矩阵与初轮分开保存。

新增私有参考为 `solution/reference.patch`，完整改变后的 sort.rs 在 `solution/reference/`。其优化仅在 Arrow 计算出的完整排列为 identity 时跳过 payload gather；不改变比较语义，不对 TopK 短前缀保留整批。`solution/inverse.patch` 可恢复生产文件原样。参考源与固定源清单共同定义完整 reference；solve.sh 实际把这个文件注入 submission，不写奖励。上游已有排序能力不属于作者原创；这个快路径、probe、独立 oracle、用例、包装与评分器为本次新编写。

独立排序 oracle 位于 tests/oracle.py，使用标量比较器与 IEEE 位表示，不调用 Arrow 或 DataFusion 的排序结果；Rust 驱动只负责真实引擎执行和整行保留核对。两种语言的数据生成均由公开合同给出，逐个 id 对照最终全局序列；这不是候选和参考互相 roundtrip。浮点输入只生成规范正 NaN，未宣称覆盖所有 NaN payload/负 NaN、dictionary、decimal、timestamp 或全部 SQL planner；这些仍属于普通原生回归和后续扩展范围。

公开 split：完整上游源码、原生测试、三份反馈样例、公共驱动和标量 oracle。反馈 split：verifier/private/cases.json 的冻结 34 用例，分 numeric、utf8、floating、topk、partition、spill 六组，其成员和权重固定在 score-spec。作者审计 split：配置扫描的不同 seed/规模、reference 的 Arc 复用审计、故意错误的 nulls-last 与 skip-ascending 控制、权限与故障分类检查。审计结果不用于事后选择提交，也不改变当前分母。没有声称存在独立设计者的测试复审；作者与参考同源设计仍存在共同遗漏风险。

许可：DataFusion 原始 LICENSE.txt 和 NOTICE.txt 原样保留，Apache-2.0；新增代码使用 Apache-2.0。Cargo.lock 不变，完整 cargo vendor 输出及各 crate 自带许可进入 vendor.tar.gz，包名/版本/声明许可/校验值另列 dependency-licenses.json。Rust 1.90.0 官方发行 archive 经官方 SHA256 核对，工具链仅安装于本 job；Docker 使用提供的 Python immutable manifest pin。Debian 编译工具使用固定日期 snapshot，镜像尚待实际构建核验，不能宣称已验证系统包闭包。

work 与 judge 的构建上下文平级且自足。work 不含 solution、private、controls、作者日志或父批次。judge 含固定 upstream、权威驱动、测试和 root-only 私有配置；参考补丁仍只在独立 solution 目录。候选编译和执行均降至 UID 10001，私有路径不可读，reward 目录不可写。候选只影响指定生产源码，测试尾部由固定源恢复。本地主机已实际验证已知私有文件读取、编译嵌入与 reward 写入被拒绝；最终评分器把重建后的源码/测试设为 root 只读、复制固定探针至只读位置，并在执行探针前完成原生回归，避免执行阶段改写后续测试或探针。完整降权 NOP 构建/执行得到 0.25；它发生在最后一轮所有权加固前，最后的加固使用真实 UID 权限探针及输出/缺提交分支检查，未重新做完整镜像端到端。因此本地主机证据不替代完整容器隔离认证。

泄漏风险：公开上游本身正确性很强；当前禁用性能项的草稿会被 NOP 早期饱和，不能宣称六小时题通过。源码/公开测试/公开 oracle 是合法起点，不通过隐藏它们制造难度。测试 seed 保密不是根本安全边界，性能优化必须泛化至真实排序行为。只有测量并冻结新的性能规范、硬件资源与重复性证据后才能启用性能奖励；现有筛选数据不能冒充跨架构锚点。

两份 near-miss 的引擎探针使用 release 编译；作者审计中的原生回归使用上游自带 ci profile，以缩短不涉及性能的错误控制反馈。正式 grader 的原生回归仍使用 release。控制报告中的组合分为作者诊断值，不是 Harbor 正式 trial 或六小时成绩。

公开 baseline-configs.json 同时保留有限参数扫描与真实排序信息基线；补充探针使用未修改上游代码，显示已知全局有序单分区源可通过既有 API 跳过排序。其收益属于现有能力，不属于本次新实现。

完整源包在最终闭包检查后直接从固定 Git 工作树重建：补入 codeload export-ignore 省略的 .github 文件，将仓内 LICENSE/NOTICE symlink 物化为同内容文件，排除 .git 元数据。新包的全部 2516 个文件内容哈希与 checkout 清单一致；原始下载包哈希和新封装包哈希在 source-manifest 中分别保留。首次未闭合审计保留在 authoring/evidence/package-closure-audit-initial-export.json。
