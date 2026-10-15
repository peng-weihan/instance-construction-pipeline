"""Use the solver's supported clearance option; keep strict geometry checks."""
from pathlib import Path
import json,shutil,subprocess
R=Path('/ws/users/raymone/edgebench/next-two-001');src=R/'source-complete/industrial_nesting_improvement';dst=R/'packing-task-r3';shutil.copytree(src,dst)
for p in dst.rglob('scoring_metadata.json'):
 d=json.loads(p.read_text());d['constants']['solver_clearance']=0.001;p.write_text(json.dumps(d,indent=2)+'\n')
for p in dst.rglob('grader.py'):
 s=p.read_text().replace("'--verbosity-level','0'","'--verbosity-level','0','--item-item-minimum-spacing',str(c['solver_clearance'])");p.write_text(s)
for p in dst.rglob('prepare_reference.py'):
 s=p.read_text().replace("'--verbosity-level','0'","'--verbosity-level','0','--item-item-minimum-spacing',str(constants['solver_clearance'])");p.write_text(s)
for p in dst.rglob('instruction.md'):
 p.write_text(p.read_text()+'\n求解器调用统一附带 --item-item-minimum-spacing 0.001，为接触布局留出数值安全裕量；参考布局和提交使用相同参数。独立几何检查的重叠容差及评分公式保持不变。\n')
context=R/'packing-reference-r3';context.mkdir()
for name in ['prepare_reference.py','grader.py']:shutil.copyfile(dst/'verifier'/name,context/name)
shutil.copyfile(dst/'public/scoring_metadata.json',context/'scoring_metadata.json')
base=subprocess.check_output(['docker','image','inspect','edge-raymone-packing:runtime','--format','{{.Id}}'],text=True).strip()
(context/'Dockerfile').write_text('FROM edge-raymone-packing:runtime'+'\nCOPY prepare_reference.py grader.py /judge/verifier/\nCOPY scoring_metadata.json /judge/public/scoring_metadata.json\nRUN python /judge/verifier/prepare_reference.py\n')
(R/'packing-clearance-repair-r3.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'clearance':0.001,'geometry_tolerance_unchanged':True,'formula_unchanged':True,'evidence':'packing-geometry-probe/report.json and packing-clearance-probe/report.json'},indent=2)+'\n')
