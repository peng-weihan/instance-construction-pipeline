"""Build-time reference material generation; run only when building the judge image.
Freezes independent geometry-validated reference lengths once, never per submission.
"""
import json,subprocess,tempfile,hashlib
from pathlib import Path
from geometry import validate
root=Path('/judge');rows=json.loads((root/'private/workloads.json').read_text());records={}
binary=Path('/opt/runtime/packing-build/install/bin/packingsolver_irregular')
if not binary.exists():
    candidates=[p for p in Path('/opt/runtime/packing-build').rglob('packingsolver_irregular') if p.is_file() and p.stat().st_mode&0o111]
    if len(candidates)!=1:raise RuntimeError('reference executable cannot be located uniquely')
    binary=candidates[0]
for row in rows:
    folder=root/('public/cases' if row['split']=='public' else 'private/'+row['split']+'_cases');case=folder/(row['id']+'.json')
    with tempfile.TemporaryDirectory() as t:
        cert=Path(t)/'certificate.json'
        subprocess.run([str(binary),'--input',str(case),'--certificate',str(cert),'--time-limit','20','--verbosity-level','0'],check=True,timeout=30)
        geometry=validate(json.loads(case.read_text()),json.loads(cert.read_text()))
        records[row['id']]={**geometry,'input_sha256':hashlib.sha256(case.read_bytes()).hexdigest(),
                            'certificate_sha256':hashlib.sha256(cert.read_bytes()).hexdigest()}
        target=root/'private/reference_certificates'/cert.name.replace('certificate',row['id']);target.parent.mkdir(exist_ok=True);target.write_bytes(cert.read_bytes())
(root/'private/reference_lengths.json').write_text(json.dumps(records,indent=2)+'\n')
