"""Create the time origin before beginning agent work, not at first submission."""
import argparse,json,time,uuid
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run-state',required=True);a=p.parse_args()
path=Path(a.run_state);path.parent.mkdir(parents=True,exist_ok=True)
with path.open('x') as f:json.dump({'run_id':str(uuid.uuid4()),'started_unix':time.time(),'agent_budget_seconds':21600},f)
print(path)
