from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2];src=ROOT/'samples/remaining-three-built-001/game-task-r1';dst=src.with_name('game-task-r2')
shutil.copytree(src,dst)
for folder in ['verifier','environment/verifier/verifier']:
 p=dst/folder/'grader.py';text=p.read_text();text=text.replace("'match_scores':values})", "'match_scores':values},valid=all(x['pass'] for x in checks))")
 p.write_text(text)
note='\nvalid 表示所有对局均完成合法策略执行；非法动作、Lua错误或弃权会使它为 false。原每局分数与平均公式保持不变，原始部分分数仍用于诊断；只有有效提交进入最好分曲线。\n'
for p in [dst/'instruction.md',dst/'public/instruction.md',dst/'environment/agent/public/instruction.md',dst/'environment/verifier/public/instruction.md']:p.write_text(p.read_text()+note)
(dst/'REVISION.json').write_text(json.dumps({'previous_revision':'game-task-r1','change':'execution failures now propagate valid=false',
 'formula_constants_unchanged':True,'six_hour_difficulty':'not_measured'},indent=2)+'\n')
print(dst)
