"""Wait for our own verified upload, seal its explicit overlay, then launch gates."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,tarfile,time
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
archive=ROOT/'singlecell-source-r2.tar.gz';overlay=ROOT/'singlecell-grader-r2.py'
expected_archive='dda9b4bc6ebe08fdce38b8e76d358aeef264211ac5f7c6a56a89ed087cf75c74'
expected_overlay='3406528e88120764b8c0144b2d6e696edfc71bd7823cc09af6a15a89fd7eef53'
deadline=time.monotonic()+1800
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def status(stage):
 (ROOT/'science-bootstrap-status.json').write_text(json.dumps({'stage':stage,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n');print(stage,flush=True)
status('waiting_for_own_source_upload')
while True:
 if archive.exists() and archive.stat().st_size==121501276 and overlay.exists() and sha(overlay)==expected_overlay:break
 if time.monotonic()>deadline:raise TimeoutError('source upload incomplete')
 time.sleep(10)
assert sha(archive)==expected_archive
source=ROOT/'singlecell_cross_site_graph_lab-r2'
assert not source.exists()
with tarfile.open(archive) as t:t.extractall(ROOT,filter='data')
hashes=json.loads((source/'source-files.sha256.json').read_text())
for name,digest in hashes.items():assert sha(source/name)==digest,name
shutil.copyfile(overlay,source/'verifier/grader.py')
hashes['verifier/grader.py']=expected_overlay
(source/'source-files.sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
(source/'deployment-overlay.json').write_text(json.dumps({'source_archive_sha256':expected_archive,'overlay_grader_sha256':expected_overlay,'changes':['reject symlink predictions','accept unsigned integer predictions without numeric promotion'],'score_formula_changed':False},indent=2)+'\n')
status('waiting_for_offline_ml_dependency_image')
while subprocess.run(['docker','image','inspect','edge-raymone-science:ml-runtime-001'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 if time.monotonic()>deadline:raise TimeoutError('ML dependency image unavailable')
 time.sleep(10)
status('running_actual_preflight_and_authorized_rollout')
subprocess.run(['/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python',str(ROOT/'advance_science_pilot.py')],check=True)
