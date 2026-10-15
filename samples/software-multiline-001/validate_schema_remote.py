"""Read-only validation against the user's actual Harbor source.

No candidates, containers, model calls or shared-source writes are performed.
Python -B suppresses bytecode writes. Requires the existing SSH control socket.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parent
EXPECTED_CONFIG_SHA = "d8c62a49acefb8cd6a0be4c4d48dc0f4f52f31f8a8a6728439aad04e1c62e9fb"


def main() -> None:
    plan = json.loads((ROOT / "routes.json").read_text())
    payload = {}
    input_hashes = {}
    for route in plan["routes"]:
        path = ROOT / route["id"] / "task.toml"
        if path.is_file():
            raw = path.read_bytes()
            payload[route["id"]] = tomllib.loads(raw.decode())
            input_hashes[route["id"]] = hashlib.sha256(raw).hexdigest()
    if not payload:
        raise SystemExit("No task.toml files yet; no remote call made")
    program = r'''
import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
source=Path('/ws/users/wcgu/edgebench/dev/harbor')
sys.path.insert(0,str(source/'src'))
from harbor.models.task.config import TaskConfig,AgentConfig,VerifierConfig,EnvironmentConfig,SolutionConfig
actual=hashlib.sha256((source/'src/harbor/models/task/config.py').read_bytes()).hexdigest()
if actual!=EXPECTED: raise RuntimeError('source changed; refresh provenance before validation')
records=[]
for name,data in PAYLOAD.items():
    unknown=[]
    for prefix,obj,model in [('',data,TaskConfig),('agent',data.get('agent',{}),AgentConfig),('environment',data.get('environment',{}),EnvironmentConfig),('verifier',data.get('verifier',{}),VerifierConfig),('verifier.environment',data.get('verifier',{}).get('environment',{}),EnvironmentConfig),('solution',data.get('solution',{}),SolutionConfig)]:
        unknown.extend((prefix+'.' if prefix else '')+key for key in obj if key not in model.model_fields)
    try:
        config=TaskConfig.model_validate(data)
        records.append({'route':name,'model_validation':'pass','unknown_keys':unknown,'strict_known_fields_pass':not unknown,'agent_network':str(config.agent.network_mode)})
    except Exception as error:
        records.append({'route':name,'model_validation':'fail','unknown_keys':unknown,'error':str(error)})
print(json.dumps({'config_sha256':actual,'records':records,'scope':'actual TaskConfig validation only, not task/container execution'}))
'''
    # Input is Python stdin, not shell interpolation; candidate text is never executed.
    program = "EXPECTED=" + repr(EXPECTED_CONFIG_SHA) + "\nPAYLOAD=json.loads(" + repr(json.dumps(payload)) + ")\n" + program
    # json must be imported before the payload declaration.
    program = "import json\n" + program
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "-o", "ControlPath=/tmp/edgebench-raymone-smoke.sock", "root@173.231.10.234", "/ws/users/wcgu/edgebench/venv/bin/python", "-B", "-"]
    result = subprocess.run(command, input=program, text=True, capture_output=True, timeout=45)
    changed = [name for name, digest in input_hashes.items() if hashlib.sha256((ROOT/name/'task.toml').read_bytes()).hexdigest()!=digest]
    evidence = {"command": command, "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "input_config_sha256": input_hashes, "inputs_changed_during_validation": changed, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "schema_acceptance_only": True, "runtime_verified": False}
    if result.returncode == 0:
        evidence["result"] = json.loads(result.stdout)
    (ROOT / "schema-validation.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(evidence.get("result", {"returncode": result.returncode, "stderr": result.stderr}), ensure_ascii=False))


if __name__ == "__main__":
    main()
