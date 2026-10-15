"""One authorized six-hour pilot: official Codex in Aliyun; frozen Docker judge."""
import datetime,hashlib,json,os,shutil,subprocess,sys,tempfile,tomllib
from pathlib import Path
KIND=sys.argv[1]
RUN_NAME=sys.argv[2] if len(sys.argv)>2 else 'run-6h-001'
assert RUN_NAME.startswith('run-6h-') and '/' not in RUN_NAME
assert KIND in ('packing','lean')
ROOT=Path('/ws/users/raymone/edgebench/next-two-001')/(KIND+'-pilot');F=ROOT/'framework';TASK=ROOT/'task';ACCOUNT=Path('/ws/users/wcgu/new-codex-group/raymone')/('2' if KIND=='packing' else '3')
sys.path[:0]=[str(F),str(F/'sdk')]
import toml
from launcher_support import configure
from harbor.models.task.config import TaskConfig,NetworkMode,VerifierEnvironmentMode
from edgebench_harbor.static_native import selected_binding,configure_native_transport
from edgebench_harbor.grading_budget import host_outer_budget

def main():
 life=configure(F)
 controls=json.loads(Path(json.loads((ROOT/'preparation.json').read_text())['controls']).read_text());admission=json.loads((ROOT/'admission/report.json').read_text())
 if not controls['passed'] or not admission['passed']:raise ValueError('actual score controls and official cloud model admission required')
 identity=selected_binding(ACCOUNT)
 if admission['cli_sha256']!=identity['cli_sha256']:raise ValueError('admission identity mismatch')
 if admission['selected_native_identity']['account']!=identity['account']:raise ValueError('admission account mismatch')
 frozen=json.loads((F/'framework-version.json').read_text())
 inventory={p.relative_to(F).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
 if inventory!=frozen['runtime_file_hashes'] or admission['runtime_tree_sha256']!=frozen['runtime_tree_sha256']:raise ValueError('runtime changed after admission')
 context={p.relative_to(TASK/'environment').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (TASK/'environment').rglob('*') if p.is_file()}
 if context!=admission['cloud_context_file_hashes']:raise ValueError('public cloud context changed after admission')
 actual={str(p.relative_to(TASK)):hashlib.sha256(p.read_bytes()).hexdigest() for p in TASK.rglob('*') if p.is_file()}
 preparation=json.loads((ROOT/'preparation.json').read_text())
 if preparation['image_id']!=controls['image_id']:raise ValueError('tested judge image mismatch')
 out=ROOT/RUN_NAME;out.mkdir(mode=0o700,exist_ok=False)
 snapshot=out/'task';shutil.copytree(TASK,snapshot)
 images=json.loads((ROOT/'images.json').read_text());profile=json.loads((TASK/'pipeline-profile.json').read_text())
 if images['verifier']['image_id']!=controls['image_id']:raise ValueError('judge image changed after controls')
 isolation=json.loads((ROOT.parent/(KIND+'-isolation.json')).read_text())
 if not isolation['passed'] or isolation['image']!=controls['image_id']:raise ValueError('actual candidate isolation probe required')
 cfg=TaskConfig.model_validate_toml((snapshot/'task.toml').read_text())
 cfg.environment.network_mode=NetworkMode.ALLOWLIST;cfg.environment.allowed_hosts=[identity['proxy_ip'],'chatgpt.com','api.ipify.org']
 cfg.agent.network_mode=NetworkMode.ALLOWLIST;cfg.agent.allowed_hosts=cfg.environment.allowed_hosts
 cfg.agent.timeout_sec=host_outer_budget(21600,600,120,profile['grading_workers'],profile['verifier_timeout_sec'])
 # BestSubmissionVerifier reads only the host controller's completed grades.
 cfg.verifier.environment_mode=VerifierEnvironmentMode.SHARED;cfg.verifier.environment=None
 cfg.verifier.network_mode=NetworkMode.ALLOWLIST;cfg.verifier.allowed_hosts=cfg.environment.allowed_hosts
 (snapshot/'task.toml').write_text(cfg.model_dump_toml())
 ipc=out/'ipc';ipc.mkdir(mode=0o700)
 (ipc/'public.json').write_text(json.dumps({'artifacts':profile['artifacts'],'snapshot_limit_bytes':64000000,'response_timeout_sec':3600}))
 package=json.loads(Path(os.environ['TBSCI_TOOLCHAIN_MANIFEST']).read_text())['codex']
 protocol={**profile,'backend':'aliyun-learner-docker-verifier','budget_sec':21600,'interval_sec':600,'ipc_host':str(ipc),'controller_root':str(out/'evaluation'),'docker_task_dir':str(snapshot),'verifier_image':images['verifier']['image_id'],'selected_codex_home':str(ACCOUNT),'codex_static_package':package['codex_package_hashes'],'runtime_max_outage_sec':600}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 config=configure_native_transport(tomllib.loads((ACCOUNT/'config.toml').read_text()),'responses-websocket')
 config.update(model='gpt-6.1-sol',model_reasoning_effort='high',web_search='disabled',mcp_servers={},approval_policy='never',sandbox_mode='danger-full-access')
 config.pop('sandbox_workspace_write',None);config.setdefault('features',{}).update(apps=False,hooks=False)
 config.get('shell_environment_policy',{}).get('set',{}).pop('CODEX_HOME',None)
 with tempfile.TemporaryDirectory(prefix='raymone-edge-config-') as temp:
  config_path=Path(temp)/'config.toml';config_path.write_text(toml.dumps(config));config_path.chmod(0o600)
  command=[str(Path(sys.executable).parent/'harbor'),'run','--path',str(snapshot),'--env','edgebench_harbor.official_cloud_supervision:SupervisedOfficialCodexCloudEnvironment','--ek','selected_codex_home='+str(ACCOUNT),'--ek','cloud_context='+str(snapshot/'environment'),'--ek','protocol='+str(out/'protocol.json'),'--agent','codex','--model','gpt-6.1-sol','--ak','version=0.160.0','--ak','reasoning_effort=high','--ak','web_search=disabled','--ak','config='+str(config_path),'--verifier','edgebench_harbor.verifier:BestSubmissionVerifier','--verifier-kwarg','controller_root='+str(out/'evaluation'),'--jobs-dir',str(out/'jobs'),'--job-name','trial','--n-concurrent','1','--n-attempts','1','--max-retries','0','--yes']
  env={k:v for k,v in os.environ.items() if not k.startswith(('OPENAI_','CODEX_','AZURE_','ANTHROPIC_'))};env['CODEX_AUTH_JSON_PATH']=str(ACCOUNT/'auth.json');env['TBSCI_E2B_CREDENTIAL_FILE']='/ws/users/wcgu/aliyun-sandbox-runtime/private/connection.json'
  record={'host_harbor_entry_sha256':hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),'kind':'six_hour_engineering_pilot','formal_acceptance':False,'model':'gpt-6.1-sol','reasoning_effort':'high','account':identity['account'],'runtime_tree_sha256':frozen['runtime_tree_sha256'],'learning_budget_seconds':21600,'evaluation_interval_seconds':600,'difficulty_early_stop':False,'backend':'Aliyun learner + offline Docker verifier','task_hashes':actual,'cli_sha256':identity['cli_sha256'],'command':command,'status':'starting','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  def save():(out/'run-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
  save()
  with (out/'console.log').open('wb') as stream:
   process=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   record.update(status='host_harbor_started',pid=process.pid);save();code=process.wait()
  record.update(status='host_finished',exit_code=code,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
 return code

if __name__=='__main__':sys.exit(main())
