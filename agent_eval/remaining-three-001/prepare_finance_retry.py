"""Prepare a fresh independent finance rollout, preserving task and prior traces."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
OLD=ROOT/'finance-pilot-r2';OUT=ROOT/'finance-pilot-r3';OUT.mkdir()
SCI=ROOT/'science-pilot/framework-r2';F=OUT/'framework'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['cp','-a','--reflink=auto',str(SCI),str(F)],check=True)
subprocess.run(['cp','-a','--reflink=auto',str(OLD/'task'),str(OUT/'task')],check=True)
shutil.copyfile(OLD/'images.json',OUT/'images.json')
shutil.copyfile(OLD/'isolation.json',OUT/'isolation.json')
for rel,oldrel in [('edgebench_harbor/singlecell_scorer_base.py','edgebench_harbor/restler_scorer.py'),('edgebench_harbor/cloud.py','edgebench_harbor/cloud.py'),('edgebench_harbor/unleased_official_cloud_environment.py','edgebench_harbor/official_cloud_environment.py')]:
 assert sha(F/rel)==sha(OLD/'framework'/oldrel),rel
p=F/'edgebench_harbor/static_native.py';p.write_text(p.read_text().replace(str(ROOT/'science-pilot/activity'),str(OUT/'activity')))
task_hashes={p.relative_to(OUT/'task').as_posix():sha(p) for p in (OUT/'task').rglob('*') if p.is_file()}
assert task_hashes=={p.relative_to(OLD/'task').as_posix():sha(p) for p in (OLD/'task').rglob('*') if p.is_file()}
inventory={p.relative_to(F).as_posix():sha(p) for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
tree=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()
dump(F/'framework-version.json',{'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,'runtime_tree_sha256':tree,'runtime_file_hashes':inventory})
prep=json.loads((OLD/'preparation.json').read_text());prep.update(runtime_tree_sha256=tree,runtime_root=str(F),previous_interrupted_trial=str(OLD/'run-6h-001'),independent_session_from_starter=True,docker_prestart_125_retries=2,shared_guard_lease_lifecycle=True)
dump(OUT/'preparation.json',prep)
dump(OUT/'source-component-attestation.json',{'previous_task':str(OLD/'task'),'task_file_hashes_unchanged':task_hashes,'judge_image_id':prep['image_id'],'scoring_implementation_sha256':sha(F/'edgebench_harbor/singlecell_scorer_base.py'),'old_control_report_sha256':sha(OLD/'scorer-controls/report.json'),'formula_data_and_resources_unchanged':True,'new_features':['retry only Docker pre-start exit125 with no result','existing guarded shared-account lease, release after SDK not-found'],'old_runs_modified':False})
s=(ROOT/'launch_agent.py').read_text().replace("assert KIND in ('game','finance')","assert KIND=='finance'").replace("/(KIND+'-pilot')","/(KIND+'-pilot-r3')").replace("ROOT/'admission-002/report.json'","ROOT/'admission/report.json'")
(ROOT/'launch_finance_retry.py').write_text(s)
# Named copies of the existing actual audit tools. Shared original source stays untouched.
tools=OUT/'capacity-audit';(tools/'authoring').mkdir(parents=True);(tools/'reports').mkdir()
origin=Path('/root/professional-growth-20261014/authoring')
p=origin/'audit_all_current_host_cloud_including_raymone123_r1.py'
s=p.read_text().replace("C=Path('/root/professional-growth-20261014/reports')","C=Path("+repr(str(tools/'reports'))+")").replace("F=Path('/root/professional-growth-20261014/framework/aliyun-professional-v010-account2-complete-binding-shared-host-lease')","F=Path("+repr(str(F))+")")
(tools/'authoring'/p.name).write_text(s)
shutil.copyfile(origin/'review_raymone123_actual_unused_accounts_r1.py',tools/'authoring/review_raymone123_actual_unused_accounts_r1.py')
s=(origin/'refresh_shared_raymone2_capacity_r3.py').read_text().replace('raymone/2','raymone/1').replace('raymone2','raymone1').replace('.professional-shared-refresh.tmp','.raymone-finance-shared-refresh.tmp')
s=s.replace("'authorization':'User explicitly permits sharing raymone/1 even when others use it'","'authorization':'User authorized supplied raymone accounts and requested a fresh finance rollout; preserve all shared leases and reservations'")
s=s.replace("'authorization_user_text':'不是不是,raymone/1不要管,有人用你也可以用'","'authorization_user_text':'金融那一题，再roll一次吧；此前授权raymone/1,2,3'")
(tools/'authoring/refresh_capacity.py').write_text(s)
dump(tools/'copied-tool-provenance.json',{'original_readonly_sources':{p.name:sha(p) for p in [origin/'audit_all_current_host_cloud_including_raymone123_r1.py',origin/'review_raymone123_actual_unused_accounts_r1.py',origin/'refresh_shared_raymone2_capacity_r3.py']},'changes':['owned audit output directory','explicit authorized account raymone/1','current user authorization text'],'preserve_all_existing_leases_and_external_reservations':True,'unreserved_Docker_native_or_SDK_usage_blocks_admission':True,'original_guard_source_modified':False})
print('fresh finance task and guarded framework prepared',tree,flush=True)
