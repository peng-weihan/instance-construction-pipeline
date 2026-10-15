"""Inspect the actual candidate namespace through the same trusted judge runtime."""
import json, subprocess, uuid
from pathlib import Path
R=Path('/ws/users/raymone/edgebench/restler-agent-001')
e=json.loads((R/'controls-r4/reference/grade/execution.json').read_text())
argv=e['command']
argv[argv.index('--name')+1]='edge-raymone-probe-'+uuid.uuid4().hex[:12]
image=argv.pop()
probe="""import os,json;from pathlib import Path;print(json.dumps({'uid':os.getuid(),'gid':os.getgid(),'judge_visible':Path('/judge').exists(),'status':[x for x in Path('/proc/self/status').read_text().splitlines() if x.startswith(('CapEff:','NoNewPrivs:'))],'uid_map':Path('/proc/self/uid_map').read_text(),'routes':Path('/proc/net/route').read_text()}))"""
code="from runtime import run,workdir;\nwith workdir() as work:\n rc,out,err=run(work,['python','-c',"+repr(probe)+"]);print(out);print(err);assert rc==0\n"
argv+=['--entrypoint','/opt/runtime/venv/bin/python',image,'-c',code]
p=subprocess.run(argv,capture_output=True,text=True,timeout=90)
report={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'image':image}
if p.returncode==0:
 data=json.loads(p.stdout);report['candidate']=data
 report['passed']=data['uid']==2000 and data['gid']==2000 and not data['judge_visible'] and 'CapEff:\t0000000000000000' in data['status'] and len(data['routes'].splitlines())==1
else:report['passed']=False
(R/'judge-isolation-r4.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
