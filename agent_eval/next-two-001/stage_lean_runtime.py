"""Export only the public Lean dependency closure, before model admission."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
R=Path('/ws/users/raymone/edgebench/next-two-001');out=R/'lean-runtime-stage';out.mkdir();assets=out/'assets';assets.mkdir()
base=subprocess.check_output(['docker','image','inspect','edge-raymone-lean:initial','--format','{{.Id}}'],text=True).strip()
cid=subprocess.check_output(['docker','create',base],text=True).strip()
try:
 for remote,relative in [('/opt/runtime/elan/toolchains/leanprover--lean4---v4.33.0-rc1','opt/lean'),('/opt/runtime/lean-project','opt/runtime/lean-project')]:
  local=assets/relative;local.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['docker','cp',cid+':'+remote,str(local)],check=True)
finally:subprocess.run(['docker','rm',cid],check=True)
assert not (assets/'opt/runtime/lean-project/.git').exists()
assert not any(p.name in ('auth.json','static-egress.json') for p in assets.rglob('*'))
f=out/'runtime.tar.gz'
with tarfile.open(f,'w:gz',compresslevel=1) as tar:tar.add(assets/'opt',arcname='opt')
with f.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
(out/'report.json').write_text(json.dumps({'source_image_id':base,'bytes':f.stat().st_size,'sha256':sha,'public_paths':['/opt/runtime/lean-project','/opt/runtime/elan/toolchains/leanprover--lean4---v4.33.0-rc1']},indent=2)+'\n')
print((out/'report.json').read_text())
