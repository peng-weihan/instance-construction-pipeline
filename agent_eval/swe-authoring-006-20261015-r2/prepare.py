"""Prepare six independent native-author jobs on the user's newly added homes."""
from pathlib import Path
import ast
import hashlib
import json
import shutil

ROOT = Path('/ws/users/raymone/edgebench/swe-authoring-006-20261015-r2')
OLD = ROOT.parent / 'swe-authoring-016-20261015-r1'
tree = ast.parse((OLD / 'authoring/prepare_jobs.py').read_text())
common = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'common' for t in n.targets))
guidance = ROOT / 'guidance'
shutil.copytree(OLD / 'guidance', guidance, dirs_exist_ok=True)
focus = {
 '17_duckdb_execution': ('performance', '4', '''在真实 DuckDB 执行引擎中寻找正确性约束下的优化任务：聚合/TopK/排序、变长或嵌套键、并行合并、内存压力与 spill 的相互影响。先实测原生引擎和最强合理设置；不能把已有 spill 能力称作缺失，不能用人为慢参考、toy SQL 执行器或包装现成 CLI 冒充优化。至少考察三组有实际源码/issue/基准依据的候选 workload/瓶颈，再选一个真实可改进且能稳定判分的合同。吞吐/内存锚点只记录实测；共享宿主噪声若淹没改进，性能分明确禁用并 hold，不编数字。'''),
 '18_polars_streaming': ('engineering_evolution', '5', '''在真实 Polars 流式执行链中寻找有产品依据的新能力或跨层恢复：lazy plan 与有界 streaming state、checkpoint/resume、join/groupby、schema/order/null 语义之间的组合。所列方向是假设，先核对固定版本已有能力，并考察至少三个来自真实源码、公开需求或回归的合同。优先实现一个连贯新扩展而不是拼无关 issues。若普通 serialize-plan/materialize/replay 包装已经完整满足当前合同，否定该合同，继续筛其余候选；不要禁止合法库。任务必须通过真实 Polars API/引擎运行，不能替换成 Python 流处理玩具。'''),
 '19_ruff_project_analysis': ('engineering_evolution', '6', '''围绕真实 Ruff 的语义分析、规则诊断、作用域/导入解析和安全自动修复链寻找新工程任务。至少审阅三个来自原始源码/公开 issue/实际回归的候选需求，再选连贯、跨模块、可验证的真实扩展。多文件重导出/别名、重复 edit/fix、忽略规则和诊断一致性只是探索入口，不能假定 Ruff 本来支持或缺少这些合同。保留原生 CLI/库入口及回归，允许正常依赖；普通 wrapper 就能全过时先换有依据的合同，而不是用隐藏限制强行保留。'''),
 '20_libcst_project_migration': ('engineering_evolution', '4', '''以真实 LibCST 为基础构造一套有清晰产品规格的跨文件 API 迁移/重构能力，研究 scope-qualified names、import/reexport/alias、签名与调用点联合迁移、格式/注释保持和幂等重跑。先读至少三个真实 codemod/metadata 能力与需求候选，实测普通现成 codemod/visitor 的最强基线，选其不能直接完成的连贯需求。不要把 parser/serializer 已有能力说成新功能，也不要只做字符串替换或独立 AST helper。完整题面必须明确可支持的闭世界项目语义和不支持情形，不能声称解决一般动态 Python 的不可判定解析。'''),
 '21_coverage_context_merge': ('engineering_evolution', '5', '''以真实 coverage.py 的 collector/context/data/combine/report 链寻找新能力：跨进程上下文及分支数据合并、路径映射、来源/版本绑定、增量合并和可解释诊断之间的连贯合同。至少考察三个真实 issue/源码/回归支持的需求，验证已有 combine/dynamic-context 功能和普通 SQLite/公开 API 包装能覆盖多少。不能重出已有 combine 功能，不能无依据堆分支/进程数假造难度。做完整实际 coverage 工程演进，保留追踪/聚合/报告原生入口；若无可信新缺口，交具体 reject/hold 证据。'''),
 '22_sphinx_incremental_build': ('engineering_evolution', '6', '''围绕真实 Sphinx 的增量构建、依赖图、扩展事件、autodoc/include/toctree、并行读写与输出一致性寻找跨模块工程任务。至少审阅三个真实需求/已知失败行为，选一个确有缺口的连贯合同。用全量干净构建作为独立语义对照，同时实测普通 forced rebuild/已有 extension hooks 的最强基线；若全量重建已满足全部合理合同就不能把它假称错误。只有真实测量支持资源/增量约束时才能计性能，不设猜测的操作数或等待门槛。交真实 Sphinx 源码扩展及回归，不用目录生成 toy 代替。''')
}
jobs = []
for source in json.loads((ROOT / 'source-plan.json').read_text()):
    key = source['id']
    family, n, extra = focus[key]
    job = ROOT / 'jobs' / key
    job.mkdir(parents=True, exist_ok=False)
    (job / 'AGENTS.md').write_text('Authorized EdgeBench native AUTHOR workspace. Write only beneath this directory. Follow prompt.md. Do not start another model, subagent, teacher or cloud sandbox. Preserve shared/foreign files and all historical tasks.\n')
    prompt = common.format(base=ROOT)
    prompt += ('\n\n本批用户最新指令：阿里云账户资源配额已满，先继续造题；使用新增 raymone-04/05/06。'
        '本次仅做素材挖掘和完整任务构造，不启动教师、云实例、其他模型或子代理。'
        '容器启动有已知间歇 systemd/cgroup 故障；可以在本目录做可信本地构建/检查，不能重启/修改全局 Docker，不能把基础设施失败当有效零分。\n')
    prompt += f"\n固定来源：{source['url']}\n40位固定revision：{source['revision']}\n来源卡：{ROOT}/sources/{key}.json\n机制：{family}\n方向：{extra}\n"
    prompt += '''
额外必须阅读：guidance/factory-original/deepswe.md、programbench.md、nl2repo.md 和 factory-methods.md。
三套 factory 是方法参考，不是顺序阶段：真实需求演进优先 DeepSWE C；受控恢复可用 A，但必须有完整干净 gold 与逆补丁且缺口足够连贯；NL2Repo 帮助抽取真实规格；ProgramBench 的独立行为对照可用于测试，但不强行改成重实现题。

本次加强“来源/候选→题目”的步骤：
1. 完整获取固定源码、许可证与原生文档/测试，保存 hash；至少找到三个有原始证据的候选需求/瓶颈，写 CANDIDATE_MINING.json，逐项列证据 URL/本地源码位置、已有能力、便宜捷径、探针结果、筛选理由。
2. 一个初始提案被成熟包装否证，不能直接等同整个项目没有价值；在同一固定来源里继续检验其余候选。三者都不合适时仍应诚实拒绝，不强凑题，不临时禁用正常依赖。
3. 选中的任务覆盖真实跨模块行为，公开规格充分，保留基础可运行 starter。私有参考、保留集、反馈集分离；不得复制原 EdgeBench 评测题或使用隐藏评测数据。参考能运行不等于六小时难度。
4. 针对上一批已暴露的问题：Dockerfile 的 PATH 必须含需要的 /usr/sbin 等命令；私有测试复制到受限候选临时目录后的可读模式必须实测；不要依赖对只读 grader 根目录 chmod；测试/评分依据不能被候选输出、同进程 monkeypatch 或可写报告自证。
5. 产出完整 task/ 和 AUTHOR_RESULT.json、PROGRESS.md，阶段和缺项要真实。构造完成尽量交可审查实物，而不是计划；没有实物不能写 constructed_unverified。失败探针与被否证候选保留。两个有实质意义的后期改进路径只算假设，不估计虚假的“需要几小时”。
6. 不扫描或复用其他人的任务源码和账号，不读取 /proc/*/environ，不全局安装包，不运行模型基线。普通 source/build/test 子进程可以使用，每个构建最多 -j4；离线依赖、临时目录和下载缓存全部落在当前 job 里。
'''
    (job / 'prompt.md').write_text(prompt)
    jobs.append({**source, 'account': 'raymone/' + n,
        'codex_home': '/ws/users/wcgu/new-codex-group/raymone/' + n,
        'cwd': str(job), 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high',
        'family': family, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
        'expected_cli_sha256': '76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30'})
(ROOT / 'launch-plan.json').write_text(json.dumps({'phase': 'authoring_only', 'jobs': jobs,
    'teacher_runs_authorized_in_this_batch': False, 'model': 'gpt-6.1-sol'}, ensure_ascii=False, indent=2) + '\n')
print('PREPARED', len(jobs), flush=True)
