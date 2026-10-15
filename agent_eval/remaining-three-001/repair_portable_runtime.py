"""Use one matching interpreter, loader, stdlib and library closure offline."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tarfile
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
for kind in ['finance','game']:
 out=ROOT/(kind+'-pilot');assets=out/'public-runtime';context=out/'task/environment'
 image=json.loads((out/'preparation.json').read_text())['base_image_id'];cid=subprocess.check_output(['docker','create',image],text=True).strip()
 pyroot=assets/'opt/runtime/edge-python';(pyroot/'bin').mkdir(parents=True);(pyroot/'lib').mkdir()
 libs=assets/'opt/runtime/edge-system-libs';libs.mkdir()
 def cp(remote,dest,follow=False):subprocess.run(['docker','cp']+(['-L'] if follow else [])+[cid+':'+remote,str(dest)],check=True)
 try:
  cp('/usr/bin/python3.12',pyroot/'bin/python3.12',True);cp('/usr/lib/python3.12',pyroot/'lib/python3.12')
  # ldd reports the complete transitive closure; additionally include optional
  # Python extension dependencies needed by compression, sqlite, SSL and ctypes.
  command="ldd /opt/runtime/wesnoth/bin/wesnoth; ldd /usr/bin/python3.12; for f in /usr/lib/python3.12/lib-dynload/*.so; do ldd \"$f\"; done"
  ldd=subprocess.check_output(['docker','run','--rm','--network','none','--read-only','--entrypoint','sh',image,'-c',command],text=True,stderr=subprocess.DEVNULL)
  for path in sorted(set(re.findall(r'=> (/[^\s]+)',ldd))):cp(path,libs/Path(path).name,True)
  cp('/lib64/ld-linux-x86-64.so.2',libs/'ld-linux-x86-64.so.2',True)
 finally:subprocess.run(['docker','rm',cid],stdout=subprocess.DEVNULL,check=True)
 wrapper='''#!/bin/sh
export PYTHONHOME=/opt/runtime/edge-python
export PYTHONPATH=/opt/runtime/venv/lib/python3.12/site-packages
exec /opt/runtime/edge-system-libs/ld-linux-x86-64.so.2 --library-path /opt/runtime/edge-system-libs /opt/runtime/edge-python/bin/python3.12 "$@"
'''
 for name in ['python','python3','python3.12']:
  p=assets/'opt/runtime/venv/bin'/name
  if p.exists() or p.is_symlink():p.unlink()
  p.write_text(wrapper);p.chmod(0o755)
 if kind=='game':
  engine=assets/'opt/runtime/wesnoth/bin/wesnoth';engine.rename(engine.with_name('wesnoth.real'))
  engine.write_text('#!/bin/sh\nexec /opt/runtime/edge-system-libs/ld-linux-x86-64.so.2 --library-path /opt/runtime/edge-system-libs /opt/runtime/wesnoth/bin/wesnoth.real "$@"\n');engine.chmod(0o755)
  p=context/'bootstrap.sh';p.write_text(p.read_text().replace('LD_LIBRARY_PATH=/opt/runtime/edge-game-libs ',''))
  p=context/'public/play_public.py';p.write_text(p.read_text().replace("'LD_LIBRARY_PATH':'/opt/runtime/edge-game-libs',",''))
 archive=context/'runtime.tar.gz';old=out/'runtime-before-portable-fix.tar.gz';archive.rename(old)
 with tarfile.open(archive,'w:gz',compresslevel=1) as tar:tar.add(assets/'opt',arcname='opt')
 # The immutable original interpreter is left at /usr/bin/python3 for the SDK.
 # Only the explicit task runtime command is redirected to the copied CPython.
 p=out/'preparation.json';d=json.loads(p.read_text());d.update(runtime_archive_sha256=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),runtime_archive_bytes=archive.stat().st_size,
  portable_interpreter=True,portable_python_version='3.12',portable_loader_closure=True);p.write_text(json.dumps(d,indent=2)+'\n')
 print('portable runtime ready',kind,archive.stat().st_size,flush=True)
