# 素材与实例转换

唯一项目来源是 RoaringBitmap/CRoaring，固定 revision `f2d9c6d3affaed28c8a899e96d85334ce4ae35af`。job 根目录 `material-src/` 是完整 Git checkout，不是选读文件集合；原始 LICENSE 为 Apache-2.0 OR MIT。`authoring/evidence/source-manifest.json` 保存全部 tracked 文件的 SHA-256。与输入卡片的六份已下载文件逐个比对相符，checkout 的 Git status 为空。来源 URL、依赖许可与镜像 pin 见 provenance.json。

这是新扩展实例，不声称上游缺少二元集合运算。实际阅读了 `src/roaring.c` 的 cardinality 快路、容器共享/转换实现、上游混合容器与 robust deserialization 测试和 README 的既有批量/优化选项。原生 `and_cardinality`、`or_many`、run_optimize 和 dispatch 都保留可用。新合同是三个集合在给定半开范围内的八格 Venn 直方图；批量结果要求全量预验证与输入不可变。只复制了真实库，没有用 Python 实现替换被优化的引擎。

公开 starter 的 `src/venn3.c` 使用现成 API、最小交集选择和批内重复 descriptor 复用。该实现语义完整，不能将它称为不工作的起点。私有参考 `solution/venn3.c` 直接合并 high-key，借用 bitset 存储、在约 24 KiB 栈空间展开 array/run，融合求七个交集/单集合统计量，再通过容斥还原八格。它没有堆上中间 bitmap，且正确处理 shared 容器；稀疏和 run 路径的实测速度仍可能劣于普通基线。reference.patch 和 inverse.patch 保存相对 starter 的明确源码差异；solve.sh 实际安装参考源码和头文件。另在 job 根目录私有 `reference-src/` 建立了真实 Git 分支 `author/venn3-reference`，commit `ceca35d8e836a2cdd3661ae889798e46200383d6`；`solution/upstream-reference.patch` 保存相对固定上游的完整改动。

镜像上下文包含上游源码与原有测试；可选 `benchmarks/realdata` 不参与本实例，已从两个镜像上下文移出，保留在 job 的完整 checkout 和 excluded-assets 中。这些外部语料的独立数据许可没有核验，因此没有把它们当成“已许可真实负载”。全部任务工作负载是作者新写的确定性合成分布。上游 testdata 原样保留，用于其原生鲁棒性回归；testdata README 说明 Java 序列化来源，并未把这些文件冒充本作者的新独立 oracle。

编译采用固定 GCC 镜像，Python runtime 来自输入给定的 immutable manifest-list pin；没有 apt 或运行期联网。cmocka 1.1.7 从官方 tarball 获取并锁定 SHA-256，其真实断言框架与源码随包，未重写/跳过原测试。独立构建脚本逐个编译实际 `src/*.c`，不执行提交者的构建脚本。cmocka Linux config 的路径被去除，指针大小改用编译器宏；ARM 容器构建尚未验证。

# Oracle 与分离

核心语义由私有 Python 整数集合生成期望值，不调用 CRoaring。每个元素的三位 membership 决定格子；bin 0 由范围宽度减去非空格得到，避免遍历 2^32。独立 portable encoder 生成无 run 格式输入，由 C 库反序列化并验证；独立 decoder 检查库生成的 array/bitset/run 格式、offset 与实际集合。查询前后的 portable 字节和 COW 原件必须一致。这既包含跨实现互通，也包含不可变性检查，不是单纯自 roundtrip。私有 root-only、未修改原库加普通组合的 sanity runner 用于基础设施检查，不能读到它时不会伪造候选零分。

公开材料是 API、starter、ordinary 基线、确定性 benchmark、真实 native regressions 和一个可手算 CLI smoke。反馈集固定 63 个 case，各用 native/scalar 两次；组成员见 `verifier/private/case-membership.json`。作者审计采用不同 seed，但边界与类型组合有结构重叠，不声称是独立来源 holdout。审计集不进入正式反馈分数，也不用于事后挑提交。

同一作者写了合同、参考和测试，故仍有共同遗漏风险。公开上游可被记忆，完整普通组合也能拿满当前语义分；本实例的长期潜力只能来自后续性能目标，不能来自隐藏已有 API。生成器、测试分组、权重已冻结；没有使用原 EdgeBench 的隐藏输入或答案。authoring 与 solution 是作者/评测包文件，只有 environment/ 被复制到解题镜像。

编译与运行均降为 UID 65534，私有参考、评分代码和奖励目录由 root 保护。实际本地探针确认已知私有文件不可读、reward 不可追加、汇编器 `.incbin` 不能嵌入私有参考。候选输出有时间、内存、文件和长度预算，运行组结束后清理。镜像隔离本身、Harbor 实际挂载、目标 ARM 及原生运行尚未实测，不能由本地主机权限探针推断通过。
