"""Public developer check. Writes only disposable build output and prints SDK traces."""
from pathlib import Path
import subprocess,sys,json
root=Path(__file__).resolve().parents[1]
project=root if (root/'submission').is_dir() else Path('/home/workspace/openapi-streaming')
output=project/'build-public'
output.mkdir(exist_ok=True)
command=[sys.executable,'-m','openapi_python_client','generate','--path',str(root/'public/stream-contract.json'),'--config',str(root/'public/config.json'),'--meta','none','--output-path',str(output/'stream_sdk'),'--overwrite']
r=subprocess.run(command,cwd=project/'submission')
if r.returncode:raise SystemExit(r.returncode)
for mode in ['sync','async']:
    check=subprocess.run([sys.executable,str(root/'public/worker.py'),str(output),'{"action":"records","mode":"'+mode+'"}'],check=True,capture_output=True,text=True)
    print(check.stdout)
    payload=json.loads([line[7:] for line in check.stdout.splitlines() if line.startswith('RESULT ')][-1])
    if payload.get('fatal') or payload.get('error'):raise SystemExit(1)
