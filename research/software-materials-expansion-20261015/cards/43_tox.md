# 43_tox — 带资源租约与可恢复执行记录的测试矩阵版本
- 来源：[tox-dev/tox](https://github.com/tox-dev/tox)；SHA `d947dd4e43388f727bb534c3f0ad7997d76b4767`；M1 / `build_scope_probe`。
- 已有：已有环境依赖拓扑、全局并发上限、fail-fast、进程中断、结果 journal 和环境复用。
- 拟任务缺口：拟扩展多资源容量/互斥租约及以输入身份校验的恢复计划；不是新增并行或 depends。整体缺口尚待基线探针确认。
- 产品/子系统边界：交付适合共享 CI 主机的矩阵执行模式：环境声明数据库/设备等资源，计划器联合依赖与容量调度，失败和 SIGINT 归还租约；恢复记录只重用输入未变且真实完成的环境。
## 模块链与固定证据
- [`src/tox/session/cmd/run/common.py:424`](https://github.com/tox-dev/tox/blob/d947dd4e43388f727bb534c3f0ad7997d76b4767/src/tox/session/cmd/run/common.py#L424)：已有线程池、完成集合和就绪环境调度
- [`src/tox/session/cmd/run/common.py:554`](https://github.com/tox-dev/tox/blob/d947dd4e43388f727bb534c3f0ad7997d76b4767/src/tox/session/cmd/run/common.py#L554)：依赖决定可运行集合，run_order 检查循环
- [`src/tox/session/cmd/run/common.py:231`](https://github.com/tox-dev/tox/blob/d947dd4e43388f727bb534c3f0ad7997d76b4767/src/tox/session/cmd/run/common.py#L231)：已有中断及 journal/结果处理，必须复用而非重做
- [`tests/session/cmd/test_depends.py:15`](https://github.com/tox-dev/tox/blob/d947dd4e43388f727bb534c3f0ad7997d76b4767/tests/session/cmd/test_depends.py#L15)：真实项目测试检查 wheel 构建环境与 depends 拓扑
## 组合场景
1. 共享数据库容量为2、设备互斥为1；相互依赖的测试环境满足容量且无无关串行。
2. 一个环境安装失败、另一个被中断；资源可立即供后继独立环境使用，结果区分失败/未执行。
3. 恢复上次矩阵时修改一项命令或包输入，只重用仍有效的完成项，旧依赖结果不污染新运行。
## 基线与退出
- 强合法基线：tox -p/depends/result_json 与插件钩子；shell flock 或标准 filelock 包装命令、CI 自带资源组/恢复脚本都属于合法基线。
- 首探/退出：先以现有插件+filelock 实现双资源、失败后释放、恢复输入校验三个场景；若仅薄配置即可覆盖整套契约则 hold，不能靠禁用插件抬难度。
- 早期完成后的剩余假设：单资源互斥成功后，多资源原子获取、容量、公平排队与依赖饥饿仍可能待解。
- 早期完成后的剩余假设：一次并行运行成功后，SIGINT/失败的释放、过期记录和配置/依赖变更的恢复失效仍需验证。
- 独立 oracle / 原生回归：独立子进程事件账本和实际资源计数验证并发/释放/执行集合；保留原生 test_depends/test_parallel 与 journal/中断回归，不信任计划器自报。
- 许可观察：根 LICENSE 为 MIT 式许可文本；保留许可与版权，插件/解释器另审。
- 离线/架构风险：固定源码 Python>=3.11；预装多解释器、wheelhouse 和构建后端，避免联网装包；POSIX/Windows 信号与锁语义须分开定契约。
- 官方在线核对：[primary](https://github.com/tox-dev/tox)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
