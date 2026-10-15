"""Prepare a new owned scientific pilot with a real offline ML runtime."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tarfile
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
SOURCE=ROOT/'singlecell_cross_site_graph_lab-r2'
OUT=ROOT/'science-pilot';OUT.mkdir()
OLD=ROOT/'game-pilot';F=OUT/'framework'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
subprocess.run(['cp','-a','--reflink=auto',str(OLD/'framework'),str(F)],check=True)
sys.path[:0]=[str(F),str(F/'sdk')]
from harbor.models.task.config import TaskConfig,EnvironmentConfig,AgentConfig,VerifierConfig
p=F/'edgebench_harbor/static_native.py';p.write_text(p.read_text().replace(str(OLD/'activity'),str(OUT/'activity')))
# Keep old experiments immutable. Only this new scorer retries pre-start faults.
p=F/'edgebench_harbor/restler_scorer.py';shutil.copyfile(p,p.with_name('singlecell_scorer_base.py'))
shutil.copyfile(ROOT/'singlecell_scorer.py',p)
assert sha(F/'harbor/agents/installed/codex.py')=='ee0ca8ec43617f3909d2195afe8f9e7cbd7313a8b3b558b01fde388f65b7c39c'
judge=OUT/'judge';judge.mkdir()
for name in ['public','private','verifier']:shutil.copytree(SOURCE/name,judge/name)
recipe='''FROM edge-raymone-science:ml-runtime-001
RUN rm -rf /judge/public /judge/private /judge/verifier
COPY public /judge/public
COPY private /judge/private
COPY verifier /judge/verifier
RUN /opt/runtime/venv/bin/python -m pip freeze > /opt/runtime/ml-requirements.lock.txt
ENTRYPOINT ["/opt/runtime/venv/bin/python", "/judge/verifier/judge_entry.py"]
'''
(judge/'Dockerfile').write_text(recipe)
with (OUT/'judge-build.log').open('wb') as log:
 subprocess.run(['docker','build','--network','none','-t','edge-raymone-science:pilot-001',str(judge)],stdout=log,stderr=subprocess.STDOUT,check=True)
image=subprocess.check_output(['docker','image','inspect','edge-raymone-science:pilot-001','--format','{{.Id}}'],text=True).strip()
task=OUT/'task';context=task/'environment';context.mkdir(parents=True)
shutil.copytree(SOURCE/'public',context/'public')
shutil.copytree(SOURCE/'solution',task/'solution')
shutil.copytree(F/'public-native-audit',context/'native-audit')
assets=OUT/'public-runtime';runtime=assets/'opt/runtime';runtime.mkdir(parents=True)
for name in ['edge-python','edge-system-libs']:
 subprocess.run(['cp','-a','--reflink=auto',str(ROOT/'finance-pilot/public-runtime/opt/runtime'/name),str(runtime/name)],check=True)
cid=subprocess.check_output(['docker','create',image],text=True).strip()
try:
 subprocess.run(['docker','cp',cid+':/opt/runtime/venv',str(runtime/'venv')],check=True)
 subprocess.run(['docker','cp',cid+':/opt/runtime/ml-requirements.lock.txt',str(runtime/'ml-requirements.lock.txt')],check=True)
finally:subprocess.run(['docker','rm',cid],check=True,stdout=subprocess.DEVNULL)
wrapper='''#!/bin/sh
export PYTHONHOME=/opt/runtime/edge-python
export PYTHONPATH=/opt/runtime/venv/lib/python3.12/site-packages
export NUMBA_CACHE_DIR="${NUMBA_CACHE_DIR:-/tmp/edge-numba-cache-$(id -u)}"
exec /opt/runtime/edge-system-libs/ld-linux-x86-64.so.2 --library-path /opt/runtime/edge-system-libs /opt/runtime/edge-python/bin/python3.12 "$@"
'''
for name in ['python','python3','python3.12']:
 p=runtime/'venv/bin'/name
 if p.exists() or p.is_symlink():p.unlink()
 p.write_text(wrapper);p.chmod(0o755)
# Exercise the portable loader and binary wheels exactly as installed in cloud.
test="import numpy,scipy,sklearn,torch,h5py,scanpy,harmonypy; x=torch.ones((3,3));print(torch.__version__,sklearn.__version__,float((x@x).sum()))"
check=subprocess.run(['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp:rw,size=1g','--mount','type=bind,source='+str(runtime)+',target=/opt/runtime,readonly','--entrypoint','/opt/runtime/venv/bin/python',image,'-c',test],capture_output=True,text=True)
dump(OUT/'portable-runtime-check.json',{'returncode':check.returncode,'stdout':check.stdout,'stderr':check.stderr})
if check.returncode:raise RuntimeError('portable offline ML runtime failed')
with tarfile.open(context/'runtime.tar.gz','w:gz',compresslevel=1) as tar:tar.add(assets/'opt',arcname='opt')
shutil.copyfile(ROOT/'finance-pilot/task/environment/aliyun.json',context/'aliyun.json')
work='/home/workspace/cellgraph'
boot=(ROOT/'finance-pilot/task/environment/bootstrap.sh').read_text().replace('/home/workspace/adaptive-allocation',work)
boot=boot.replace("import numpy,scipy;print(numpy.__version__,scipy.__version__)","import numpy,scipy,sklearn,torch,h5py,scanpy;print(numpy.__version__,sklearn.__version__,torch.__version__)")
(context/'bootstrap.sh').write_text(boot)
(task/'instruction.md').write_text((SOURCE/'instruction.md').read_text())
profile={'workdir':work,'submission_root':work+'/submission','artifacts':[work+'/submission'],'selection':'valid_then_score','score_direction':'maximize','verifier_timeout_sec':600,'cooldown_sec':120,'grading_workers':1,'judge_cpuset':'6,7'}
dump(task/'pipeline-profile.json',profile)
cfg=TaskConfig(metadata={'name':'singlecell-cross-site-pilot','reward_type':'bounded_continuous','formal_acceptance':False},environment=EnvironmentConfig(workdir=work,cpus=4,memory_mb=16384,storage_mb=15360,network_mode='no-network'),agent=AgentConfig(user='agent',timeout_sec=28800,network_mode='no-network'),verifier=VerifierConfig(timeout_sec=600,network_mode='no-network'),artifacts=profile['artifacts'])
(task/'task.toml').write_text(cfg.model_dump_toml());(task/'tests').mkdir()
(task/'tests/test.sh').write_text('#!/bin/sh\nset -eu\nexec /opt/runtime/venv/bin/python /judge/verifier/judge_entry.py\n')
oldimages=json.loads((OLD/'images.json').read_text());oldimages['verifier']['image_id']=image;dump(OUT/'images.json',oldimages)
inventory={p.relative_to(F).as_posix():sha(p) for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
tree=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()
dump(F/'framework-version.json',{'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,'runtime_tree_sha256':tree,'runtime_file_hashes':inventory})
dump(OUT/'preparation.json',{'source_task':str(SOURCE),'image_id':image,'account':'raymone/1','model':'gpt-6.1-sol','runtime_tree_sha256':tree,'runtime_archive_sha256':sha(context/'runtime.tar.gz'),'official_adapter_unchanged':True,'formal_acceptance':False})
launch=(ROOT/'launch_agent.py').read_text().replace("assert KIND in ('game','finance')","assert KIND=='science'").replace("ROOT/'admission-002/report.json'","ROOT/'admission/report.json'")
(ROOT/'launch_science_agent.py').write_text(launch)
print('science pilot prepared',image,flush=True)
