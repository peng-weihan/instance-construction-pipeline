"""Preserve the measured baseline so source rebuilds use identical score anchors."""
from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path('/ws/users/raymone/edgebench/next-two-001');task=R/'packing-task-r4';out=R/'packing-frozen-reference';out.mkdir()
image=subprocess.check_output(['docker','image','inspect','edge-raymone-packing:initial','--format','{{.Id}}'],text=True).strip()
cid=subprocess.check_output(['docker','create',image],text=True).strip()
try:
 for name in ['reference_lengths.json','reference_lock.json','reference_certificates']:
  subprocess.run(['docker','cp',cid+':/judge/private/'+name,str(out/name)],check=True)
finally:subprocess.run(['docker','rm',cid],check=True,stdout=subprocess.DEVNULL)
refs=json.loads((out/'reference_lengths.json').read_text());assert len(refs)==27
for parent in [task/'private',task/'environment/verifier/private']:
 for p in out.iterdir():
  if p.is_dir():shutil.copytree(p,parent/p.name,dirs_exist_ok=True)
  else:shutil.copyfile(p,parent/p.name)
code='''import json,hashlib
from pathlib import Path
from geometry import validate
from runtime import scoring_constants
r=Path('/judge');refs=json.loads((r/'private/reference_lengths.json').read_text());rows=json.loads((r/'private/workloads.json').read_text());assert len(refs)==len(rows)==27
for row in rows:
 folder=r/('public/cases' if row['split']=='public' else 'private/'+row['split']+'_cases')
 case=folder/(row['id']+'.json');cert=r/'private/reference_certificates'/(row['id']+'.json');ref=refs[row['id']]
 assert hashlib.sha256(case.read_bytes()).hexdigest()==ref['input_sha256']
 assert hashlib.sha256(cert.read_bytes()).hexdigest()==ref['certificate_sha256']
 actual=validate(json.loads(case.read_text()),json.loads(cert.read_text()),scoring_constants())
 assert all(actual[k]==ref[k] for k in actual)
print('27 frozen source-bound reference layouts verified')
'''
for parent in [task/'verifier',task/'environment/verifier/verifier']:(parent/'verify_frozen_reference.py').write_text(code)
p=task/'environment/verifier/Dockerfile';s=p.read_text();assert 'RUN python prepare_reference.py' in s;s=s.replace('RUN python prepare_reference.py','RUN python verify_frozen_reference.py');p.write_text(s)
report={'image_id':image,'cases':len(refs),'baseline_is_measured_and_frozen':True,'source_rebuild_verifies_instead_of_regenerating_baseline':True,'files':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='files'}))
