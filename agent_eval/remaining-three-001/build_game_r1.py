from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2];src=ROOT/'samples/remaining-three-built-001/wesnoth_frontier_campaign_ai';dst=ROOT/'samples/remaining-three-built-001/game-task-r1';shutil.copytree(src,dst)
runtime=(src/'verifier/runtime.py').read_text().replace("'--unshare-all','--die-with-parent'","'--unshare-all','--share-net','--uid','2000','--gid','2000','--die-with-parent'")
runtime=runtime.replace("    cmd+=['--bind',str(Path(work).resolve())", "    if Path('/etc/fonts').is_dir():cmd+=['--ro-bind','/etc/fonts','/etc/fonts']\n    cmd+=['--bind',str(Path(work).resolve())")
grader=(src/'verifier/grader.py').read_text().replace('import json,re,shutil,itertools','import json,re,shutil,itertools,time,hashlib')
grader=grader.replace("            try:\n                rc,out,err=run", "            began=time.monotonic()\n            try:\n                rc,out,err=run")
grader=grader.replace("            if rc and 'candidate_policy'", "            logdir=Path('/logs/verifier/engine');logdir.mkdir(parents=True,exist_ok=True)\n            stem=hashlib.sha256(name.encode()).hexdigest()[:16]\n            (logdir/(stem+'.log')).write_text(log)\n            (logdir/(stem+'.json')).write_text(json.dumps({'case':name,'command':args,'exit_code':rc,'seconds':time.monotonic()-began}))\n            if rc and 'candidate_policy'")
for parent in [dst/'verifier',dst/'environment/verifier/verifier']:
    (parent/'runtime.py').write_text(runtime);(parent/'grader.py').write_text(grader)
print(dst)
