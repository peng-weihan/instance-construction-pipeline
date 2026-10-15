from pathlib import Path
import sys, importlib.util,hashlib,json
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'downloads/harbor-src'))
snapshot=Path('/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1/guidance/harbor-0.23.0-task-config.py')
name='harbor.models.task.config'
spec=importlib.util.spec_from_file_location(name,snapshot);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
config=module.TaskConfig.model_validate_toml((root/'task/task.toml').read_text())
# Reject every unknown table/key too: pydantic's default extra=ignore is insufficient.
data=__import__('tomllib').loads((root/'task/task.toml').read_text())
for value,cls,label in [(data,module.TaskConfig,'root'),(data['task'],module.PackageInfo,'task'),(data['agent'],module.AgentConfig,'agent'),(data['environment'],module.EnvironmentConfig,'environment'),(data['verifier'],module.VerifierConfig,'verifier'),(data['verifier']['environment'],module.EnvironmentConfig,'verifier.environment')]:
 assert not set(value)-set(cls.model_fields),(label,set(value)-set(cls.model_fields))
assert config.agent.timeout_sec>=21600
assert config.verifier.environment_mode.value=='separate'
assert all(x.network_mode.value=='no-network' for x in [config.agent,config.environment,config.verifier,config.verifier.environment])
output={'valid':True,'snapshot':str(snapshot),'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'supporting_package':'PyPI harbor==0.23.0 extracted locally, only imported for schema/artifact validators','schema_version':config.schema_version,'unknown_fields':[],'network':'no-network in all scopes','separate_verifier':True,'agent_budget':config.agent.timeout_sec}
(root/'evidence/schema-validation.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output))
