"""Render the six primary-agent source cards from recorded research decisions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DATA = [
    dict(id='37_tokio', repo='tokio-rs/tokio', route='M4',
         title='异步运行时的任务、计时器与关闭生命周期恢复', priority='hold_harness_probe',
         scope='对健康固定版本构造关联子系统的受控恢复：任务状态、通知/取消、计时器和runtime关闭共同可用。不是为现有Tokio修复一个已知上游bug。',
         existing_capability='固定源码已经实现原子任务生命周期、取消、通知和虚拟时间测试；这些是拟保留的gold能力。',
         proposed_gap='拟选择一组完整生命周期实现作受控缺口，保留公开API、健康I/O和可起步路径；具体mask、参考健康性和实际工作量尚未验证。',
         chain='spawn/JoinHandle → 原子任务状态 → scheduler通知 → timer → cancellation/shutdown',
         analogue='Rust multicrate/regex-automata恢复；不能按并发分支数量预言时长。',
         scenarios=['任务等待计时器时取消，再次唤醒不得重复完成，JoinHandle观察到合同内结果。',
                    '虚拟时间前进、计时器重设和任务自唤醒交错，完成与资源析构恰当。',
                    'runtime关闭时有等待、已通知和已完成任务，退出后资源被释放；不要求所有合法执行具有相同poll顺序。'],
         remaining_work_hypotheses=['基本spawn/join恢复后，通知与取消竞争仍需统一状态和引用所有权。',
                                    '单线程计时恢复后，关闭与多线程路径的组合可能需要跨模块修订。'],
         oracle='原生单线程/虚拟时间回归、选定并发模型检查和独立资源计数；比较合法结果/不变量，不比较偶然调度顺序。',
         cheap_baseline='使用最直接的锁式状态机、正常futures/同步工具或串行调度；若满足完整合同应允许通过。',
         first_probe='先在健康gold重放选定测试多次，证实不依赖wall-clock和偶然调度；再做一份独立锁式实现，评估是否快速闭合。',
         license_observation='根LICENSE为MIT；依赖及分发闭包后续逐项记录。',
         resources='Rust vendor与MSRV未验证；OS reactor及线程模型需分别验证Linux x86/ARM。并发检查不可把概率性失败写成确定奖励。',
         evidence=[('tokio/src/runtime/task/state.rs',117,'running/idle、通知、取消和引用计数协同'),
                   ('tokio/tests/time_sleep.rs',21,'原生暂停时间与计时器测试')],
         read_ranges=['state.rs:110-180','time_sleep.rs:18-70；其他已下载文件只做符号/结构定位']),
    dict(id='38_tantivy', repo='quickwit-oss/tantivy', source_repo_alias='tantivy-search/tantivy', route='M4',
         title='全文索引的写入、提交、读视图与失败恢复', priority='build_scope_probe',
         scope='恢复同一个全文索引工作区的写入/提交/删除、reader reload、segment管理和失败处理行为，形成建索引→查询→修改→重开的完整链。',
         existing_capability='健康上游已有IndexWriter/IndexReader、显式reload和commit失败测试；自动reload不是commit返回时同步可见。',
         proposed_gap='在健康参考上选择关联实现缺口，保留schema/公开API和可运行骨架。不是给原生Tantivy补一个其实已有的事务提交功能。',
         chain='schema/tokenization → writer/segment → metadata commit → reader reload → query/collector → GC',
         analogue='Rust内容寻址多crate恢复/Codeflash因果退化；实际mask尚未选定。',
         scenarios=['提交A→显式reload→保存旧searcher→提交B和删除→reload，新旧读视图各遵守公开契约。',
                    '在元数据保存失败时提交B被拒绝，重新打开仍只看到先前成功提交A；随后能继续写。',
                    '多segment合并/回收与查询并存，重开后文档集合、删除和排序结果保持一致。'],
         remaining_work_hypotheses=['基础索引可查询后，delete/commit/reload的可见性仍需跨层集成。',
                                    '正常提交恢复后，失败发布、segment生命周期和旧读视图可能仍需修订。'],
         oracle='小型独立文档集合/查询解释模型，加固定gold的API差分和原生failpoints；先限定查询语义及排序并列规则。',
         cheap_baseline='正常索引库或简单全量重建实现；全量重建若达到所有公开正确性/资源要求，应承认可行。',
         first_probe='完整gold使用Manual reload跑提交/删除/失败/重开纵向场景，再用正常全量重建基线比较；避免把异步reload窗口误判成bug。',
         license_observation='根LICENSE为MIT文本；子crate和压缩/分词依赖后续单列。',
         resources='Rust/Cargo离线闭包未构建；特定SIMD/文件系统行为需x86/ARM验证。测试优先显式reload与可控故障。',
         evidence=[('src/reader/mod.rs',15,'reload策略及commit返回不保证自动reload已完成'),
                   ('tests/failpoints/mod.rs',42,'保存元数据失败后新文档不可见的原生回归')],
         read_ranges=['reader/mod.rs:15-44','tests/failpoints/mod.rs:42-105；index_writer只做入口定位']),
    dict(id='39_rustls', repo='rustls/rustls', route='M4',
         title='TLS记录、握手恢复与应用I/O的关联状态恢复', priority='hold_harness_probe',
         scope='恢复固定Rustls版本的有限TLS1.3会话与记录生命周期实现，保留可信密码provider和证书fixture；不用手写密码原语增加工作。',
         existing_capability='上游已有early-data状态与长度检查、ticket获取/消费和多次恢复测试；不是待实现的上游功能。',
         proposed_gap='受控恢复跨握手/会话/应用数据的实现，具体缺口和参考互通尚未构造；需区别于原EdgeBench的Python trace状态机。',
         chain='record分片 → handshake状态/transcript → session ticket → early/app data → close/error',
         analogue='regex-automata式跨表示恢复；原TLS trace任务仅作机制参照，不复制其题目或检查。',
         scenarios=['完整握手取得ticket→多次尝试恢复→按参考契约消费ticket，耗尽后走完整握手。',
                    'early-data分片跨多个输入到达，长度超限或消息次序错误被拒绝；正常握手继续的边界需明确。',
                    '应用部分读写、对端关闭和alert交错，公开API返回与资源生命周期保持一致。'],
         remaining_work_hypotheses=['完整握手可用后，ticket消费、恢复兼容性及early-data状态仍可能未闭合。',
                                    '内存pair通过后，部分I/O、关闭和错误路径可能要求记录层与API协同。'],
         oracle='固定证书/随机源/crypto provider下的原生pair测试及独立TLS对端；随机密文不直接作逐字节相等判据。',
         cheap_baseline='保留crypto provider并用成熟TLS组件/API适配；如果正常适配就完成所有公开行为，应重估恢复范围。',
         first_probe='先编译健康gold及离线pair测试，再判断是否可确定地恢复完整状态链；验证引用原版TLS材料的重复风险。',
         license_observation='根LICENSE声明Apache-2.0、MIT、ISC三选一；三份文本均已取得，crypto及证书材料另核。',
         resources='密码provider可能带原生构建/汇编依赖；离线构建、固定熵源与x86/ARM未验证。本任务是基准素材研究。',
         evidence=[('rustls/src/server/tls13.rs',1245,'early-data上限及EndOfEarlyData推进状态'),
                   ('rustls-test/tests/api/resume.rs',327,'ticket使用、并行尝试和耗尽后不恢复的测试')],
         read_ranges=['server/tls13.rs:1240-1300','resume.rs:327-403；client/io文件只做关键词定位']),
]

DATA += [
    dict(id='40_rsync', repo='RsyncProject/rsync', route='M5',
         title='目录同步工具的过滤、链接、更新与多步状态兼容', priority='build_scope_probe',
         scope='明确支持范围内的本地目录同步替代实现：文件选择、目录层级、过滤/保护、链接、更新和itemized输出，连续多次运行后文件树及副作用与参考一致。远端协议首轮不自动纳入。',
         existing_capability='固定rsync已实现目录作用域过滤、删除、硬链接和增量更新回归。参考实现可用于作者观察，学生环境与被执行提交不委托目标rsync。',
         proposed_gap='构造新的兼容实现规格和可构建骨架；实现语言/部署约束须预先作为产品目标公开，普通文件/校验库保持允许。',
         chain='参数/过滤规则 → file list → generator决策 → receiver写入/链接 → 输出/退出 → 再次同步',
         analogue='Git→Zig的多命令/持久副作用兼容；范围限定为另一独立工具。',
         scenarios=['初次同步含硬链接的树→目标局部被改写→再次更新，内容与硬链接关系和输出保持参考契约。',
                    '按目录加载filter，P保护与普通exclude同时存在，再执行delete-excluded，检查最终集合和受保护文件。',
                    '首次同步后移动/删除/新增源文件，dry-run与实际运行，再次运行无多余变化；检查退出码与文件元数据。'],
         remaining_work_hypotheses=['基本复制完成后，过滤/保护/删除优先级仍可能要求统一决策模型。',
                                    '单次正确后，跨次增量、链接身份和dry-run/itemize一致性仍可能存在工作。'],
         oracle='固定reference＋独立文件树快照：内容、类型、链接关系、约定时间/权限和退出码。每场景独立临时根，固定locale/umask。',
         cheap_baseline='标准库全量copy＋现成ignore/path工具。若完整满足公开合同就允许；不凭空要求delta算法或用重复文件堆难度。',
         first_probe='在同文件系统普通UID下跑gold的过滤/硬链接/二次同步，再用简单全量复制方案验证是否只剩少量参数适配。',
         license_observation='根COPYING包含GPLv3文本及OpenSSL/xxhash例外；具体分发文件和第三方依赖单列。',
         resources='POSIX硬链接/时间精度/权限需统一；不以root专属chown或不同平台偶然输出作难点。远端SSH与daemon运行不在已取得运行证据内。',
         evidence=[('generator.c',320,'目录作用域filter及遇I/O错误时的删除决策'),
                   ('testsuite/delete_test.py',88,'保护规则与exclude在delete-excluded下的不同效果'),
                   ('testsuite/hardlinks_test.py',43,'改写后再次同步仍保持硬链接及跨批次场景')],
         read_ranges=['generator.c:320-363','delete_test.py:86-109','hardlinks_test.py:20-75；manpage仅定向定位']),
    dict(id='41_curl', repo='curl/curl', route='M5',
         title='HTTP传输CLI的重定向、重试、续传与输出兼容', priority='hold_wrapper_probe',
         scope='仅HTTP/1.1和明确列出的CLI契约，交付请求、响应、文件输出、续传、重试和错误的兼容替代实现；首轮不扩成curl全部协议。',
         existing_capability='原生curl已有Retry-After、退避、部分下载自动续传前提及协议级测试；这些是兼容目标而非新增上游需求。',
         proposed_gap='新的CLI/库交付规格与骨架尚未构造。若正常libcurl绑定或成熟HTTP库即可完成全部合同，此范围应降级，不临时禁库。',
         chain='命令配置 → 传输状态 → HTTP头/重定向 → retry/resume → 输出文件 → 退出码',
         analogue='Git式外部行为重实现；与既有HTTPX/mitmproxy共享HTTP语义谱系，数据划分须保留关联。',
         scenarios=['部分响应写文件后断开→按公开续传选项继续，服务端Range行为和最终字节均匹配。',
                    '重定向后收到可重试状态及Retry-After→有界重试→成功，检查请求链、输出及退出码。',
                    'chunked响应在完成前断开→报告部分文件错误，已有输出如何保留按固定reference确定。'],
         remaining_work_hypotheses=['普通GET完成后，重定向、凭据和重试/续传的交互可能需要统一传输状态。',
                                    '成功下载后，部分输出、header重置和失败退出仍可能要求跨模块修复。'],
         oracle='离线loopback脚本服务器记录wire和事件，固定reference给stdout/stderr/退出/输出文件差分；时间用可控逻辑或独立非计时判据。',
         cheap_baseline='libcurl绑定＋现成参数解析器，或成熟HTTP客户端；这是必须先给机会的强合法方案。',
         first_probe='先用libcurl绑定实现限定命令矩阵，若适配即可全部满足则当前profile不推进长程。不能据curl支持很多协议就声称该HTTP子集很大。',
         license_observation='根COPYING为curl版权及permission notice；测试/可选TLS依赖的许可后续核对。',
         resources='完整curl的TLS/HTTP2等依赖不自动进入任务。用本地服务可离线，但短写、文件时间与超时判据需稳定化。',
         evidence=[('src/tool_operate.c',332,'输出文件在重试中可否续传的严格前提'),
                   ('docs/cmdline-opts/retry.md',20,'重试状态、退避和Retry-After已有合同'),
                   ('tests/data/test207',38,'chunked传输提前断开返回CURLE_PARTIAL_FILE')],
         read_ranges=['tool_operate.c:332-355','retry.md:15-65','test207:1-62','test1059:1-30']),
    dict(id='42_cmark_gfm', repo='github/cmark-gfm', route='M5',
         title='GFM文档的解析、AST位置、扩展与渲染兼容', priority='hold_wrapper_probe',
         scope='一个可嵌入Markdown库及CLI，明确CommonMark/GFM子集、AST与source positions、分块输入和HTML输出契约；不只把固定文本转成HTML。',
         existing_capability='上游已有block/inline分层、GFM table等扩展、API source-position测试和扩展规范样例。',
         proposed_gap='拟构造独立兼容实现和统一API骨架；普通Markdown库是否已完整覆盖还未运行，不能把多个格式标签当新难点。',
         chain='UTF-8/chunks → block parsing → inline delimiter → extension nodes → AST/source positions → render/CLI',
         analogue='Expat式解析库/ABI兼容和Git式CLI行为；继承行为目标，不复制原题材料。',
         scenarios=['表格单元含转义pipe、嵌套inline和Unicode，AST及HTML按固定reference一致。',
                    '同一文档以不同输入切分喂入，结果和source positions一致；位置单位需先抽取真实API合同。',
                    '嵌套list/quote内扩展与原始HTML交互，切换公开渲染选项后输出及CLI失败行为保持兼容。'],
         remaining_work_hypotheses=['普通段落/列表渲染完成后，block与inline/扩展组合仍可能要求统一解析表示。',
                                    'HTML结果可用后，AST API、位置和分块输入兼容可能还有工程工作。'],
         oracle='规范＋固定reference差分，另以独立AST不变量检查位置/父子关系；新生成语料与引用的官方样例分开留来源。',
         cheap_baseline='pulldown-cmark、markdown-it等合法成熟实现加API适配。若全部输出/API要求可薄封装完成则降级，不事后禁止。',
         first_probe='先比较两种正常解析库对AST/位置/扩展/分块接口的覆盖，再选择真正需要新实现的完整范围。',
         license_observation='COPYING含BSD两条款及其他文件归属；test/extensions.txt头部单独标CC-BY-SA-4.0，不能把测试材料统一当BSD。',
         resources='源码C/CMake及scanner构建闭包未验证；纯文本/CPU适合离线，但Unicode位置、渲染选项和gold版本须固定。',
         evidence=[('extensions/table.c',189,'table行解析与inline内容、空cell和pipe处理'),
                   ('test/extensions.txt',39,'table与inline格式及Unicode组合的规范样例'),
                   ('api_test/main.c',996,'source position API场景'),
                   ('test/extensions.txt',6,'扩展测试文本单独声明CC-BY-SA-4.0')],
         read_ranges=['table.c:189-231','extensions.txt:1-75','api_test/main.c:990-1010；其他parser文件仅结构定位']),
]


def main():
    (ROOT / 'cards').mkdir(exist_ok=True)
    candidates = []
    for c in DATA:
        base = ROOT / 'sources' / c['id']
        manifest = json.loads((base / 'manifest.json').read_text())
        c['revision'] = manifest['revision']
        c['status'] = 'material_acquired_design_proposed'
        c.update(task_constructed=False, runtime_verified=False,
                 six_hour_difficulty_verified=False)
        c['source_manifest'] = f"sources/{c['id']}/manifest.json"
        c['card'] = f"cards/{c['id']}.md"
        c['evidence'] = [dict(path=f"sources/{c['id']}/files/{path}", line=line,
            claim=claim, url=f"https://github.com/{c['repo']}/blob/{c['revision']}/{path}#L{line}")
            for path, line, claim in c['evidence']]
        text = [f"# {c['id']} {c['title']}", '',
            f"路线：{c['route']}；优先级：{c['priority']}；状态：素材已取、范围待验证。",
            f"来源：[{c['repo']}](https://github.com/{c['repo']}/tree/{c['revision']})；固定版本 `{c['revision']}`。", '',
            f"**已有能力：** {c['existing_capability']}", '',
            f"**拟交付：** {c['scope']}", '', f"**拟缺口：** {c['proposed_gap']}", '',
            f"**工程链：** {c['chain']}", '', f"**原题参照：** {c['analogue']}", '',
            '**三个组合场景（设计）：**', '',
            *[f'{i}. {x}' for i,x in enumerate(c['scenarios'],1)], '',
            '**基础完成后的剩余工作假设：**', '',
            *[f'- {x}' for x in c['remaining_work_hypotheses']], '',
            f"**独立评测：** {c['oracle']}", '',
            f"**最强正常基线：** {c['cheap_baseline']}", '',
            f"**首个否证探针：** {c['first_probe']}", '',
            f"**许可观察：** {c['license_observation']}", '',
            f"**离线和资源：** {c['resources']}", '', '**已读证据：**', '']
        text += [f"- [{ev['claim']}](../{ev['path']}#L{ev['line']}) / [固定上游]({ev['url']})" for ev in c['evidence']]
        text += ['', '定向阅读范围：'+'；'.join(c['read_ranges'])+'。', '',
            '未构造题包、未运行gold/候选/容器/模型，未验证六小时难度。下载文件是选读材料，不是完整checkout或依赖包。', '']
        (ROOT / c['card']).write_text('\n'.join(text))
        candidates.append(c)
    (ROOT / 'remaining-candidates.json').write_text(json.dumps(
        {'candidates':candidates},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cards_written':len(candidates),'source_count':len(DATA)}))


if __name__ == '__main__':
    main()

