from pathlib import Path
import json,tarfile
workspace=Path.cwd();r=workspace/'runs/software-authoring-016-20261015-r1'
root=workspace/'research/software-candidates-016-20261015'
with tarfile.open(r/'inputs.tar.gz','w:gz') as t:
 for rel in ['cards','sources','plan.json','candidates.json','REPORT.md','source-manifests.json','authoring_queue.json']:
  t.add(root/rel,arcname='inputs/'+rel)
 for p in (workspace/'samples/software-multiline-001/guidance').iterdir():
  if p.is_file():t.add(p,arcname='guidance/'+p.name)
 for name in ['factory-methods.md','original-software-tasks.md']:
  t.add(workspace/'research/software-engineering-2026-10-15'/name,arcname='guidance/'+name)
print(json.dumps({'bundle':str(r/'inputs.tar.gz'),'bytes':(r/'inputs.tar.gz').stat().st_size}))
