"""Require explicit target completion in addition to kernel axiom closure."""
from pathlib import Path
import shutil,json
R=Path('/ws/users/raymone/edgebench/next-two-001');src=R/'lean-task-r2';dst=R/'lean-task-r3';shutil.copytree(src,dst)
for p in dst.rglob('grader.py'):
 s=p.read_text().replace('SubmissionError,workdir','SubmissionError,InfrastructureError,workdir')
 s=s.replace('checks=[]\n','checks=[];unfinished=set()\n')
 s=s.replace('for m in PAT.finditer(changed):','for m in PAT.finditer(changed):\n                if re.search(r"\\b(sorry|admit)\\b",m[3]):unfinished.add(m[2])')
 s=s.replace("if rc:return result(0", "if rc<0 or rc>=128:raise InfrastructureError('Lean compiler terminated abnormally: '+str(rc))\n        if rc:return result(0")
 s=s.replace("checks=[check('lean_build',True)]", "if rc:raise InfrastructureError('Lean declaration checker failed: '+str(rc)+' '+err[-300:])\n        checks=[check('lean_build',True)]")
 s=s.replace("ok=bool((match or no_axioms)", "ok=bool(t['name'] not in unfinished and (match or no_axioms)")
 p.write_text(s)
for p in dst.rglob('instruction.md'):
 p.write_text(p.read_text()+'\n目标得分同时要求：标记内无 sorry/admit 占位符，且内核声明依赖仅含允许公理。未完成目标可以保留 sorry，但该目标不计分。\n')
(R/'lean-scoring-repair.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'reason':'starter with explicit sorry received 0.04 under axiom-only completion check','score_formula_unchanged':True,'new_check':'per-target absence of sorry/admit plus existing kernel dependency closure','abnormal_compiler_exit':'infrastructure error, never a valid zero'},indent=2)+'\n')
