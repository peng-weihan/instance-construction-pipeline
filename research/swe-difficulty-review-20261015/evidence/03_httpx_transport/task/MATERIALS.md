# 素材、转换和隔离

原始来源为 encode/httpx，Git URL `https://github.com/encode/httpx.git`，固定 commit `b5addb64f0161ff6bfe94c124ef76f6a1fba5254`，BSD-3-Clause（完整 LICENSE.md 保留）。作者在 job 的 material-src 完整 clone/checkout，125 个跟踪文件的逐文件 URL、大小与 SHA-256 见 authoring/source-manifest.json；不是只用候选卡预下载的五个文件。上游 auth flow、redirect、connect retries、取消清理是已有功能。

environment/project/submission 是该固定版本的完整跟踪源码快照。新增公开 `_execution.py` 只含不可变配置、事件/trace 值对象和异常类型；`_client.py` 增加可接受但未生效的配置参数；公开 development_tests 提供三个可运行例子。没有删除上游子系统，也没有把上游已有功能重新声称为缺陷。题目是一次逻辑 send 的物理执行账本这一原创扩展，约束均见 instruction.md。

私有参考修改真实 `httpx.Client` / `AsyncClient` 的 send 与 transport 分派链；复用原生认证、重定向、response history、cookies、transport routing 和 response ownership。新增懒惰 tee/cache 与 per-send ContextVar 只承载新政策。job 的 reference-branch 是从原 commit 派生的真实 git 分支，提交号见 provenance.json；solution/reference-httpx 是冻结可注入实现，reference.patch 为 starter→reference，authoring/inverse.patch 为精确逆向恢复。solve.sh 复制真实生产源码，没有固定分数或评测替换。默认写 Harbor submission；作者本地通过 HTTPX_SUBMISSION_DIR 指向 job 内隔离目录，实际运行并逐文件比对了注入结果。

私有 oracle 不调用参考实现生成答案。private/cases.json 中的响应脚本和独立预期在实现之外定义；受保护的 grader 控制响应、记录 transport 进入、实际请求字节、流读取和关闭，核对预算/历史/凭据与 trace。worker.py 仅把测试输入适配到原生 HTTPX 客户端，不含预期答案或奖励公式。原生回归来自固定上游源码，不接受候选改写的 tests/config。外部观察避免仅让实现和自己的序列化来回转换。测试和参考仍由同一作者设计，因此不能声称独立人员语义审查完成。

公开/反馈/作者审计三层：公开层为完整上游源码、公开合同和值对象、三个 development tests；正式反馈层是冻结的私有语义场景和 160 个可执行原生回归，七组等权；作者审计另检验 IDNA/端口 0、MockTransport 缓存旁路、connect 前未消费、嵌套禁用和真正 asyncio task cancellation，不用于事后挑选考生快照或修改正式分数。作者审计发现的两个参考 origin bug 已保留失败与修复后的证据。

私有目录、solution 与作者资料不进入 work image。独立 verifier image 以 root 保管私有资产和奖励；候选编译 UID 2101、执行 UID 2102，均清空补充组并受时间、内存、进程、文件和输出限制。候选只能访问自己的生产源码快照、公开 worker 和原生上游测试。真实权限探针验证两种 UID 均不能打开已知私有参考文件或写奖励；不仅检验目录列表。candidate 不与权威 Python scorer 共进程。Python 动态导入仍有通常的不可信插件攻击面；未声称已完成恶意候选红队审计或容器级隔离认证。

全部依赖锁在本包，wheel manifest 记录版本/hash/许可证元数据，wheel 内许可证保留。amd64 与 arm64 的 CPython 3.12 wheel 闭包已下载；amd64 本地离线安装、pip check 已实测，arm64 未执行。锁还包含可正常使用的 tenacity 与 hatch 构建工具；上游与参考均以原生 pyproject 实际构建 wheel 成功，构建日志保留。两个 Docker context 都独立含依赖，无父目录 COPY。FROM 使用所提供的 Python 3.12.8 manifest-list digest；本地检查解释器为 3.12.15，不能替代这个镜像的运行证据。

不得将整个 task（含 solution/verifier/authoring）挂进解题容器。候选卡、私有参考和测试历史仅供作者审阅；交付任务时只向 agent 发布 environment 与 instruction。源码本身公开，未来发布参考实现也会产生污染风险，应按源码谱系与本扩展机制分组，不按换 URL/测试种子计新题。
