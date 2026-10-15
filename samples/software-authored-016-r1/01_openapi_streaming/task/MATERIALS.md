# 材料、实例与边界

唯一上游为 https://github.com/openapi-generators/openapi-python-client ，固定 commit `0a283fe21eeaa23046faf622d4ff4b2c826d2edb`。完整检出保存在 job 的 `material-src/openapi-python-client/`，488 个跟踪文件逐一 SHA-256 记录在 `material-src/manifest.json`；不是把候选卡下载的六个文件当作仓库。原样保留 MIT LICENSE 和 Triax Technologies 版权声明。上游本来已有 HTTPX sync/async client、认证、multipart 文件数组和生命周期支持，CHANGELOG 0.25.0 也已说明 multipart 数组的改动；这些能力不被宣称为本题新增。

`environment/submission/` 是该完整跟踪树的公开副本，不包含本题参考。公开新材料为 `environment/public/stream-contract.json`、生成配置、SDK exerciser 和 smoke 命令。模型/端点/记录、wire 分块和 oracle predicates 均由本作者原创；没有取得或复制 EdgeBench 原始隐藏测试。候选卡仅指导机制与工程链。固定一个联合工作负载：文档级 bearer 安全性、匿名双媒体 POST、普通 JSON GET、可选认证和整数记录端点。规格不涉及任意 SSE、压缩流、OAuth 发现或泛化任意 HTTP 协议扩展。

参考是对真实 parser、endpoint 元数据和 Jinja 端点模板的五文件改造，保存在 `solution/reference/`。同一改造在本地完整 Git 仓库内有 `author/streaming-reference` 分支，实际 commit 见 `authoring/provenance.json`；基线 HEAD 没有移动。`solution/reference.patch` 是干净的正向补丁，逆向应用可恢复基线。`solution/solve.sh` 实际复制完整参考到 `/home/workspace/openapi-streaming/submission`，不写奖励、不替换 grader。工作镜像默认 root，以兼容 Harbor Oracle 注入；工作构建上下文完全不含 solution/private。独立 judge 内，所有提交生成、导入和执行都降至 UID/GID 21001。

Oracle 不使用参考生成器计算考生的 expected。root grader 持有冻结的记录字典、请求语义和事件次序。真实 SDK 生成后，在独立进程内导入执行。root loopback HTTP server 独立记录合并后的 Authorization、共享 header、JSON 和 MIME multipart；network 首记录必须先通过管道观测，server 才释放第二记录，避免以吞吐或任意延时奖励“流式”；提前退出时 server 观察 peer EOF。另有独立编写的 HTTPX ByteStream 观察器记录 read/close 次序，检查解码、空迭代、异常、取消和共享 client。它没有调用候选 parser 构造 expected。MIME 由 Python 标准库解析，模型返回值与冻结字典比较。39 项 upstream parser 回归取自受保护的私有副本，考生修改自己的 tests 不能改写这些检查。本地额外运行全套原生单元测试和 upstream generated-code 功能测试，日志另存作者 evidence。

公开集含完整 schema、输入分块和可运行 exerciser，允许正常使用 HTTPX/contextlib 等成熟工具。反馈集是 36 个固定检查、五个评分组，分组与权重见 `authoring/score-spec.json`。它不以隐藏 schema 数量制造难度。作者审计为近错对照、同源重复评分、损坏提交/基础设施区分、文件权限和补丁重放，留在 job 的 `evidence/`，不进入 work 镜像。单 schema 的泛化压力有限；生成器源码可能被记忆，固定探针也可能被投机硬编码。未来更换测试必须新版本化，不追改此版分数。

评分进程和期望值由 root 控制。工作目录的 harness/native 文件不可由候选替换；候选仅能写自己的源、generated 和 tmp 子目录。私有目录和 reward 目录是 root 0700，编译前以实际候选 UID 检查已知参考文件不可读、奖励目录不可写。源码快照拒绝符号链接和特殊文件；完整 grader 有时间、内存、文件、输出预算并清理进程组。Python SDK 与 HTTPX 进程内 instrumentation 仍共享解释器，这不是能抵御一切主动 monkeypatch 的安全虚拟机；root HTTP 证据与奖励隔离是额外边界。容器级进程/cgroup 和快照集成尚待正式运行核实，不把本地权限检查当作完整沙箱认证。

依赖版本和 wheel SHA-256 在各自独立 build context 的 `requirements-hashed.txt` 中冻结。基线 wheel 从固定源构建，仅提供上游版本元数据和正常基线发行物；评分显式把提交目录放在 import 搜索路径第一位，并要求提交存在 generator package。依赖已在全新本地 venv 无网络安装；Python 3.12 的 amd64/aarch64 wheel 均已取得。Docker FROM 使用输入提供的 Python 3.12.8 manifest-list digest；未构建 work/judge 镜像，未运行 ARM。依赖 wheel 许可元数据和 SHA/来源记录在 build manifest/依赖清单，不能把 wheel 下载成功说成容器通过。

所有 oracle/reference、Nop 和 near-miss 都使用同一原始评分公式。没有性能分数，没有虚构性能端点，也没有将弱参考归一化成 1。NOP 保留原生回归的 0.03 分是有意的诚实起点。完整检查和未解项见 `AUTHORING_REPORT.json`；六小时收益仍待证。
