"""Remove only our derived Lean export after verified archive and dependency checks."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tarfile
ROOT=Path('/ws/users/raymone/edgebench/next-two-001')
CACHE=ROOT/'lean-pilot/public-runtime'
receipt=Path('/ws/users/storage-archive/logs/20261014T191748Z-16893.json')
r=json.loads(receipt.read_text());assert r['status']=='verified' and r['source']==str(ROOT/'lean-runtime-immutable-archive')
manifest=json.loads((ROOT/'lean-runtime-immutable-archive/manifest.json').read_text())
archive=ROOT/'lean-runtime-immutable-archive/runtime.tar.gz'
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==manifest['sha256']
verified=0
with tarfile.open(archive,'r|gz') as tar:
    for member in tar:
        path=CACHE/member.name
        assert path.is_relative_to(CACHE) and '..' not in Path(member.name).parts
        if member.isfile():
            expected=hashlib.file_digest(tar.extractfile(member),'sha256').hexdigest()
            with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            assert actual==expected,str(path);verified+=1
        elif member.issym():assert path.is_symlink() and os.readlink(path)==member.linkname
        elif member.isdir():assert path.is_dir()
        else:raise ValueError('unsupported archive entry')
for task in ['lean-pilot/run-6h-002','packing-pilot/run-6h-001']:
    assert str(CACHE) not in (ROOT/task/'protocol.json').read_text()
ids=subprocess.check_output(['docker','ps','-q'],text=True).split()
for cid in ids:
    mounts=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .Mounts}}',cid],text=True))
    assert not any(m.get('Source','').startswith(str(CACHE)) for m in mounts)
shutil.rmtree(CACHE)
(ROOT/'lean-export-cache-retirement.json').write_text(json.dumps({'removed_derived_cache':str(CACHE),'archive_destination':r['destination'],'archive_status':'verified','archive_receipt':str(receipt),'verified_regular_files':verified,'compressed_archive_retained_locally':True,'active_run_contexts_and_images_untouched':True},indent=2)+'\n')
print('Verified and retired derived export cache:',verified,'files')
