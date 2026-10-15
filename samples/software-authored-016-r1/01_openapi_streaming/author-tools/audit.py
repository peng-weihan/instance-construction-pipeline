from pathlib import Path
import json,subprocess,shutil,hashlib
r=Path(__file__).resolve().parents[1];py=r/'.venv/bin/python';out=r/'evidence/audit';out.mkdir(exist_ok=True)
controls=r/'controls';bad=controls/'syntax_error';bad.mkdir(exist_ok=True);(bad/'openapi_python_client').mkdir(exist_ok=True);(bad/'openapi_python_client/__init__.py').write_text('def broken(:\n')
records=[]
for name,source,extra in [('syntax_error',bad,[]),('missing',controls/'absent',[]),('infrastructure',controls/'absent',['--inject-infrastructure-failure'])]:
 target=out/name
 cmd=[str(py),str(r/'task/tests/grader.py'),'--submission',str(source),'--private',str(r/'task/verifier/private'),'--output',str(target),'--scratch',str(r/'.tmp/grade'),'--python',str(py),*extra]
 p=subprocess.run(cmd,capture_output=True,text=True)
 d=json.loads((target/'score.json').read_text());native=(target/'reward.txt').read_text().strip() if (target/'reward.txt').exists() else None
 records.append({'name':name,'command':cmd,'exit_code':p.returncode,'valid':d['valid'],'score':d.get('score'),'native_reward':native})
 assert (d['valid'] and d['score']==0 and native=='0' and p.returncode==0) if name!='infrastructure' else (not d['valid'] and d['score'] is None and native is None and p.returncode!=0)
(out/'failure-classification.json').write_text(json.dumps(records,indent=2)+'\n')
# Test clean inverse patch applies to the public source tree and reproduces actual reference bytes.
target=r/'.tmp/patch-replay'
if target.exists():shutil.rmtree(target)
shutil.copytree(r/'task/environment/submission',target)
p=subprocess.run(['patch','-p1','-i',str(r/'task/solution/reference.patch')],cwd=target,capture_output=True,text=True)
assert p.returncode==0,p.stdout+p.stderr
changed=json.loads((r/'evidence/reference-changed-files.json').read_text())
assert all((target/f).read_bytes()==(r/'task/solution/reference'/f).read_bytes() for f in changed)
(out/'patch-replay.json').write_text(json.dumps({'exit_code':p.returncode,'changed_files':changed,'matches_reference':True,'stdout':p.stdout},indent=2)+'\n')
print('classification and inverse patch verified')
