# 产品演进与 CLI 兼容方向潜力复评

前序素材池证明来源丰富；本组进一步判断正常依赖允许时，拟题范围还剩多少真实软件交付。这里按同一语义能否跨阶段闭合、状态能否独立观察、简单方案是否足额来排序，供系统/性能/恢复方向横向比较。

本组 15 项：A=4, B=6, C=5, D=0。A 是优先做基线和健康参考的投入判断，不是难度合格结论；没有任何求解时长/成功概率实测。

Alembic、mitmproxy、Task、SQLFluff 最值得先试。它们的关键是对象身份保持、动态会话身份、成功缓存条目身份、模板源位置分别要穿过多阶段及失败生命周期。允许成熟底层依赖仍存在可自然定义的完整交付；但是仍应让最强包装/插件基线先尝试，基线成功就降级。

Celery 和 APISIX 上限高，作者成本也高。前者需可控真实 broker、确认窗口和副作用账本；后者需稳定 OpenResty 多 worker 与独立请求版本观测。高成本不等于求解难度。curl/GFM/Pandoc 的主要未知是成熟库是否已经满足行为合同；tox 的主要未知是锁+记录包装是否足额。

Sphinx、Hatch、Fastify、dbt、fd 当前应重设或先做短探针。理由不是项目小，而是现有事件/锁定/取消/选择/遍历能力已成熟，拟增加部分可能被普通扩展或组合直接完成。不能靠更多 flags、目录、平台或任意禁库恢复高难外观。

跨组注意：SQLFluff 的模板语义与本池 Jinja/dbt 来源共享谱系，GFM 与 Pandoc 共享 Markdown 语义。它们可产生不同产品任务，但不能按仓库名视作完全独立任务族。【待主验证】是否与系统/恢复组最终选择的范围构成实质重复，应按语义单元和健康参考划分。

## 逐项判断

|素材|档位|上限|作者成本|决定性验证|
|---|---|---|---|---|
|28_alembic|A|high|medium|用最短 Rewriter 加正常插件先做关联表/列 rename，并用真实数据执行升级降级；再叠加一个同次属性变化。|
|29_sphinx|C|medium|medium|用原生事件扩展实现保留 mtime 的 include 修改、迁移缓存、串并行重跑三个旅程。|
|30_mitmproxy|A|high|medium|最小 addon 捕获 JSON ID 并替换 path/header，跑两个交错会话加一次中途取消；同时允许原生插件组合。|
|41_curl|B|high|medium|直接用 libcurl 绑定加参数解析器完成一条断连后续传和一条重定向后重试旅程。|
|42_cmark_gfm|B|high|medium|用一个成熟 GFM 库适配 table+inline 的 AST/sourcepos，并让同一文档分块喂入后比较三种输出。|
|43_tox|B|high|medium|先用 flock+现有 journal/results 包装依赖矩阵，做一次持锁 SIGINT 后恢复与一次输入变更重跑。|
|44_hatch|C|medium|medium|原生 env lock+uv/pip wheelhouse 归档，换目录禁网安装两个环境并执行项目命令。|
|45_celery|B|high|high|用原生 revoke/errback+事务 outbox 做一条有副作用的取消链；强制一次确认边界重投递，看成熟组合是否全部完成。|
|46_fastify|C|medium|low|以 scoped hooks、已有 request.signal 和标准并发控制库写最短插件，执行排队取消与 handler 超时两个旅程。|
|47_task|A|high|medium|先用 sha256+tar 包装现有 Task，覆盖删输出恢复、变量变更以及一次命令失败；定位包装仍无法获得的调用身份或生命周期语义。|
|48_apisix|B|high|high|先用全量原子文件替换+短预检，同时发版本标记请求；注入一个未知插件并重启一个 worker，检查是否已有完整 last-good 语义。|
|49_dbt|C|medium|high|仅用当前原生命令和归档脚本生成、迁移并重放一份含 state 与独立 defer-state 的审查包。|
|71_fd|C|medium|low|成熟 ignore/walk 加常规进程执行器，完成嵌套 ignore 和带特殊路径的 batch exec，比较真实 argv。|
|74_sqlfluff|A|high|high|把候选规则映射到成熟替代 parser/formatter，用空渲染占位符加相交修复完成一条完整源回写旅程，看适配缺口是否仍真实。|
|75_pandoc|B|high|high|成熟 reader/AST/writer 组合先做 YAML Markdown metadata+嵌套脚注+filter 的单条完整旅程，比较 AST 与 HTML。|

## 实际阅读范围

本次是基于固定版本摘录的定向潜力快评。每项核对了实现及测试/规格；没有重新 clone 全仓、没有运行 baseline/gold/solver，没有达到或宣称 repo-analyzer 全仓快速架构模式的 30% 核心模块覆盖。下面只记录实际请求并读到的源码行区间，不能外推为全仓审计。

|素材|文件|实际读行|类型|
|---|---|---|---|
|28_alembic|research/software-materials-expansion-20261015/sources/28_alembic/files/alembic/autogenerate/compare/tables.py|83–128|implementation|
|28_alembic|research/software-materials-expansion-20261015/sources/28_alembic/files/tests/test_autogen_diffs.py|1837–1887|test_or_spec|
|28_alembic|research/software-materials-expansion-20261015/sources/28_alembic/files/docs/build/autogenerate.rst|150–180|test_or_spec|
|28_alembic|research/software-materials-expansion-20261015/sources/28_alembic/files/alembic/operations/ops.py|1444–1490|implementation|
|29_sphinx|research/software-materials-expansion-20261015/sources/29_sphinx/files/sphinx/environment/__init__.py|849–895|implementation|
|29_sphinx|research/software-materials-expansion-20261015/sources/29_sphinx/files/tests/test_environment/test_environment_record_dependencies.py|14–17|test_or_spec|
|29_sphinx|research/software-materials-expansion-20261015/sources/29_sphinx/files/doc/extdev/event_callbacks.rst|32–83|test_or_spec|
|30_mitmproxy|research/software-materials-expansion-20261015/sources/30_mitmproxy/files/mitmproxy/addons/clientplayback.py|174–230|implementation|
|30_mitmproxy|research/software-materials-expansion-20261015/sources/30_mitmproxy/files/test/mitmproxy/addons/test_serverplayback.py|209–254|test_or_spec|
|41_curl|research/software-materials-expansion-20261015/sources/41_curl/files/src/tool_operate.c|332–380|implementation|
|41_curl|research/software-materials-expansion-20261015/sources/41_curl/files/tests/data/test207|1–62|test_or_spec|
|42_cmark_gfm|research/software-materials-expansion-20261015/sources/42_cmark_gfm/files/extensions/table.c|189–236|implementation|
|42_cmark_gfm|research/software-materials-expansion-20261015/sources/42_cmark_gfm/files/api_test/main.c|996–1045|test_or_spec|
|43_tox|research/software-materials-expansion-20261015/sources/43_tox/files/src/tox/session/cmd/run/common.py|424–480|implementation|
|43_tox|research/software-materials-expansion-20261015/sources/43_tox/files/tests/session/cmd/test_depends.py|15–68|test_or_spec|
|43_tox|research/software-materials-expansion-20261015/sources/43_tox/files/src/tox/session/cmd/run/common.py|231–278|implementation|
|44_hatch|research/software-materials-expansion-20261015/sources/44_hatch/files/src/hatch/env/lockers/uv.py|66–112|implementation|
|44_hatch|research/software-materials-expansion-20261015/sources/44_hatch/files/tests/cli/env/test_lock.py|376–425|test_or_spec|
|45_celery|research/software-materials-expansion-20261015/sources/45_celery/files/celery/backends/base.py|1403–1454|implementation|
|45_celery|research/software-materials-expansion-20261015/sources/45_celery/files/t/unit/tasks/test_canvas.py|1140–1191|test_or_spec|
|46_fastify|research/software-materials-expansion-20261015/sources/46_fastify/files/lib/route.js|534–585|implementation|
|46_fastify|research/software-materials-expansion-20261015/sources/46_fastify/files/test/hooks.test.js|3419–3475|test_or_spec|
|47_task|research/software-materials-expansion-20261015/sources/47_task/files/internal/fingerprint/sources_checksum.go|31–88|implementation|
|47_task|research/software-materials-expansion-20261015/sources/47_task/files/task_test.go|502–550|test_or_spec|
|47_task|research/software-materials-expansion-20261015/sources/47_task/files/task.go|127–310|implementation|
|48_apisix|research/software-materials-expansion-20261015/sources/48_apisix/files/apisix/core/config_yaml.lua|305–365|implementation|
|48_apisix|research/software-materials-expansion-20261015/sources/48_apisix/files/t/admin/standalone-plugin-validation.t|48–104|test_or_spec|
|48_apisix|research/software-materials-expansion-20261015/sources/48_apisix/files/apisix/core/config_yaml.lua|150–209|implementation|
|49_dbt|research/software-materials-expansion-20261015/sources/49_dbt/files/crates/dbt-scheduler/src/node_selector.rs|68–124|implementation|
|49_dbt|research/software-materials-expansion-20261015/sources/49_dbt/files/crates/dbt-state/src/explain/tests.rs|29–85|test_or_spec|
|49_dbt|research/software-materials-expansion-20261015/sources/49_dbt/files/crates/dbt-defer/src/lib.rs|63–111|implementation|
|71_fd|research/software-materials-expansion-20261015/sources/71_fd/files/src/exec/job.rs|45–63|implementation|
|71_fd|research/software-materials-expansion-20261015/sources/71_fd/files/tests/tests.rs|1974–2030|test_or_spec|
|74_sqlfluff|research/software-materials-expansion-20261015/sources/74_sqlfluff/files/src/sqlfluff/core/linter/linter.py|457–510|implementation|
|74_sqlfluff|research/software-materials-expansion-20261015/sources/74_sqlfluff/files/test/core/linter/fix_test.py|211–251|test_or_spec|
|74_sqlfluff|research/software-materials-expansion-20261015/sources/74_sqlfluff/files/src/sqlfluff/core/templaters/jinja.py|825–903|implementation|
|75_pandoc|research/software-materials-expansion-20261015/sources/75_pandoc/files/src/Text/Pandoc/Readers/Markdown.hs|67–111|implementation|
|75_pandoc|research/software-materials-expansion-20261015/sources/75_pandoc/files/test/Tests/Readers/Markdown.hs|510–550|test_or_spec|

本组的 A/B 范围先交付可淘汰的基线探针，之后再与系统、性能和恢复方向比较预算与构题优先级。
