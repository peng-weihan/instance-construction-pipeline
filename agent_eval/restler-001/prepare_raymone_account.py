"""Prepare a new isolated runtime for the explicitly authorized raymone/1."""
import hashlib, json, shutil, subprocess
from pathlib import Path

R=Path('/ws/users/raymone/edgebench/restler-agent-001')
F=R/'framework-r3'
SOURCE=Path('/ws/users/wcgu/codex-static-egress/package-0.160.0-nine-accounts')
SHA='2a4ec9fb603d1f9deb487644f394d486024d323d14920a6c908c96332b3fca37'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(SOURCE/'bin/codex')==SHA
assert json.loads(Path('/ws/users/wcgu/codex-static-egress/nine-accounts-build/installation.json').read_text())['passed']
assert not F.exists()
subprocess.run(['cp','-a','--reflink=auto',str(R/'framework-r2'),str(F)],check=True)
shutil.rmtree(F/'codex-static-package')
shutil.copytree(SOURCE,F/'codex-static-package')
package=F/'codex-static-package'
hashes={p.relative_to(package).as_posix():digest(p) for p in package.rglob('*') if p.is_file()}
assert not any(p.is_symlink() or p.name in ('auth.json','static-egress.json','config.toml') for p in package.rglob('*'))
manifest=json.loads((F/'toolchain-manifest.json').read_text())
entry=manifest['codex']
entry.update(codex_binary=str(package/'bin/codex'),codex_sha256=SHA,codex_code_mode_host=str(package/'bin/codex-code-mode-host'),codex_code_mode_host_sha256=hashes['bin/codex-code-mode-host'],codex_package_root=str(package),codex_package_hashes=hashes)
(F/'toolchain-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
p=F/'edgebench_harbor/static_native.py';s=p.read_text()
s=s.replace('1a61b2dfe1d83b6bc38ec3a67aa97542011525c9cb8d6dd81492adf664aa7ee9',SHA)
s=s.replace('/ws/users/wcgu/new-codex-group/20x/7','/ws/users/wcgu/new-codex-group/raymone/1')
s=s.replace('155.229.74.142','206.135.156.134').replace('7401','7056')
s=s.replace("'account': 'receiver' if receiver else 7","'account': 'receiver' if receiver else 'raymone/1'")
s=s.replace("'account':7","'account':'raymone/1'").replace('account7','raymone/1').replace('Account7','Raymone1').replace('20x/7 only','raymone/1 only')
p.write_text(s)
provenance=Path('/ws/users/wcgu/codex-static-egress/nine-accounts-build')
(F/'raymone-package-provenance.json').write_text(json.dumps({'source_provenance':json.loads((provenance/'provenance.json').read_text()),'patch_sha256':digest(provenance/'nine-accounts.patch'),'installation_passed':True,'cli_sha256':SHA,'package_files':len(hashes)},indent=2)+'\n')
inventory={p.relative_to(F).as_posix():digest(p) for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
tree=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()
(F/'framework-version.json').write_text(json.dumps({'status':'frozen','kind':'raymone_cloud_pilot','formal_acceptance':False,'runtime_tree_sha256':tree,'runtime_file_hashes':inventory},indent=2)+'\n')
T=R/'task-r3';shutil.copytree(R/'task-r2',T)
p=T/'verifier/verifier/runtime.py';s=p.read_text().replace('        os.setgroups([]); os.setgid(2000); os.setuid(2000)\n','')
s=s.replace("'--share-net','--die-with-parent'","'--share-net','--uid','2000','--gid','2000','--die-with-parent'")
p.write_text(s)
print(json.dumps({'framework':str(F),'runtime_tree_sha256':tree,'cli_sha256':SHA,'package_files':len(hashes),'task':str(T)}))
