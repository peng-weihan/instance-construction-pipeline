"""Inspect available offline build tools in an owned sandbox; no model/auth files."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,'/ws/users/raymone/edgebench/restler-agent-001/framework-r3/sdk')
from sandbox_smoke import connection,api_options,confirm_delete
from e2b import Sandbox
from e2b.exceptions import SandboxNotFoundException
os.environ['TBSCI_E2B_CREDENTIAL_FILE']='/ws/users/wcgu/aliyun-sandbox-runtime/private/connection.json'
r=Path('/ws/users/raymone/edgebench/next-two-001/template-probe.json');report={'model_calls':0};box=None
try:
 box=Sandbox.create(template='x4inxbpfrrak70x7jqwp',timeout=180,secure=True,allow_internet_access=False,network={'allow_public_traffic':False},metadata={'purpose':'raymone-offline-build-tools-probe'},**api_options(connection()))
 report['sandbox_id']=box.sandbox_id
 command="python3 - <<'PY'\nimport shutil,json,platform,sys,os\nprint(json.dumps({'tools':{s:shutil.which(s) for s in ['gcc','g++','make','cmake','ninja','git','zstd','tar','python3','ld','ar']},'python':sys.version,'libc':platform.libc_ver(),'disk_free_bytes':shutil.disk_usage('/').free}))\nPY"
 result=box.commands.run(command,user='root',timeout=30);report.update(exit_code=result.exit_code,system=json.loads(result.stdout))
finally:
 if box:report['destroyed']=confirm_delete(box,SandboxNotFoundException)
 r.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
