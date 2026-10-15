from pathlib import Path
import json,hashlib,tomllib,sys
from harbor.models.task.config import TaskConfig
import harbor.models.task.config as module
R=Path(__file__).resolve().parents[1];T=R/'task'
snapshot=Path('/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1/guidance/harbor-0.23.0-task-config.py')
assert snapshot.read_bytes()==Path(module.__file__).read_bytes(),'schema differs from supplied snapshot'
config=TaskConfig.model_validate_toml((T/'task.toml').read_text())
# Pydantic defaults to ignore extras. Recursively reject unknown supplied fields explicitly.
def fields(value,model):
 for k,v in value.items():
  assert k in type(model).model_fields,(type(model).__name__,k)
  child=getattr(model,k)
  if isinstance(v,dict) and hasattr(child,'model_fields'):fields(v,child)
fields(tomllib.loads((T/'task.toml').read_text()),config)
assert config.verifier.environment_mode.value=='separate'
assert config.agent.timeout_sec>=21600
assert config.environment.network_mode.value=='no-network'
assert config.verifier.environment.network_mode.value=='no-network'
r={'valid':True,'schema_source':'harbor==0.23.0 wheel; byte-identical to supplied snapshot','schema_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'actual_TaskConfig_model_validation':True,'unknown_fields_rejected_by_extra_audit':True,'runtime_or_container_validation':False,'config':config.model_dump(mode='json')}
(R/'evidence/schema-check.json').write_text(json.dumps(r,indent=2)+'\n');print('Actual TaskConfig validation passed; no unsupported fields supplied')
