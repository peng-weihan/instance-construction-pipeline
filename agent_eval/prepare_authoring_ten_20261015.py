"""Prepare a bounded ten-author pool; deployment and launch are separate steps."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

LOCAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOCAL))
from edge_factory.swe import plan

NAME = 'swe-route-authoring-010-20261015-r4'
OUT = LOCAL / 'runs' / NAME
REMOTE = Path('/ws/users/raymone/edgebench') / NAME
PREVIOUS = Path('/ws/users/raymone/edgebench/swe-route-authoring-005-20261015-r3')
PREVIOUS_LOCAL = LOCAL / 'research/swe-pipeline-v2-20261015/source-registry.json'
CLI_SHA = '76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30'

REPAIRS = [
    ('23_scrapy_product_roadmap', '28_scrapy_complete_r2', 4,
     '保留六组真实产品能力的完整范围。在新副本独立检查公开契约是否足以解释原生测试的内部结构假设、候选是否能伪造测试输出/修改结果文件，然后实际修复题包和可信评分边界。完整参考、starter、正常插件/包装基线及至少两份真实partial重放。完成独立agent/verifier镜像以及原生Harbor Oracle/NOP和同快照partial双入口验证。已有253用例、参考1.0、B约0.39只是作者旧主机证据，不能照抄为新镜像结果。若范围仍像小feature，依据固定源码扩大真正产品目标并明确新题版本，而不是加同构测试。'),
    ('24_lark_system_reconstruction', '29_lark_verifier_repair_r2', 5,
     '最高优先级修复零实现可打印worker成功帧获得1.0的已复现评分漏洞。参考、私有期望、比较逻辑必须在可信父进程/隔离空间；不把私有断言和预期放进候选解释器，不相信候选自报pass/fail。把旧exploit复制为必须失败的回归，增加合法行为相同的正确实现/真实partial控制，防止只按输出标记或文件名封堵。保留完整grammar→lexer→parser→tree/transformer→组合/诊断合同，不通过删难测能力缩小任务。复查普通库包装0.72的剩余工程空间。完成可信行为评分、完整题包及镜像/原生双入口控制；源码/测试/包内git和字节码不得漏出目标实现。'),
    ('26_ripgrep_multicrate_reconstruction', '30_ripgrep_complete_r2', 4,
     '补齐跨crate搜索执行器和Standard/Summary/JSON报告的完整恢复题，不缩小现有生产范围。旧主机F2P428/P2P789、B约0.604仅作待重放证据；先独立检查公开契约、结构耦合测试偏差、cargo/test输出伪造、候选编译身份和私有文件访问。可信父进程应依据实际行为判分，不能把不可信测试程序打印通过数作为唯一权威。完成题包自身可重建的固定依赖、独立镜像、Oracle/NOP、两份真实partial双入口；验证工作镜像没有完整gold、git对象、编译产物或逆补丁。保留初始范围及历史分数，修改评分语义必须新修订说明，不用性能分/虚构等待制造难度。'),
    ('27_ninja_behavioral_port', '31_ninja_full_rust_reference_r2', 5,
     '继续完成真实Rust行为兼容重实现题。旧版reference满分依赖官方C++，合法Rust solution只有44/135，不能交付假满分Oracle。在保留135条已公开能力合同、manifest/增量状态/depfile/dyndep/pool/rsp/工具/诊断完整范围的前提下，实际写出可重建的Rust完整参考并修复相关题包。允许正常Rust依赖；不能通过调用原Ninja/C++源码或缩减测试来补满分。先确认题面覆盖所有测试语义；有非合同断言应公开说明并在新版本修正，不能回写旧结果。固定依赖、隔离编译权限、候选同资源控制，完成Docker和原生Oracle/NOP/partial。不要完成一个薄Rust包装后再次泛泛held，尽力完成已定位的工程缺口，遇到真实不可行问题给可复现证据。'),
]

NEW = [
    ('32_mkdocs_product_roadmap', 'M1', 'mkdocs/mkdocs', '2862536793b3c67d9d83c33e0dd6d50a791928f8', 4,
     '调查固定MkDocs真实文档构建产品：配置验证/组合、文件与导航模型、插件生命周期、Markdown链接/资源处理、多步构建与诊断。比较至少三个完整产品里程碑范围，选择多组实际有价值的需求及跨阶段集成；现版本已有的能力必须明确，可在验证完整gold后恢复大范围子系统或从有证据的旧版本需求链构造。不是改主题、单个链接检查器或缓存插件。原生插件和普通库组合都作为强B真实测试。要求自然局部反馈、完整可运行参考、独立可信行为评分，来源新且不复制EdgeBench或Sphinx旧题测试。'),
    ('33_sqlglot_system_reconstruction', 'M2', 'tobymao/sqlglot', '021991fb9a63060e2f71aeac48e134f67c77227f', 5,
     '从固定真实SQLGlot抽取完整SQL工具引擎契约：token/parse→AST→作用域和名称解析→查询变换/生成→方言与错误语义，调查多个完整核心范围。优先覆盖真实SELECT/CTE/子查询/连接/窗口及多阶段变换链，避免只做几个SQL正则重写。目标不是复刻所有方言全部API；需完整而边界清楚的大型子系统。参考来自真实上游、测试与规格独立核验。正常sqlparse等库可用并作为强B，目标SQLGlot实现及等价包/缓存不放入学生环境。可信父进程判断候选输出AST/SQL/执行等价，私有断言不与候选共解释器。'),
    ('34_lz4_codec_optimization', 'M3', 'lz4/lz4', '48bfbfe351c5d6ea87d4af5557705e87755844e0', 6,
     '从固定LZ4真实源码、格式规范、压缩/解压/流式或dictionary执行路径，比较至少三个有实际算法空间的优化范围。测试普通compression level、既有fast/HC、普通dispatch等强配置，再决定是否有真实收益；不把现成库性能降级后当起点。优化必须兼容原格式并通过安全/边界/流式差分约束；代表性公开可分发或自生成语料应覆盖可压缩性/长度/字典/资源取舍，不只选择参考占优案例。实际独立计时、在线候选同快照配对重评；隔离共享机器噪声，性能奖励需明确启用和真实B/R锚点，若只能获得噪声或调参即饱和则有证据拒绝，禁止造虚假性能空间。'),
    ('35_click_multimodule_reconstruction', 'M4', 'pallets/click', '2247b35ea1c47c727d7a06e51fa280e12a863ff6', 6,
     '从固定完整健康Click恢复有规模的CLI框架能力：参数解析/类型和多值语义、Context层级/默认/环境、Group/Command分派与链式调用、错误/帮助/生命周期及shell completion等。比较三个连贯完整范围；选择多个生产模块及其依赖共同支持的行为包，保留API骨架和周边健康行为，不是删几个条件或一层decorator。跑完整gold，真实记录F2P/P2P以及跨模块partial。普通argparse/其他CLI库可用且作独立强B；目标Click源码/安装包/字节码及git对象严格不进公开环境。通过可信父进程或外部CLI调用观察退出码/输出/状态，不让candidate打印通过数决定reward。'),
    ('36_yq_rust_behavioral_port', 'M5', 'mikefarah/yq', 'a814ff5166040ec745a96bddd79ee31c3a548e83', 5,
     '调查真实yq的完整核心数据变换行为，构造Rust兼容替代题：表达式求值/选择/递归/更新、多文档YAML/JSON、类型标签/锚点语义、格式与错误、就地编辑及多步文件副作用。比较三个有实际规模的核心范围并明示支持边界，不能只包一个jq子进程或支持几个flag。正常serde/YAML/表达式/系统工具允许，最强合法包装实测作为B；目标Go yq实现不得直接作为考生替代实现委托。完整合法Rust参考必须实际可运行达到声明上限，否则如实缺项；可信参考只用于作者/独立判分。冻结原输入/输出/退出码和文件多步行为，部分实现按真实维度得分，不只比较stdout。'),
    ('37_jinja_template_engine', 'M2', 'pallets/jinja', '5ef70112a1ff19c05324ff889dd30405b1002044', 4,
     '候补：根据固定真实Jinja抽取完整模板引擎核心契约，比较词法/表达式/控制流、上下文/宏/继承/加载器、自动转义/未定义/错误三类完整范围及其集成。采用完整系统构造，保留正常依赖且实测成熟普通模板库包装能覆盖多少。不能只做变量替换和几个if，也不要求整个上游可选生态。目标Jinja完整实现及副本不进学生环境，可信父进程比较实际渲染和状态/错误，隐藏expected与candidate解释器分离。'),
]

SUPPLEMENT = '''

本批执行补充（用户已明确要求同时10条出题，以下取代旧提示中不完整的操作边界）：
- 本会话是明确授权的gpt-6.1-sol原生CLI作者。完成素材、题面、完整参考、可信评分器和可运行题包；不要把计划当交付，也不要因为允许held而跳过可修复工程缺口。
- 允许当前job内正常构建/测试，以及有唯一job标签的独立Docker agent/verifier镜像构建和model-free Oracle/NOP/partial Harbor检查。禁止启动任何教师模型、额外CLI agent、子代理、云沙箱；禁止修改共享daemon、共享镜像tag、原始skill/旧题包/其他job。Docker容器不能挂载账号目录或docker.sock。
- work/judge分开；评分服务不是常驻；所有得分完全取自文件快照。评分常量、分母、权重机器可读，native reward与周期score同权威。环境依赖要闭合，留意此前Sphinx缺git、正式CLI缺strace的教训，不把依赖异常写0分。
- 作者本地跑的控制是构造证据，不是6h模型难度证据。初始旧SWE题出现3.5～14分钟满分；因此真正在题目里增加完整系统能力与兼容面，不靠等待、加同构case、降低B或重映射历史分数。
- 保护评分权威：私有expected/断言不与candidate在同一个解释器内；不能信candidate打印的pass计数/worker成功帧。编译/导入/执行均按不可信候选降权、隔离私有数据，可信侧比较实际行为。添加打印伪造成功、读取已知私有路径、写reward、残留子进程等针对性控制，并留真实证据。
- 构建最多-j2/CARGO_BUILD_JOBS=2；每次大编译/镜像前检查磁盘。不要拷贝旧target/build/cache/虚拟环境；从固定源码和依赖重建。独立使用自己的输出/镜像/容器，无全局prune。旧素材可只读参考，需闭包复制到本题才能计交付。
- 对普通任务交完整合法参考，而不是用不符合语言/约束的上游gold冒充满分solution。开放优化题可按规范声明open-solution并交可运行强参考/真实分值；不能人为拉到1.0。
- 输出完成/缺口均给明确可执行下一步和证据；不把静态gate通过写accepted。没有ARM/6h证据就写未验证。
'''


def main():
    old = {j['id']: j for j in json.loads(PREVIOUS_LOCAL.read_text())['jobs']}
    jobs = []
    for previous_id, name, account, brief in REPAIRS:
        j = dict(old[previous_id])
        j.update(id=name, account=f'raymone/{account}',
                 codex_home=f'/ws/users/wcgu/new-codex-group/raymone/{account}',
                 source_job=str(PREVIOUS / 'jobs' / previous_id),
                 work_kind='repair_and_complete_new_copy', scope_brief=brief)
        jobs.append(j)
    for name, route, repo, revision, account, brief in NEW:
        jobs.append(dict(id=name, route=route, repo=repo,
                         url=f'https://github.com/{repo}.git', revision=revision,
                         account=f'raymone/{account}',
                         codex_home=f'/ws/users/wcgu/new-codex-group/raymone/{account}',
                         expected_cli_sha256=CLI_SHA,
                         work_kind='new_material_candidate',
                         standby=name.startswith('37_'), scope_brief=brief))
    registry = LOCAL / 'runs' / (NAME + '-source-registry.json')
    registry.write_text(json.dumps({'jobs': jobs, 'selection_status': 'pinned source candidates, scope not yet validated',
                                   'pins_observed_utc': '2026-10-15T13:40:52.628387+00:00'}, ensure_ascii=False, indent=2) + '\n')
    plan(registry, OUT, REMOTE)
    data = json.loads((OUT / 'launch-plan.json').read_text())
    data.update(target_concurrent_authors=10,
                existing_author_status=str(PREVIOUS / 'jobs/25_datafusion_execution_optimization/status.json'),
                replaces_prior_batch=False,
                user_authorization='Use 10 authoring sessions concurrently; gpt-6.1-sol and accounts raymone/1..6 already authorized.')
    for j in data['jobs']:
        p = OUT / 'jobs' / j['id'] / 'prompt.md'
        addition = SUPPLEMENT
        if j.get('source_job'):
            addition += f'''\n本题是返修新版本。旧输入只读：{j['source_job']}。部署后当前job下 previous-input/ 是不含构建缓存的素材/题包副本，之前的报告只作历史输入。请先读 previous-input/AUTHOR_RESULT.json、SCOPE_CARD.json、REQUIREMENTS.json、task/instruction.md，建立 REPAIR_PLAN.json。保留previous-input不变，在当前job/task及其他当前输出创建新版本；不得修改旧job。逐项解决本题scope_brief中的缺口，再重放实际控制。复制进来的旧成功报告不可冒充本轮执行。\n'''
        addition += f'''\n先读 {REMOTE}/guidance 下的作者规范、三套factory原始规约、范围要求、actual Harbor schema。源码语义以固定revision为准；新仓库至少先比较三个完整范围。静态检查：PYTHONPATH={REMOTE}/controller python3 -m edge_factory.swe gate --job {j['cwd']} --output {j['cwd']}/STATIC_ADMISSION.json 。它不能代替真实运行。可只读参考 /ws/users/raymone/edgebench/swe-rollouts-005-20261015-r5/framework 中的实际Harbor/独立判分代码，在本题复制需要的无凭据部分后使用；不要写入那里的运行目录。\n'''
        p.write_text(p.read_text() + addition)
        j['prompt_sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT / 'launch-plan.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    scripts = OUT / 'scripts'; scripts.mkdir()
    shutil.copyfile(LOCAL / 'runs/swe-route-authoring-005-20261015-r3/scripts/worker.py', scripts / 'worker.py')
    print(json.dumps({'prepared_jobs': len(jobs), 'new_to_start_if_previous_alive': 9, 'target_concurrent': 10, 'output': str(OUT)}))


if __name__ == '__main__':
    main()
