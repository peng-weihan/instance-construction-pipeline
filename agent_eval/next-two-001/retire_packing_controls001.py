from pathlib import Path
import os,signal,json,subprocess,datetime
r=Path('/ws/users/raymone/edgebench/next-two-001');p=r/'packing-controls-001/report.json';d=json.loads(p.read_text())
if d['status']=='running':
 pid=2729162;cmd=Path('/proc',str(pid),'cmdline')
 if cmd.exists():
  text=cmd.read_bytes().replace(b'\0',b' ').decode();assert 'controls.py packing --revision 001' in text;os.kill(pid,signal.SIGTERM)
 ids=subprocess.check_output(['docker','ps','-aq','--filter','name=edge-raymone-packing-control-'],text=True).split()
 for cid in ids:
  info=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
  if any(str(r/'packing-controls-001') in m.get('Source','') for m in info['Mounts']):subprocess.run(['docker','rm','-f',cid],check=True)
 d.update(status='completed',passed=False,interrupted=True,reason='author replaced single-core compilation with declared two-CPU compilation before model run; no uncompleted scores assigned',replacement='packing-controls-002',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());p.write_text(json.dumps(d,indent=2)+'\n')
print(d['status'],d.get('reason'))
