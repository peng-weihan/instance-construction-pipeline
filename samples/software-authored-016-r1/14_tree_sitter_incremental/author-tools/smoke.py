from pathlib import Path
import shutil,subprocess,json
R=Path(__file__).resolve().parents[1];T=R/'task';D=R/'evidence/public-smoke';D.mkdir(exist_ok=True)
for src,dst in [('starter','submission'),('grammar','grammar'),('public','public')]:shutil.copytree(T/'environment'/src,D/dst,dirs_exist_ok=True)
p=subprocess.run(['/bin/sh',str(D/'public/smoke.sh')],env={'PATH':'/usr/bin:/bin','PROJECT_ROOT':str(D)},capture_output=True,text=True)
(R/'evidence/public-smoke.log').write_text(p.stdout+p.stderr)
result={'command':'PROJECT_ROOT=<job>/evidence/public-smoke /bin/sh public/smoke.sh','exit_code':p.returncode,'outputs':[str(x.relative_to(D)) for x in (D/'submission/build').glob('*.out')],'semantic_assertions':False,'purpose':'actual public build/API execution entry; raw output for debugging, no scoring'}
(R/'evidence/public-smoke.json').write_text(json.dumps(result,indent=2)+'\n');print(result);assert p.returncode==0 and len(result['outputs'])==3
