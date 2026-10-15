import json,subprocess
from pathlib import Path
R=Path('/ws/users/raymone/edgebench/next-two-001')
e=json.loads((R/'lean-controls-003/reference/execution.json').read_text())
a=e['command'];a[a.index('--name')+1]='edge-raymone-lean-target-probe';image=a.pop()
code="from pathlib import Path\nfrom runtime import run,workdir\nwith workdir() as w:\n p=Path(w)/'Probe.lean'\n p.write_text('import BrownianMotion.Gaussian.BrownianMotion\\n#print ProbabilityTheory.HasIndepIncrements.isGaussianProcess\\n#print axioms ProbabilityTheory.HasIndepIncrements.isGaussianProcess\\n#print IsGaussianProcess\\n')\n rc,out,err=run(w,['sh','-c','cd /opt/runtime/lean-project && lake env lean /work/Probe.lean']);print(rc);print(out);print(err)\n"
a+=['--entrypoint','/opt/runtime/venv/bin/python',image,'-c',code]
p=subprocess.run(a,capture_output=True,text=True,timeout=120)
(R/'lean-target-probe.json').write_text(json.dumps({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
print(p.stdout,p.stderr)
