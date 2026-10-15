from pathlib import Path
import json,subprocess,shutil,hashlib,os
r=Path(__file__).resolve().parents[1];private=r/'task/verifier/private';author=r/'.venv/bin/python';runtime=r/'.venv-offline/bin/python'
case=r/'controls/corrupt-private'
if case.exists():shutil.rmtree(case)
shutil.copytree(private,case);(case/'stream-contract.json').write_text((case/'stream-contract.json').read_text()+'\n')
out=r/'evidence/audit/corrupt-private';out.mkdir(exist_ok=True);(out/'reward.txt').write_text('0.8\n');(out/'reward.json').write_text('{"reward":0.8}\n')
cmd=[str(author),str(r/'task/tests/grader.py'),'--submission',str(r/'task/solution/reference'),'--private',str(case),'--output',str(out),'--scratch',str(r/'.tmp/grade'),'--python',str(runtime)]
p=subprocess.run(cmd,capture_output=True,text=True);data=json.loads((out/'score.json').read_text())
assert p.returncode!=0 and data['valid'] is False and data['score'] is None and not (out/'reward.txt').exists() and not (out/'reward.json').exists()
(r/'evidence/audit/corrupt-private-result.json').write_text(json.dumps({'command':cmd,'exit_code':p.returncode,'valid':data['valid'],'score':data['score'],'error':data['error'],'stale_reward_files_removed':True},indent=2)+'\n')
# Author-made caches are not task materials or part of the source reference.
for base in ['task/environment','task/solution','task/verifier/tests']:
 for pattern in ['__pycache__','.ruff_cache','.pytest_cache','.mypy_cache']:
  for path in (r/base).rglob(pattern):
   if path.is_dir():shutil.rmtree(path)
fsck=subprocess.run(['git','-C',str(r/'material-src/openapi-python-client'),'fsck','--no-reflogs'],capture_output=True,text=True)
assert fsck.returncode==0
(r/'evidence/source-fsck-result.json').write_text(json.dumps({'command':['git','-C','material-src/openapi-python-client','fsck','--no-reflogs'],'exit_code':fsck.returncode,'output':fsck.stdout+fsck.stderr},indent=2)+'\n')
source_manifest=json.loads(Path('/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1/inputs/sources/01_openapi_streaming/manifest.json').read_text())
matches=[{'path':item['path'],'matches':hashlib.sha256((r/'material-src/openapi-python-client'/item['path']).read_bytes()).hexdigest()==item['sha256']} for item in source_manifest['files_acquired']]
assert all(m['matches'] for m in matches)
(r/'evidence/source-card-hash-matches.json').write_text(json.dumps(matches,indent=2)+'\n')
# Hash equivalence for the root /tests entry and image /tests entry.
for p in (r/'task/tests').iterdir():
 if p.is_file():assert p.read_bytes()==(r/'task/verifier/tests'/p.name).read_bytes()
for context in ['environment','verifier']:
 for p in (r/'task'/context).rglob('*'):assert not p.is_symlink(),str(p)
print('corrupt-private invalid/no reward, source fsck, selected-source hashes, tests copy equality: passed')
