from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parents[1];py=r/'.venv-offline/bin/python';author=r/'.venv/bin/python'
base=r/'evidence/frozen';base.mkdir(exist_ok=True)
results=[]
checks=[(f'reference-{i}','task/solution/reference') for i in range(1,6)]+[('nop','task/environment/submission'),('cheap','controls/cheap'),('no_auth_override','controls/no_auth_override'),('eager','controls/eager')]
for name,source in checks:
 output=base/name
 cmd=[str(author),str(r/'task/tests/grader.py'),'--submission',str(r/source),'--private',str(r/'task/verifier/private'),'--output',str(output),'--scratch',str(r/'.tmp/grade'),'--python',str(py)]
 process=subprocess.run(cmd,stdout=(base/(name+'.stdout')).open('w'),stderr=subprocess.STDOUT)
 d=json.loads((output/'score.json').read_text())
 digest=hashlib.sha256((r/'task/tests/grader.py').read_bytes()).hexdigest()
 record={'name':name,'command':cmd,'exit_code':process.returncode,'valid':d['valid'],'score':d.get('score'),'passed':d.get('metrics',{}).get('passed'),'total':d.get('metrics',{}).get('total'),'grader_sha256':digest,'score_spec_sha256':d.get('spec_sha256'),'evidence':str(output.relative_to(r))}
 results.append(record);(base/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(name,d.get('score'),flush=True)
