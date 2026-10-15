# 素材与实例转换

原始生产仓库是 Microsoft RESTler Fuzzer，完整固定提交
`6d984deedbc54aad957fa3da0c7e9e5df23a2aee`，来源
https://github.com/microsoft/restler-fuzzer 。MIT 许可原文保留在公开环境根目录。
作者的完整 checkout 位于本 job 的 `material-src/`；逐文件 hash、原 URL、许可
hash 见 `authoring/provenance.json` 及 `authoring/source-files.json`。取得的选读
输入与完整源码按 SHA-256 核对，未借用旧样例的 gold、测试或分数。

公开环境由 `git archive` 导出完整固定仓库，将 Python `restler/` 移到
`submission/restler/`，其余源码和原生测试保留。唯一共用兼容修正是
`utils/logger.py:print_gc_summary` 在没有 GC 对象时输出空统计，避免原生 CLI
在退出时抛 NoneType 错误；此修正同时进入 starter、参考和独立原生 oracle。
原生 saver 的禁用状态保持在 starter 中。没有删除原本可用的恢复功能：
saver 中的 pickle 路径在该提交不可达，而 messaging 的自动 reconnect/retry 已可用。

本实例为原创工程演进任务。新写的合同、WAL/UUID/response replay 参考实现、
公用 grammar、幂等 gateway、进程故障控制器和评分程序均为本轮作者产物。
参考通过真实 CLI、driver、rendering、response parser 和 HTTP transport 运行。
反向补丁 `authoring/reference-to-starter.patch` 仅用于审查差异；本题并非从旧
公开 gold 删除代码后伪称新扩展。实际注入入口是 `solution/solve.sh`。

卡片中的 Polaris 未进入固定素材。本实例使用同一固定提交自带的 FastAPI
博客 demo_server，直接执行原 SQLModel、SQLite 和路由代码；没有编写一个
仿制资源服务替代它，也没有声称执行了 Polaris/.NET/Java 场景。预写 grammar
绕过的是本题无关的 F# 编译器构建，RESTler Python 引擎和真实 HTTP 服务均实际运行。
其原有 bug 和 SQLite 最高 ID 复用行为保留。gateway 是明确的服务协议适配层，
仅增加持久化 Idempotency-Key 缓存和故障窗口，不生成博客业务响应。

服务侧保证严格限定在 backend 响应和 ledger 提交之后的注入窗口。进程重启
保留两个数据库，gateway 重启可读取持久化 ledger；没有声称覆盖业务已提交但
ledger 未提交的任意服务崩溃。通用 exactly-once 在该窗口之外并不可由客户端保证。
公共 `public/gateway.py` 给开发者同样能力；普通库和包装工具未被禁止。

独立 oracle 是另一个从固定生产源码恢复的无 recovery 原生 campaign，输出
有序 upstream method/path/body/status，以及从真实 SQLite 直接读取的 id/body
状态。原生 testing_summary 全量比较覆盖、资源创建数和请求计数等。UUID workload
另跑原生无恢复 campaign，仅规范化 UUID 值后比较轨迹和状态；不从参考 journal
推导期望值。SQLModel checksum 与 Date 等非确定数据不进入语义比较。

公开部分：完整源码、原生测试、grammar/dictionary、协议 gateway 和本地诊断 probe。
反馈部分：冻结的十二个语义组，名称、分数和评分公式公开，具体 kill 边界由隔离
verifier 执行。作者审计部分：native pytest、控制实现、权限探针和重复重评，不额外
增加 reward。没有拿作者保留集挑选教师提交；本轮没有教师轨迹。

私有实现只在 `solution/`；verifier 镜像不含它，work 镜像也不含 solution、grader
或 authoring 目录。独立 verifier 仅包含固定原生 baseline 和测试，private 祖先
0700，候选编译/运行 UID=2001。复制候选生产模块到独立目录后降权编译和执行；
服务及 oracle 证据由 root 保护。测试源码或公共接口本身不构成秘密。源代码公开
使联网复制/已有实现污染仍需在未来独立校准中审计，本地 Oracle=1 不证明无捷径。

Python 3.12.8 基础镜像使用给定 manifest-list digest，wheel 版本、文件 hash 和
wheel 内许可元数据记录在 dependency manifest。构建上下文各自拥有全部依赖，
不引用父批目录、凭据或宿主账号配置。运行阶段禁止外网，只使用 loopback。
