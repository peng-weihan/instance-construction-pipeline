"""Test the other two user-authorized accounts without altering the live runtime."""
from pathlib import Path
import hashlib,json,subprocess
R=Path('/ws/users/raymone/edgebench/restler-agent-001')
for number,host,port in [(2,'216.132.206.229',7552),(3,'72.245.133.249',6930)]:
 home=Path('/ws/users/wcgu/new-codex-group/raymone')/str(number)
 assert (home/'auth.json').is_file()
 f=R/('framework-raymone'+str(number));assert not f.exists()
 subprocess.run(['cp','-a','--reflink=auto',str(R/'framework-r3'),str(f)],check=True)
 p=f/'edgebench_harbor/static_native.py'
 s=p.read_text().replace('raymone/1','raymone/'+str(number)).replace('Raymone1','Raymone'+str(number)).replace('206.135.156.134',host).replace('7056',str(port))
 p.write_text(s)
 inventory={p.relative_to(f).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in f.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
 sha=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()
 (f/'framework-version.json').write_text(json.dumps({'status':'frozen','kind':'raymone_account_admission','formal_acceptance':False,'runtime_tree_sha256':sha,'runtime_file_hashes':inventory},indent=2)+'\n')
 cmd=['/ws/users/wcgu/aliyun-sandbox-runtime/bin/aliyun-python',str(f/'check_docker_admission.py'),'--backend','aliyun','--cloud-context',str(R/'task-r4/environment'),'--task',str(R/'task-r4'),'--images',str(R/'images-r4.json'),'--codex-home',str(home),'--output',str(R/('admission-raymone'+str(number))),'--native-transport','responses-websocket']
 with (R/('admission-raymone'+str(number)+'.log')).open('wb') as log:
  p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 print(json.dumps({'account':'raymone/'+str(number),'pid':p.pid,'kind':'small_admission_only'}),flush=True)
