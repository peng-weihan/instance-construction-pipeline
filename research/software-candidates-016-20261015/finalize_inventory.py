import collections, datetime, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'plan.json').read_text()); design=json.loads((ROOT/'candidates.json').read_text()); manifest=json.loads((ROOT/'source-manifests.json').read_text())
by_id={x['id']:x for x in manifest['candidates']}
for item in p['candidates']:
 s=by_id[item['id']]
 s['files']=item['files']
 s['resolved_initial_404_paths']=item.get('initial_path_corrections',{})
 s['missing_paths']=[x for x in s['missing_paths'] if x not in s['resolved_initial_404_paths']]
 s['material_scope']='selected_primary_files_and_complete_git_tree_index_not_full_checkout_or_offline_dependencies'
 (ROOT/'sources'/s['id']/'manifest.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
(ROOT/'source-manifests.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
rows=design['candidates']; files=[f for s in by_id.values() for f in s['files_acquired']]
counts={'candidate_count':len(rows),'new_project_count':sum(r['new_source'] for r in rows),'revised_source_count':sum(not r['new_source'] for r in rows),'selected_source_files':len(files),'selected_source_bytes':sum(x['bytes'] for x in files),'complete_git_tree_indexes':sum(bool(s.get('tree_manifest')) for s in by_id.values()),'P1_count':sum(r['priority']=='P1' for r in rows),'P2_count':sum(r['priority']=='P2' for r in rows),'new_complete_task_profiles':0,'new_constructor_cli_runs_in_batch':0,'new_six_hour_rollouts_in_batch':0,'six_hour_qualified_tasks':0}
fam={'engineering_evolution':'工程演进','system_implementation':'系统能力实现','correctness_constrained_performance':'正确性约束的性能优化','implementation_recovery':'跨层实现恢复','behavioral_reimplementation':'行为兼容重实现'}
recipe={'engineering_evolution':'DeepSWE C + NL2Repo 的证据到规格','system_implementation':'NL2Repo 的合同恢复 + 独立系统参考','correctness_constrained_performance':'DeepSWE 补丁/回归 + ProgramBench 行为探针 + 实测性能','implementation_recovery':'DeepSWE A；先设计关联缺口，再保留完整逆补丁','behavioral_reimplementation':'ProgramBench 的 build/probe/差分 + 新组合合同'}
queue=[]
for i,r in enumerate(sorted(rows,key=lambda c:(c['priority'],c['id']))):
 queue.append({'id':r['id'],'priority':r['priority'],'state':'candidate_reviewed_not_started','candidate_card':f"cards/{r['id']}.md",'factory_recipe':recipe[r['family']],'model':'gpt-6.1-sol','reasoning_effort':'high','preferred_codex_home':p['author_codex_homes'][i%3],'launch_authorized_by_user':True,'requires_fresh_capacity_reservation':True,'requires_constructor_read_source_and_validate_gap':True,'six_hour_solver_launch_requested_for_this_batch':False,'next_output':f"constructed/{r['id']}/",'first_probe':r['first_falsification_probe']})
(ROOT/'authoring_queue.json').write_text(json.dumps({'status':'planning_inventory_not_process_status','jobs':queue,'do_not_bypass_shared_concurrency_guard':True},ensure_ascii=False,indent=2)+'\n')
report=['# 软件工程候选池：16 条真实素材路线','',
'**现有 6 条路线扩展为 16 个候选：6 个原来源重新定义更完整的范围，加 10 个新开源项目。** 每个候选均固定 40 位源码 commit、取得关键文件与许可、保存完整 Git 文件树索引，并写成可审阅的出题卡片。8 条建议先细化，另 8 条先做廉价解法筛选。优先级是下一步投入次序，不是难度通过标志。','',
f"本批实际落盘 **{len(files)} 个关键源码/文档/许可文件，{counts['selected_source_bytes']:,} 字节**；16 份 Git 文件树索引均未截断。这里只取得选读材料和文件索引，尚未下载/封装全部仓库、构建依赖、语言 grammar、参考服务和互通数据。下载成功不等于完整出题素材包就绪。",'',
'本批完成的是候选研究与构造输入，**没有新增完整题包、没有启动本批构造 CLI 或六小时求解运行**。旧六条小样保留原目录和结果；旧 profile 的 Oracle 或分数不能转移给这些扩大范围的新合同。科学/金融等已有运行不属于本批。','',
'## 16 个候选','',
'| # | 素材项目 | 拟出的题 | 机制 | 建议 | 来源 |','|---|---|---|---|---|---|']
short_tasks={
'01_openapi_streaming':'流式 SDK、认证覆盖、取消与资源生命周期',
'02_restler_recovery':'真实 campaign 的 checkpoint/journal/外部状态恢复',
'03_httpx_transport':'重试预算、可重放 body、认证/重定向与事件链',
'04_pytest_fixtures':'fixture 执行图、缓存失效与异常清理诊断',
'05_uv_resolution':'跨环境 lock 更新计划与约束解释',
'06_wasm_validation':'类型验证、模块链接与间接调用的 VM',
'07_arrow_ipc':'增量 IPC、嵌套类型与 dictionary 演化',
'08_http2_session':'HPACK、flow control 与多 stream 状态机',
'09_valkey_transactions':'RESP3 事务、WATCH、多客户端与日志恢复',
'10_datafusion_sort':'真实 SortExec/TopK/spill/分区合并优化',
'11_rocksdb_compaction':'耐久性和读写放大约束的 compaction 优化',
'12_croaring_kernels':'混合 bitmap 容器的批量操作与聚合优化',
'13_toml_lossless':'无损解析、span、table 编辑的跨 crate 恢复',
'14_tree_sitter_incremental':'增量解析、节点位置与错误恢复',
'15_jq_composition':'流、作用域、递归、更新路径与错误的兼容重实现',
'16_libarchive_cli':'tar/pax、链接、元数据与分段流的行为兼容'}
for r in rows:
 report.append(f"| {r['id'][:2]} | [{r['repo']}](https://github.com/{r['repo']}/tree/{r['revision']}) | [{short_tasks[r['id']]}](cards/{r['id']}.md) | {fam[r['family']]} | {r['priority']} | {'新增' if r['new_source'] else '原来源扩展'} |")
report += ['',
'五种机制是我们对原题的分析分类，分配为 5/4/3/2/2，并非官方子类或官方占比。原题对应关系见每张卡片；原题证据与可知边界沿用[36 道软件题逐项研究](../software-engineering-2026-10-15/REPORT.md)。这支持“同类但不同需求”的设计判断，还不能证明统计上的同分布、六小时难度相等或训练收益。','',
'## 哪些先做，哪些先否证','',
'**P1：OpenAPI SDK、RESTler、uv、WASM、Valkey、DataFusion、TOML、Tree-sitter。** 它们有可定位的跨层行为链，可以写出具体的中期与后期改进假设。先实现卡片里的最小否证探针，再决定是否投入完整参考解；P1 不表示已经验证了六小时潜力。','',
'**P2：HTTPX、pytest、Arrow IPC、HTTP/2、RocksDB、CRoaring、jq、libarchive。** 对应材料是真实的，但现成插件/库包装、普通参数设置或已有能力很可能解决大部分任务。先给强廉价基线机会；正常依赖能完整通过合理合同，说明该版本应淘汰或重新定义产品需求。不能临时禁止依赖、故意降速 baseline、隐藏公开算法或堆样例数量来补难度。','',
'关键材料观察：Arrow 提供格式定义和跨语言 runner，但这也意味着 wrapper 基线很强；HTTPX 的取消清理和 pytest 的 finalizer 已存在，新增需求必须明确；uv 已有 universal lock，不能重复出这项功能；RocksDB/CRoaring 的成熟优化意味着性能余量必须测量后才知道。','',
'## 怎样把这些材料交给三个 factory 方法','',
'- 工程演进：用 DeepSWE C 的需求→失败证据→参考改造，再用 NL2Repo 方法补足公开规格。issue 只能作为线索，先在固定版本复现；不能把已实现能力说成缺失。',
'- 系统能力实现：从规格与独立参考提取状态合同，给可起步的骨架，逐层实现；一次往返自检不能替代跨实现互通。',
'- 性能优化：保持真实引擎和独立正确性检查；先测 untouched 和强合理配置 baseline，再决定目标及归一化，不填写虚构性能端点。',
'- 实现恢复：按一个关联行为链设计受控缺口、保留逆补丁和原生回归；公开上游可能被记忆，不按删除行数估算新颖性或时长。',
'- 行为重实现：用 ProgramBench 式可观察参考与差分探针，同时定义进程内 API、CLI/文件状态等真实合同；先检查现成 binding 是否已经满足全部需求。','',
'[三个参考 factory 的实际能力与门禁](../software-engineering-2026-10-15/factory-methods.md)保持原有结论。原始规格和远端共享安装未修改；本批只新增自己的研究目录。','',
'## 训练分离与六小时证据','',
'新候选使用上述独立项目/新合同，不复制 EdgeBench 原始评测输入或私有 verifier。公开原题只用于机制和交付形态参照。后续生成的用例须分公开调试、重复反馈和作者质量审计集合；反馈集不能混入教师输入的参考答案。按源码谱系和机制做 split，特别是 OpenAPI/HTTPX、Arrow/DataFusion 这两组共享依赖关系，不能只靠随机 seed 宣称独立。','',
'每张卡片给出两条“早期基础完成后还可能做什么”的具体路径，但它们是设计假设。构造阶段先看最强廉价基线是否早满、是否存在真实跨模块缺口；只有后续真实六小时、多次运行曲线才能校准长程难度。无进展的六小时运行也不能算好题。本批不代替任务书的完整交付与验收。','',
'## 文件与可复现性','',
'- [16 张卡片的机器可读索引](candidates.json) / [CSV](candidates.csv)：设计、范围、风险、首个否证探针及原题参照。',
'- [源码获取清单](source-manifests.json) / [冻结的获取计划](plan.json)：原始 URL、字节数、SHA-256 与 commit；404 备选许可名不等于缺少许可，历史拼错路径的修正也保留。',
'- [作者输入队列](authoring_queue.json)：16 个未启动 job；P1 在前，指定 gpt-6.1-sol/high 和用户提供的三个 Codex home。启动前须有当时可用容量，preferred account 不代表已获得 slot。',
'- `harvest_sources.py` → `supplement_sources.py`：按固定 SHA 获取关键文件及全文件树；`write_cards.py`、`finalize_inventory.py` 只渲染研究产物，不生成题包或验证难度。','',
'三个远端路径此次已只读确认二进制存在且均为 codex-cli 0.160.0，配置模型均为 gpt-6.1-sol/high；这只是安装/配置确认，不是本批成功模型调用或正在构造的证据。',
'']
(ROOT/'REPORT.md').write_text('\n'.join(report)+'\n')
(ROOT/'README.md').write_text('# 16 个软件工程候选\n\n入口：[REPORT.md](REPORT.md)。完整候选是素材与设计，不是已验证题目。\n\n复现素材获取及报告渲染，逐条顺序执行：\n\n```sh\n.venv/bin/python research/software-candidates-016-20261015/harvest_sources.py\n.venv/bin/python research/software-candidates-016-20261015/supplement_sources.py\n.venv/bin/python research/software-candidates-016-20261015/write_cards.py\n.venv/bin/python research/software-candidates-016-20261015/finalize_inventory.py\n.venv/bin/python research/software-candidates-016-20261015/check_inventory.py\n```\n\n以上命令在 edgebench 根目录运行。不会启动模型或修改远端文件。\n')
(ROOT/'inventory-summary.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n')
req=ROOT.parent.parent/'requirements/current_phase.json'
s=json.loads(req.read_text());s['latest_request']='软工候选扩展至16个，使用用户指定raymone/1,2,3上的gpt-6.1-sol进行后续合成'
s['software_candidate_pool_016']={'directory':str(ROOT.relative_to(ROOT.parent.parent)),'report':str((ROOT/'REPORT.md').relative_to(ROOT.parent.parent)),**counts,'state':'source_evidence_acquired_design_proposed','authoring_queue':str((ROOT/'authoring_queue.json').relative_to(ROOT.parent.parent))}
req.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(counts,ensure_ascii=False))
