import json
from pathlib import Path
root=Path('/opt/runtime/packing-build');mapping={}
for p in root.rglob('*-src'):
    if p.is_dir():mapping[p.name[:-4]]=str(p)
Path('/opt/runtime/packing-dependencies.json').write_text(json.dumps(mapping,indent=2)+'\n')
