"""Prepare a private verifier / public Aliyun learner pilot after real controls."""
import argparse,hashlib,json,shutil,subprocess,sys,tarfile
from pathlib import Path
R=Path('/ws/users/raymone/edgebench/next-two-001')
PREV=Path('/ws/users/raymone/edgebench/restler-agent-001')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(kind,revision):
 account=2 if kind=='packing' else 3
 source=R/(kind+('-task-r5' if kind=='packing' else '-task-r3'));out=R/(kind+'-pilot');out.mkdir(exist_ok=False)
 F=out/'framework';subprocess.run(['cp','-a','--reflink=auto',str(PREV/('framework-raymone'+str(account))),str(F)],check=True)
 sys.path[:0]=[str(F),str(F/'sdk')]
 from harbor.models.task.config import TaskConfig,EnvironmentConfig,AgentConfig,VerifierConfig
 controls=json.loads((R/(kind+'-controls-'+revision+'/report.json')).read_text());assert controls['passed']
 task=out/'task';context=task/'environment';context.mkdir(parents=True)
 shutil.copytree(source/'public',context/'public');shutil.copytree(source/'solution',task/'solution')
 shutil.copytree(F/'public-native-audit',context/'native-audit')
 stage=R/'lean-runtime-stage'
 if kind=='lean' and (stage/'report.json').exists():
  staged=json.loads((stage/'report.json').read_text());assert staged['source_image_id']==controls['base_image_id']
  assets=out/'public-runtime';shutil.move(str(stage/'assets'),assets)
  archive=context/'runtime.tar.gz';shutil.move(str(stage/'runtime.tar.gz'),archive)
  assert digest(archive)==staged['sha256']
 else:
  assets=out/'public-runtime';assets.mkdir()
  cid=subprocess.check_output(['docker','create',controls['image_id']],text=True).strip()
  def cp(remote,local):
   local.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['docker','cp',cid+':'+remote,str(local)],check=True)
  try:
   if kind=='lean':
    cp('/opt/runtime/elan/toolchains/leanprover--lean4---v4.33.0-rc1',assets/'opt/lean')
    cp('/opt/runtime/lean-project',assets/'opt/runtime/lean-project')
   else:
    cp('/opt/runtime/packing-build/_deps',assets/'opt/runtime/packing-build/_deps')
    for p in (assets/'opt/runtime/packing-build/_deps').iterdir():
     if not p.name.endswith('-src'):
      if p.is_dir():shutil.rmtree(p)
      else:p.unlink()
    cp('/opt/runtime/packing-dependencies.json',assets/'opt/runtime/packing-dependencies.json')
    cp('/opt/runtime/venv/lib/python3.12/site-packages/cmake/data',assets/'opt/edge-cmake')
  finally:subprocess.run(['docker','rm',cid],check=True,stdout=subprocess.DEVNULL)
  assert not any(p.name in ('auth.json','static-egress.json') for p in assets.rglob('*'))
  archive=context/'runtime.tar.gz'
  with tarfile.open(archive,'w:gz',compresslevel=1) as tar:tar.add(assets/'opt',arcname='opt')
 if kind=='lean':
  # Consume compressed parts as they are extracted, keeping the 15 GB cloud
  # disk below its limit while unpacking the 11 GB Lean dependency closure.
  with archive.open('rb') as stream:
   index=0
   while block:=stream.read(128*1024*1024):
    (context/('runtime-part-%05d'%index)).write_bytes(block);index+=1
  held=out/'runtime.tar.gz';archive.rename(held);archive=held
 print('runtime_archive_ready',kind,archive.stat().st_size,flush=True)
 work='/home/workspace/'+('industrial-nesting' if kind=='packing' else 'brownian-proofs')
 boot='''set -eu
CTX=/opt/tbsci-bootstrap
WORK=WORK_PATH
tar -xzf "$CTX/runtime.tar.gz" -C /
rm "$CTX/runtime.tar.gz"
mkdir -p "$WORK" /opt/edgebench-native-audit
cp -a "$CTX/public/." "$WORK/"
cp -a "$CTX/native-audit/." /opt/edgebench-native-audit/
chmod -R a+rX,go-w /opt/edgebench-native-audit
chmod 755 /opt/edgebench-native-audit/bin/*
ln -sf /opt/codex-static/codex-path/rg /usr/local/bin/rg
'''.replace('WORK_PATH',work)
 if kind=='lean':boot=boot.replace('tar -xzf "$CTX/runtime.tar.gz" -C /\nrm "$CTX/runtime.tar.gz"','set -o pipefail\n{ for part in "$CTX"/runtime-part-*; do cat "$part"; rm "$part"; done; } | tar -xzf - -C /')
 if kind=='packing':
  shutil.copyfile(source/'verifier/build.py',context/'public/build.py')
  boot+='''mv "$WORK/repo" "$WORK/submission"
ln -s submission "$WORK/repo"
ln -sf /opt/edge-cmake/bin/cmake /usr/local/bin/cmake
cmake --version
g++ --version
'''
 else:
  files=sorted({t['file'] for t in json.loads((source/'public/targets.json').read_text())})
  boot+='''rm -rf "$WORK/repo"
mv /opt/runtime/lean-project "$WORK/repo"
mkdir "$WORK/submission"
ln -sf /opt/lean/bin/lean /usr/local/bin/lean
ln -sf /opt/lean/bin/lake /usr/local/bin/lake
python3 - <<'PY'
from pathlib import Path
import shutil
w=Path(WORK_LITERAL)
for name in FILES_LITERAL:
 p=w/'repo'/name;target=w/'submission'/name;target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(p,target);p.unlink();p.symlink_to(target)
PY
cd "$WORK/repo"
lake env lean --version
'''.replace('WORK_LITERAL',repr(work)).replace('FILES_LITERAL',repr(files))
 boot+='chown -R agent:agent "$WORK"\n'
 if kind=='packing':boot+='su -s /bin/sh agent -c "cd $WORK && python3 build.py"\n'
 else:boot+='su -s /bin/sh agent -c "cd $WORK/repo && LEAN_NUM_THREADS=1 lake build BrownianMotion.Gaussian.CovMatrix BrownianMotion.Continuity.CoveringNumber BrownianMotion.Gaussian.Moment BrownianMotion.Gaussian.BrownianMotion BrownianMotion.Continuity.KolmogorovChentsov"\n'
 (context/'bootstrap.sh').write_text(boot)
 (context/'aliyun.json').write_text((PREV/'task-r4/environment/aliyun.json').read_text())
 instruction=(source/'instruction.md').read_text()+'\n工作目录：'+work+'。只提交 submission/ 中的源码；repo/ 用于构建和阅读完整工程。'
 if kind=='packing':instruction+='在工作目录运行 python3 build.py 可离线构建，产物写入工作目录下 build/。'
 else:instruction+='在 repo/ 中运行 lake build；五个目标文件链接到 submission/ 中可编辑的副本，依赖均已离线准备。'
 instruction+='\n完整运行预算六小时，每十分钟自动捕获源码并评分；可用 sforge-submit 主动提交查看反馈。成绩取最好有效提交；持续探索和改进，不因一次通过而停止。\n'
 (task/'instruction.md').write_text(instruction)
 artifacts=[work+'/submission'] if kind=='lean' else [work+'/submission/src/irregular',work+'/submission/include/packingsolver/irregular']
 profile={'workdir':work,'submission_root':work+'/submission','artifacts':artifacts,'selection':'valid_then_score','score_direction':'maximize','verifier_timeout_sec':1800,'cooldown_sec':120,'grading_workers':2}
 (task/'pipeline-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
 cfg=TaskConfig(metadata={'name':kind+'-cloud-pilot','reward_type':'bounded_continuous','formal_acceptance':False},environment=EnvironmentConfig(workdir=work,cpus=4,memory_mb=16384,storage_mb=15360,network_mode='no-network'),agent=AgentConfig(user='agent',timeout_sec=28800,network_mode='no-network'),verifier=VerifierConfig(timeout_sec=1800,network_mode='no-network'),artifacts=artifacts)
 (task/'task.toml').write_text(cfg.model_dump_toml())
 (task/'tests').mkdir();shutil.copyfile(R/(kind+'-controls-'+revision+'/judge/test.sh'),task/'tests/test.sh')
 scorer=(PREV/'framework-r3/edgebench_harbor/restler_scorer.py').read_text().replace("self.timeout_sec=timeout_sec;", "self.timeout_sec=timeout_sec;self.submission_root=json.loads((self.task_dir/'pipeline-profile.json').read_text())['submission_root'].lstrip('/');")
 scorer=scorer.replace("Path(snapshot)/'home/workspace/restler-resilient/submission'","Path(snapshot)/self.submission_root").replace('/tmp:rw,exec,size=12g','/tmp:rw,exec,size=20g').replace("'--memory','12g'","'--memory','28g'")
 (F/'edgebench_harbor/restler_scorer.py').write_text(scorer)
 p=F/'edgebench_harbor/static_native.py';p.write_text(p.read_text().replace(str(PREV/'activity'),str(out/'activity')))
 inventory={p.relative_to(F).as_posix():digest(p) for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
 tree=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()
 (F/'framework-version.json').write_text(json.dumps({'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,'runtime_tree_sha256':tree,'runtime_file_hashes':inventory},indent=2)+'\n')
 images={'agent':{'image_id':json.loads((PREV/'images-r4.json').read_text())['agent']['image_id']},'verifier':{'image_id':controls['image_id']}}
 (out/'images.json').write_text(json.dumps(images,indent=2)+'\n')
 provenance={'account':'raymone/'+str(account),'source_task':str(source),'controls':str(R/(kind+'-controls-'+revision+'/report.json')),'image_id':controls['image_id'],'runtime_tree_sha256':tree,'runtime_archive_sha256':digest(archive),'runtime_archive_bytes':archive.stat().st_size,'formal_acceptance':False}
 (out/'preparation.json').write_text(json.dumps(provenance,indent=2)+'\n');print('PREPARED',out,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['packing','lean']);p.add_argument('--revision',required=True);a=p.parse_args();main(a.kind,a.revision)
