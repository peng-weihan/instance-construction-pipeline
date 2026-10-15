#!/usr/bin/env python3
"""Pinned source/native dependency preparation. Does not claim service closure."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,urllib.request
r=Path(__file__).resolve().parents[1];m=json.loads((r/'authoring/build-manifest.json').read_text())
def verify(p,digest):
 if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise RuntimeError('hash mismatch '+str(p))
for name,digest in m['sources'].items():
 p=r/'authoring/sources'/name
 if not p.exists():urllib.request.urlretrieve(m['source_urls'][name],p)
 verify(p,digest)
 shutil.copyfile(p,r/'environment'/('starter.tar.gz' if name=='restler.tar.gz' else name))
if not all((r/'environment/wheels'/n).exists() for n in m['wheels']):
 subprocess.run([sys.executable,'-m','pip','download','--require-hashes','--only-binary=:all:','--platform','manylinux2014_x86_64','--python-version','312','--implementation','cp','--abi','cp312','-r',str(r/'environment/requirements.lock'),'-d',str(r/'environment/wheels')],check=True)
for name,digest in m['wheels'].items():
 verify(r/'environment/wheels'/name,digest);shutil.copyfile(r/'environment/wheels'/name,r/'verifier/wheels'/name)
for name in ['grader.py','cases.json','test.sh']:shutil.copyfile(r/'tests'/name,r/'verifier'/name)
verify(r/'tests/grader.py',m['grader_sha256'])
verify(r/'solution/reference-draft.tar.gz',m['reference_draft_sha256'])
print('Sources/native wheels verified. HOLD: JDK21, Gradle/Maven cache, Polaris service/reset and formal oracle are not prepared.')
