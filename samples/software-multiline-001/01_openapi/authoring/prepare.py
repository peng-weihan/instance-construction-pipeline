#!/usr/bin/env python3
"""Verify/recreate offline build contexts without running Docker or a model."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, urllib.request
r=Path(__file__).resolve().parents[1]
m=json.loads((r/'authoring/build-manifest.json').read_text())
def verify(p, expected):
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual!=expected: raise RuntimeError(f'hash mismatch: {p}')
source=r/'environment/starter.tar.gz'
if not source.exists():
    urllib.request.urlretrieve('https://codeload.github.com/openapi-generators/openapi-python-client/tar.gz/0a283fe21eeaa23046faf622d4ff4b2c826d2edb',source)
verify(source,m['source_archive_sha256'])
if not all((r/'environment/wheels'/name).exists() for name in m['wheel_files']):
    subprocess.run([sys.executable,'-m','pip','download','--require-hashes','--only-binary=:all:','--platform','manylinux2014_x86_64','--platform','manylinux_2_28_x86_64','--python-version','312','--implementation','cp','--abi','cp312','-r',str(r/'environment/requirements.lock'),'-d',str(r/'environment/wheels')],check=True)
for name,digest in m['wheel_files'].items():
    verify(r/'environment/wheels'/name,digest)
    shutil.copyfile(r/'environment/wheels'/name,r/'verifier/wheels'/name)
for name in ('grader.py','cases.py','test.sh'):
    shutil.copyfile(r/'tests'/name,r/'verifier'/name)
verify(r/'tests/grader.py',m['grader_sha256'])
verify(r/'tests/cases.py',m['cases_sha256'])
verify(r/'solution/reference.tar.gz',m['reference_archive_sha256'])
print('verified source, reference, wheels, and authoritative judge copies; images not built')
