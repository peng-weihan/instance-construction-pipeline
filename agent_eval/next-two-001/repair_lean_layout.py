"""Repair misplaced proof-body newlines in a separate candidate version."""
from pathlib import Path
import shutil,re,json
R=Path('/ws/users/raymone/edgebench/next-two-001');src=R/'source-complete/brownian_multibranch_proofs';dst=R/'lean-task-r2'
shutil.copytree(src,dst)
pattern=re.compile(r'(/- BEGIN TASK PROOF ([^\n]+) -/)(.*?)(/- END TASK PROOF \2 -/)',re.S)
changes=[]
for p in dst.rglob('*.lean'):
 s=p.read_text()
 def fix(m):
  body=m[3]
  if body.startswith('\nby\n'):body=' by\n'+body[len('\nby\n'):]
  if m[2] in ('HasIndepIncrements.isGaussianProcess','IsBrownianReal.inv') and body.strip()=='by\n  sorry':body=' by\n    sorry\n'
  return m[1]+body+m[4]
 t=pattern.sub(fix,s)
 if t!=s:p.write_text(t);changes.append(str(p.relative_to(dst)))
for p in (dst/'environment').rglob('Dockerfile'):
 s=p.read_text().replace('RUN lake exe cache get && lake build','RUN lake exe cache get\nRUN lake build');p.write_text(s)
(R/'lean-layout-repair.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'changed_files':changes,'reason':'proof marker inserted a newline before by inside structure fields; preserve signatures and original proof bodies'},indent=2)+'\n')
print('repaired',len(changes),'files')
