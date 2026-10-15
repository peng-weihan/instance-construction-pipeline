from pathlib import Path
import shutil,json
R=Path('/ws/users/raymone/edgebench/next-two-001');src=R/'packing-task-r4';dst=R/'packing-task-r5';shutil.copytree(src,dst)
for p in dst.rglob('runtime.py'):
 s=p.read_text().replace('def limits(cpu=1200,memory_gb=8):','def limits(cpu=1200,memory_gb=8,pin_cpu=True):').replace("if hasattr(os,'sched_getaffinity'):","if pin_cpu and hasattr(os,'sched_getaffinity'):")
 s=s.replace('def run(work, argv, *, stdin=None, timeout=300):','def run(work, argv, *, stdin=None, timeout=300,pin_cpu=True):')
 s=s.replace('stderr=err,preexec_fn=limits())','stderr=err,preexec_fn=limits(pin_cpu=pin_cpu))');p.write_text(s)
for p in dst.rglob('grader.py'):
 s=p.read_text().replace("run(work,['python','build.py'],timeout=900)","run(work,['python','build.py'],timeout=900,pin_cpu=False)");p.write_text(s)
(R/'packing-compile-repair.json').write_text(json.dumps({'source':str(src),'candidate':str(dst),'change':'compile with both declared Docker CPUs; preserve single-core affinity for each solver call','formula_and_solver_budgets_unchanged':True,'old_controls':'packing-controls-001','new_controls':'packing-controls-002'},indent=2)+'\n')
