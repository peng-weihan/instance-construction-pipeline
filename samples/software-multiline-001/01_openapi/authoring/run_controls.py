from pathlib import Path
import json, subprocess, sys
r=Path(__file__).resolve().parents[1]
controls={'reference':r/'solution/reference','starter':r/'authoring/sources/openapi-python-client-0a283fe21eeaa23046faf622d4ff4b2c826d2edb','near-miss-lost-required':r/'authoring/near-misses/lost-required','near-miss-untyped-arrays':r/'authoring/near-misses/untyped-arrays','empty':r/'authoring/empty'}
controls['empty'].mkdir(exist_ok=True)
summary={}
for name,path in controls.items():
 output=r/'authoring/evidence'/name
 cmd=[sys.executable,str(r/'tests/grader.py'),'--candidate',str(path),'--output',str(output)]
 result=subprocess.run(cmd,capture_output=True,text=True)
 (output/'control.json').write_text(json.dumps({'command':cmd,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2))
 summary[name]=json.loads((output/'score.json').read_text())['score']
print(json.dumps(summary,indent=2))
(r/'authoring/evidence/control-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
