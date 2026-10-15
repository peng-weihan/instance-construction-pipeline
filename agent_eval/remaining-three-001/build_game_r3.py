from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
src=ROOT/'samples/remaining-three-built-001/game-task-r2';dst=src.with_name('game-task-r3');shutil.copytree(src,dst)
runtime=(src/'verifier/runtime.py').read_text()
runtime=runtime.replace('def command(work, argv, readonly=()):','def command(work, argv, readonly=(), seed=None):')
runtime=runtime.replace("    cmd+=['--']", "    if seed is not None:cmd+=['--setenv','EDGE_GAME_RNG_SEED',str(int(seed))]\n    cmd+=['--']")
runtime=runtime.replace('stdin=None, timeout=300):','stdin=None, timeout=300, seed=None):')
runtime=runtime.replace('command(work,argv),stdin=', 'command(work,argv,seed=seed),stdin=')
grader=(src/'verifier/grader.py').read_text().replace("run(work,args,timeout=c['wall_seconds'])", "run(work,args,timeout=c['wall_seconds'],seed=seed)")
grader=grader.replace("    return result(sum(values)/len(values),checks,", "    valid=all(x['pass'] for x in checks)\n    aggregate=sum(values)/len(values)\n    return result(aggregate if valid else 0,checks,")
grader=grader.replace("'match_scores':values},valid=all(x['pass'] for x in checks))", "'match_scores':values,'original_mean_before_validity_gate':aggregate},valid=valid)")
for folder in ['verifier','environment/verifier/verifier']:
 (dst/folder/'runtime.py').write_text(runtime);(dst/folder/'grader.py').write_text(grader)
for side in ['agent','verifier']:
 ctx=dst/'environment'/side;shutil.copyfile(HERE/'patch_game_entropy.py',ctx/'patch_game_entropy.py')
 p=ctx/'Dockerfile';text=p.read_text().replace('RUN cmake -S /opt/runtime/wesnoth-source', 'COPY patch_game_entropy.py /opt/patch_game_entropy.py\nRUN python3 /opt/patch_game_entropy.py\nRUN cmake -S /opt/runtime/wesnoth-source');p.write_text(text)
note='\nr3 将真实对局、Lua 与默认 AI 所用熵源一起固定到评分器指定的 seed。补丁随 Docker 源码交付，禁止策略设置或访问 RNG。策略/执行无效的整个提交给 0 分；逐局原始分仍在 raw_metrics 中保留。合法提交的原公式、权重、地图、阵营、座位和种子集合均保持不变。\n'
for p in [dst/'instruction.md',dst/'public/instruction.md',dst/'environment/agent/public/instruction.md',dst/'environment/verifier/public/instruction.md']:p.write_text(p.read_text()+note)
(dst/'REVISION.json').write_text(json.dumps({'previous_revision':'game-task-r2',
 'change':['honor all engine entropy sources with trusted per-game seed','invalid submission zero gate retains raw match mean'],
 'source_commit':'8ba2b3ebd33f6850c2dc4fe7c6478c7e4f9fc3fd',
 'score_constants_unchanged':True,'six_hour_difficulty':'not_measured'},indent=2)+'\n')
print(dst)
