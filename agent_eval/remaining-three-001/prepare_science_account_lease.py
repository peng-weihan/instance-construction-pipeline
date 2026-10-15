"""Adopt and release the existing shared guard's lease, without changing the guard."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OUT=ROOT/'science-pilot'
old=OUT/'framework';new=OUT/'framework-r2'
provider=Path('/root/professional-growth-20261014/framework/aliyun-professional-v019-raymone1-complete-binding-streaming-calibration/edgebench_harbor')
subprocess.run(['cp','-a','--reflink=auto',str(old),str(new)],check=True)
for name in ['global_account_model_slots.py','account_model_slots.py']:
 shutil.copyfile(provider/name,new/'edgebench_harbor'/name)
p=new/'edgebench_harbor/official_cloud_environment.py'
shutil.copyfile(p,p.with_name('unleased_official_cloud_environment.py'))
p.write_text('''"""Use the unchanged shared host guard, with deletion-proven lease release."""
from .unleased_official_cloud_environment import OfficialCodexCloudEnvironment as Parent

class OfficialCodexCloudEnvironment(Parent):
 async def start(self,*args,**kwargs):
  from .account_model_slots import acquire,release
  self._account_model_slot=acquire()
  try:
   await super().start(*args,**kwargs)
   self.evidence['account_model_slot']=self._account_model_slot
   self.save()
  except BaseException:
   if self._account_model_slot and not self.evidence.get('created'):
    release(self._account_model_slot,'startup_failed_before_any_model_entry')
    self._account_model_slot=None
   elif self._account_model_slot:
    await self.stop(delete=True)
   raise

 async def stop(self,delete=True):
  await super().stop(delete=delete)
  if getattr(self,'_account_model_slot',None) and self.evidence.get('destroyed') is True:
   from e2b import AsyncSandbox
   from e2b.exceptions import SandboxNotFoundException
   from sandbox_smoke import connection,api_options
   from .account_model_slots import release
   import datetime
   sid=self.evidence['sandbox_id']
   try:await AsyncSandbox.get_info(sid,**api_options(connection()))
   except SandboxNotFoundException:
    self.evidence['account_model_slot_release_actual_absence']={'sandbox_id':sid,'direct_get_info_exception':'SandboxNotFoundException','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    self.save()
   else:raise RuntimeError('Actual sandbox absence required before releasing the original lease')
   release(self._account_model_slot,'learner_deleted')
   self._account_model_slot=None
''')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
unchanged={}
for name in ['edgebench_harbor/restler_scorer.py','edgebench_harbor/singlecell_scorer_base.py','harbor/agents/installed/codex.py']:
 assert sha(old/name)==sha(new/name);unchanged[name]=sha(new/name)
inventory={p.relative_to(new).as_posix():sha(p) for p in new.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
tree=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()
(new/'framework-version.json').write_text(json.dumps({'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,'runtime_tree_sha256':tree,'runtime_file_hashes':inventory},indent=2)+'\n')
shutil.copyfile(OUT/'preparation.json',OUT/'preparation-before-account-lease.json')
prep=json.loads((OUT/'preparation.json').read_text());prep['runtime_tree_sha256']=tree;prep['runtime_root']=str(new)
(OUT/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
controls=OUT/'scorer-controls/report.json';image=json.loads((OUT/'images.json').read_text())['verifier']['image_id']
assert json.loads(controls.read_text())['image_id']==image
(OUT/'unchanged-scoring-attestation.json').write_text(json.dumps({'original_measured_controls':str(controls),'controls_sha256':sha(controls),'image_id':image,'unchanged_components':unchanged,'changes':['borrow the actual guarded host entry lease','release only after direct SDK not-found'],'score_formula_or_resources_changed':False,'shared_guard_source_modified':False},indent=2)+'\n')
s=(ROOT/'launch_science_agent.py').read_text().replace("F=ROOT/'framework'","F=ROOT/'framework-r2'").replace("ROOT/'admission/report.json'","ROOT/'admission-002/report.json'")
(ROOT/'launch_science_agent_r2.py').write_text(s)
print('new guarded runtime frozen',tree)
