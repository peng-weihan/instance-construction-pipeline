from pathlib import Path
import json,hashlib,subprocess,shutil,ast,math
r=Path(__file__).resolve().parents[1];task=r/'task';author=task/'authoring';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((author/'build-manifest.json').read_text());checks={}
for name,context in manifest['contexts'].items():
 root=task/name
 for item in context['files']:assert sha(root/item['path'])==item['sha256'],item['path']
 checks[name+'_manifest']=True
for name in ['test.sh','grader.py','worker.py']:assert (task/'tests'/name).read_bytes()==(task/'verifier/tests'/name).read_bytes()
checks['root_and_image_tests_identical']=True
for p in ['tests/grader.py','tests/worker.py','environment/public/smoke.py']:ast.parse((task/p).read_text())
for p in ['tests/test.sh','solution/solve.sh']:assert subprocess.run(['sh','-n',str(task/p)]).returncode==0
checks['syntax']=True
spec=json.loads((author/'score-spec.json').read_text());assert abs(sum(g['weight'] for g in spec['groups'].values())-1)<1e-12
results=json.loads((author/'frozen-replay-results.json').read_text());freeze=json.loads((author/'grading-freeze.json').read_text())
assert freeze['grader_sha256']==sha(task/'tests/grader.py') and freeze['score_spec_sha256']==sha(author/'score-spec.json') and freeze['worker_sha256']==sha(task/'tests/worker.py')
for row in results:
 data=json.loads((r/row['evidence']/'score.json').read_text());reward=float((r/row['evidence']/'reward.txt').read_text())
 assert data['valid'] and 0<=data['score']<=1 and math.isfinite(reward) and reward==data['score']
 expected=sum(g['weight']*sum(c['passed'] for c in data['checks'] if c['name'] in g['checks'])/len(g['checks']) for g in spec['groups'].values())
 assert expected==reward and row['grader_sha256']==freeze['grader_sha256'] and row['score_spec_sha256']==freeze['score_spec_sha256']
assert [x['score'] for x in results[:5]]==[1.0]*5
checks['score_formula_native_and_structured_agree']=True
patchroot=r/'.tmp/packaged-controls';patchroot.mkdir(exist_ok=True,mode=0o700);patches=[]
for name in ['cheap','no_auth_override','eager']:
 dest=patchroot/name
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(task/'environment/submission',dest)
 p=subprocess.run(['patch','-p1','-i',str(author/'controls'/f'{name}.patch')],cwd=dest,capture_output=True,text=True)
 assert p.returncode==0,p.stdout+p.stderr
 original=r/'controls'/name
 originalfiles={str(p.relative_to(original)):sha(p) for p in original.rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','.ruff_cache','.pytest_cache','.mypy_cache'])}
 actualfiles={str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()}
 assert actualfiles==originalfiles,name
 patches.append({'name':name,'patch_reconstructs_actual_control':True,'files':len(actualfiles)})
checks['preserved_controls_reconstruct_actual_inputs']=patches
# Do not hash the self-index. Reports and all context bytes are frozen in this package index.
files=[p for p in sorted(task.rglob('*')) if p.is_file() and p!=author/'package-files.json']
(author/'package-files.json').write_text(json.dumps({'self_excluded':'authoring/package-files.json','files':[{'path':str(p.relative_to(task)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]},indent=2)+'\n')
(r/'evidence/package-final-qc.json').write_text(json.dumps({'valid':True,'checks':checks,'file_count_without_self_index':len(files),'docker_built':False,'harbor_trial_run':False,'arm_run':False,'teacher_run':False},indent=2)+'\n')
print(json.dumps({'valid':True,'files':len(files),'score_checks':len(results),'controls_reconstructed':len(patches)}))
