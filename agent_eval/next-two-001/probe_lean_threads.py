import json,subprocess
from pathlib import Path
R=Path('/ws/users/raymone/edgebench/next-two-001')
e=json.loads((R/'lean-controls-001/reference/execution.json').read_text())
a=e['command'];a[a.index('--name')+1]='edge-raymone-lean-thread-probe';image=a.pop()
code="""import json
from runtime import run,workdir
rows=[]
for command in ['lake --version','LEAN_NUM_THREADS=1 lake --version']:
 with workdir() as w:
  rc,out,err=run(w,['sh','-c',command]);rows.append({'command':command,'rc':rc,'out':out,'err':err})
print(json.dumps(rows))
"""
a+=['--entrypoint','/opt/runtime/venv/bin/python',image,'-c',code]
p=subprocess.run(a,capture_output=True,text=True,timeout=120)
(R/'lean-thread-probe.json').write_text(json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
print(p.stdout,p.stderr)
