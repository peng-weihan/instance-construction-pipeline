from pathlib import Path
import subprocess,json,hashlib,os
root=Path(__file__).resolve().parents[1];src=root/'material-src/openapi-python-client';ref=root/'task/solution/reference'
revision=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
files=subprocess.check_output(['git','-C',str(src),'ls-files','-z']).split(b'\0')
manifest={'repository':'https://github.com/openapi-generators/openapi-python-client.git','revision':revision,'license':'MIT','license_sha256':hashlib.sha256((src/'LICENSE').read_bytes()).hexdigest(),'acquisition':'full git clone followed by detached checkout; complete tracked tree, not selected files','files':[]}
for b in files:
 if not b:continue
 name=b.decode();p=src/name;manifest['files'].append({'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest['tracked_files']=len(manifest['files'])
(root/'material-src/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# This index is private to this author branch; baseline HEAD and its index remain unchanged.
env=dict(os.environ,GIT_INDEX_FILE=str(root/'.tmp/reference.index'))
base=['git','--git-dir',str(src/'.git'),'--work-tree',str(ref),'-c','user.name=EdgeBench Task Author','-c','user.email=author@example.invalid']
def git(*args,input=None):return subprocess.check_output(base+list(args),env=env,input=input,text=True).strip()
git('read-tree',revision)
changed=json.loads((root/'evidence/reference-changed-files.json').read_text())
git('add','--',*changed)
tree=git('write-tree');commit=git('commit-tree',tree,'-p',revision,input='Implement streaming SDK response contexts and request-local auth\n')
git('update-ref','refs/heads/author/streaming-reference',commit)
patch=git('diff','--binary',revision,commit)+'\n'
(root/'task/solution/reference.patch').write_text(patch);(root/'task/verifier/private/reference.patch').write_text(patch)
(root/'evidence/reference-branch.json').write_text(json.dumps({'base_revision':revision,'reference_commit':commit,'tree':tree,'branch':'author/streaming-reference','changed_files':changed,'baseline_HEAD_unchanged':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()==revision},indent=2)+'\n')
private=root/'task/verifier/private'
(private/'integrity.json').write_text(json.dumps({str(p.relative_to(private)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(private.rglob('*')) if p.is_file() and p.name!='integrity.json'},indent=2)+'\n')
print('complete tracked tree:',manifest['tracked_files'],'reference branch:',commit)
