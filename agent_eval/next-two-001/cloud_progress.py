"""Read only our current admission sandbox's aggregate disk/install progress."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,'/ws/users/raymone/edgebench/restler-agent-001/framework-r3/sdk')
from sandbox_smoke import connection,api_options
from e2b import Sandbox
os.environ['TBSCI_E2B_CREDENTIAL_FILE']='/ws/users/wcgu/aliyun-sandbox-runtime/private/connection.json'
r=Path('/ws/users/raymone/edgebench/next-two-001');kind=sys.argv[1]
p=next((r/(kind+'-pilot/admission/jobs/smoke')).glob('*/aliyun-*.json'));state=json.loads(p.read_text());assert not state['destroyed']
box=Sandbox.connect(state['sandbox_id'],timeout=3600,**api_options(connection()))
command='df -h /; du -sm /opt/tbsci-bootstrap /tmp/harbor-parts-* /tmp/harbor-upload-* /home/workspace/brownian-proofs /opt/lean 2>/dev/null || true'
result=box.commands.run(command,user='root',timeout=30)
print(json.dumps({'sandbox_id':state['sandbox_id'],'command_exit':result.exit_code,'disk_and_public_install_progress':result.stdout}))
