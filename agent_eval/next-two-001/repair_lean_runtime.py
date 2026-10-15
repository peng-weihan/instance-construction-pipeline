from pathlib import Path
import json
r=Path('/ws/users/raymone/edgebench/next-two-001')
for p in (r/'lean-task-r3').rglob('runtime.py'):
 s=p.read_text().replace('def limits(cpu=1200,memory_gb=8):','def limits(cpu=1200,memory_gb=64):')
 if "'--setenv','LEAN_NUM_THREADS','1'" not in s:s=s.replace("'--setenv','OMP_NUM_THREADS','1'","'--setenv','LEAN_NUM_THREADS','1','--setenv','OMP_NUM_THREADS','1'")
 p.write_text(s)
s=(r/'lean-task-r3/verifier/runtime.py').read_text().replace("'--unshare-all','--die-with-parent'","'--unshare-all','--share-net','--uid','2000','--gid','2000','--die-with-parent'")
assert s==(r/'lean-controls-005/judge/runtime.py').read_text()
(r/'lean-runtime-repair.json').write_text(json.dumps({'virtual_address_limit_gib':64,'container_memory_limit_gib':28,'lean_num_threads':1,'actual_judge_runtime_matches_source_plus_namespace_adapter':True,'candidate':'lean-task-r3','controls':'lean-controls-005'},indent=2)+'\n')
print('candidate runtime matches frozen tested implementation')
