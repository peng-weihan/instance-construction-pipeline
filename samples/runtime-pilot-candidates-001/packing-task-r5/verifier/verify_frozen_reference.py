import json,hashlib
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
