from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'authoring/prepare_jobs.py').read_text())
common=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='common' for t in n.targets))
candidates=json.loads((ROOT/'inputs/candidates.json').read_text())['candidates']
plan=json.loads((ROOT/'launch-plan.json').read_text());known={j['id'] for j in plan['jobs']}
notes={
 'engineering_evolution':'Use the real production repository and native entrypoints. Define a coherent NEW extension contract after checking current abilities. Implement a true reference branch. Do not call pre-existing functionality missing, and do not substitute a toy helper for the full cross-module behavior.',
 'system_implementation':'Freeze a bounded but substantive protocol/format/state-machine contract from primary sources. Build an executable independent reference and real starter. Measure the ordinary mature binding/wrapper baseline first; preserve legitimate tool use and never add arbitrary bans to fabricate difficulty.',
 'correctness_constrained_performance':'Optimize the ACTUAL pinned engine/library and preserve independent correctness. First obtain a genuine unmodified and strongest ordinary configuration baseline on the actual host. Never substitute toy timing or invent anchors. If no measurements are feasible, package with performance score explicitly pending/disabled, not a fabricated numerical result.',
 'implementation_recovery':'Construct linked recovery gaps across a real behavioral chain, not just four trivial helper masks. Retain initial useful behavior and native regressions. Preserve untouched gold/inverse patches privately. Label any gold-derived partial controls as such; they do not prove independent cheap solvability or solver time.',
 'behavioral_reimplementation':'Use a genuine CLI/ABI/stateful behavior contract and independent fixed reference. Preserve normal library/tool availability. If an ordinary existing library fully satisfies a reasonable contract, document the actual shortcut and hold/reject rather than pretending it is a difficult six-hour task.'}
created=[]
for c in sorted(candidates,key=lambda x:(x['priority'],x['id'])):
 if c['id'] in known:continue
 cid=c['id'];d=ROOT/'jobs'/cid;d.mkdir(parents=True,exist_ok=True)
 assert not (d/'status.json').exists(),'preserve existing run'
 (d/'AGENTS.md').write_text('Authorized EdgeBench AUTHOR directory. Only write beneath this directory. Follow prompt.md and source card. Never start another model/subagent/cloud or six-hour solver; never modify shared/foreign files. Preserve private reference isolation and report evidence honestly.\n')
 details={k:c[k] for k in ['proposed_task','existing_capability','artifact_scope','reference_plan','score_dimensions','post_two_hour_hypotheses','cheap_strong_baseline','first_falsification_probe','construction_risks','previous_profile']}
 prompt=common.format(base=ROOT)+f"\nSOURCE: {c['repo']} at {c['revision']}\nCARD: {ROOT}/inputs/cards/{cid}.md\nSOURCE MANIFEST: {ROOT}/inputs/sources/{cid}/manifest.json\nBATCH REPORT: {ROOT}/inputs/REPORT.md\n\nSPECIFIC MECHANISM: "+notes[c['family']]+'\n\nRESEARCHED PROPOSAL (check against actual source, improve if needed):\n'+json.dumps(details,ensure_ascii=False,indent=2)+'\n\nThe user has now explicitly requested ALL sixteen candidate authoring attempts. Produce a concrete package if the contract is worthwhile; retain an honest evidence-backed hold/reject if the mandatory strong baseline falsifies its value. Do not count copied gold-derived controls as independent cheap solutions. Do not launch a teacher.\n'
 (d/'prompt.md').write_text(prompt)
 plan['jobs'].append({'id':cid,'account':None,'codex_home':None,'model':'gpt-6.1-sol','reasoning_effort':'high','cwd':str(d),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'source_revision':c['revision'],'priority':c['priority'],'dispatch_policy':'all_authorized_launch_on_fresh_actual_capacity'})
 created.append(cid)
plan['all_candidates_authorized']=True;plan['target_candidates']=16
p=ROOT/'launch-plan.json';tmp=p.with_suffix('.all-prepared.tmp');tmp.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
(ROOT/'all-candidates-queue.json').write_text(json.dumps({'authorized_total':16,'new_pending':created,'excluded_existing':['01_openapi_streaming','09_valkey_transactions','14_tree_sitter_incremental'],'model':'gpt-6.1-sol','phase':'authoring_only'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_candidates':len(plan['jobs']),'new_jobs_prepared':len(created),'pending':created}))
