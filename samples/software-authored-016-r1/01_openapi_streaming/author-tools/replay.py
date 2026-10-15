from pathlib import Path
import subprocess,json,shutil
r=Path(__file__).resolve().parents[1];py=r/'.venv/bin/python'
records=[]
for name,source in [('ref-final-2','task/solution/reference'),('ref-final-3','task/solution/reference'),('ref-final-4','task/solution/reference'),('ref-final-5','task/solution/reference'),('cheap-final','controls/cheap'),('nop-final','task/environment/submission'),('noauth-final','controls/no_auth_override'),('eager-final','controls/eager')]:
 out=r/'evidence'/name
 cmd=[str(py),str(r/'task/tests/grader.py'),'--submission',str(r/source),'--private',str(r/'task/verifier/private'),'--output',str(out),'--scratch',str(r/'.tmp/grade'),'--python',str(py)]
 p=subprocess.run(cmd,stdout=(r/'evidence'/(name+'.stdout')).open('w'),stderr=subprocess.STDOUT)
 d=json.loads((out/'score.json').read_text());records.append({'name':name,'command':cmd,'exit_code':p.returncode,'score':d.get('score'),'valid':d['valid']})
 (r/'evidence/replay-results.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,d.get('score'),flush=True)
