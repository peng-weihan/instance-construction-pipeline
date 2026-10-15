"""Prepare authorized full-six-hour engineering pilots in new owned directories."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,sys,tarfile
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OLD=ROOT.parent/'restler-agent-001'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main(kind):
 revision='r4' if kind=='game' else 'r3';source=ROOT/(kind+'-task-'+revision);out=ROOT/(kind+'-pilot');out.mkdir()
 controls=json.loads((ROOT/(kind+'-reuse-controls-'+revision+('/report.json' if kind=='game' else '-extra/report.json'))).read_text());assert controls['passed']
 if kind=='game':assert controls['reference_deterministic']
 framework=out/'framework';subprocess.run(['cp','-a','--reflink=auto',str(OLD/'framework-r3'),str(framework)],check=True)
 sys.path[:0]=[str(framework),str(framework/'sdk')]
 from harbor.models.task.config import TaskConfig,EnvironmentConfig,AgentConfig,VerifierConfig
 # New copy only: preserve previous runs and the official Codex adapter.
 cloud=framework/'edgebench_harbor/cloud.py';cloud.write_text(cloud.read_text().replace("('/logs/agent','/artifacts')", "('/logs/agent','/artifacts','/logs/artifacts')"))
 scorer=(framework/'edgebench_harbor/restler_scorer.py').read_text()
 scorer=scorer.replace("self.timeout_sec=timeout_sec;", "self.timeout_sec=timeout_sec;self.submission_root=json.loads((self.task_dir/'pipeline-profile.json').read_text())['submission_root'].lstrip('/');")
 scorer=scorer.replace("Path(snapshot)/'home/workspace/restler-resilient/submission'", "Path(snapshot)/self.submission_root")
 scorer=scorer.replace("report.get('valid') is not True", "type(report.get('valid')) is not bool or (not report['valid'] and reward!=0)")
 (framework/'edgebench_harbor/restler_scorer.py').write_text(scorer)
 activity=framework/'edgebench_harbor/static_native.py';activity.write_text(activity.read_text().replace(str(OLD/'activity'),str(out/'activity')))
 assert sha(framework/'harbor/agents/installed/codex.py')==sha(OLD/'framework-r3/harbor/agents/installed/codex.py')
 # Bake the exact tested scoring source and patched engine into an immutable judge.
 judge=out/'judge';judge.mkdir()
 for folder in ['public','private','verifier']:shutil.copytree(source/folder,judge/folder)
 shutil.copyfile(ROOT/'judge_entry.py',judge/'verifier/judge_entry.py')
 initial='edge-raymone-game:initial';base_id=subprocess.check_output(['docker','image','inspect',initial,'--format','{{.Id}}'],text=True).strip()
 recipe='FROM '+initial+'\nCOPY public /judge/public\nCOPY private /judge/private\nCOPY verifier /judge/verifier\n'
 if kind=='game':
  binary=ROOT/'game-entropy-build-004/wesnoth';assert sha(binary)==controls['patched_binary_sha256'];shutil.copyfile(binary,judge/'wesnoth');(judge/'wesnoth').chmod(0o755)
  recipe+='COPY wesnoth /opt/runtime/wesnoth/bin/wesnoth\n'
 recipe+='ENTRYPOINT ["/opt/runtime/venv/bin/python", "/judge/verifier/judge_entry.py"]\n';(judge/'Dockerfile').write_text(recipe)
 tag='edge-raymone-'+kind+':pilot-001'
 with (out/'judge-build.log').open('wb') as log:subprocess.run(['docker','build','--network','none','-t',tag,str(judge)],stdout=log,stderr=subprocess.STDOUT,check=True)
 image=subprocess.check_output(['docker','image','inspect',tag,'--format','{{.Id}}'],text=True).strip()
 task=out/'task';context=task/'environment';context.mkdir(parents=True);shutil.copytree(source/'public',context/'public')
 shutil.copytree(source/'solution',task/'solution');shutil.copytree(framework/'public-native-audit',context/'native-audit')
 # Extract only public runtime dependencies. No /judge, credentials or private config.
 assets=out/'public-runtime';assets.mkdir();cid=subprocess.check_output(['docker','create',base_id],text=True).strip()
 def cp(remote,dest):
  dest.parent.mkdir(parents=True,exist_ok=True);subprocess.run(['docker','cp',cid+':'+remote,str(dest)],check=True)
 try:
  cp('/opt/runtime/venv',assets/'opt/runtime/venv')
  if kind=='game':
   cp('/opt/runtime/wesnoth',assets/'opt/runtime/wesnoth');shutil.copyfile(ROOT/'game-entropy-build-004/wesnoth',assets/'opt/runtime/wesnoth/bin/wesnoth');(assets/'opt/runtime/wesnoth/bin/wesnoth').chmod(0o755)
   ldd=subprocess.check_output(['docker','run','--rm','--network','none','--read-only','--entrypoint','ldd',base_id,'/opt/runtime/wesnoth/bin/wesnoth'],text=True)
   (out/'engine-ldd.txt').write_text(ldd)
   libs=assets/'opt/runtime/edge-game-libs';libs.mkdir()
   for remote in sorted(set(re.findall(r'=> (/[^\s]+)',ldd))):
    # Follow image symlinks, preserving the needed SONAME as a real public file.
    dest=libs/Path(remote).name;subprocess.run(['docker','cp','-L',cid+':'+remote,str(dest)],check=True)
 finally:subprocess.run(['docker','rm',cid],check=True,stdout=subprocess.DEVNULL)
 assert not any(p.name in ['auth.json','static-egress.json','connection.json'] for p in assets.rglob('*'))
 archive=context/'runtime.tar.gz'
 with tarfile.open(archive,'w:gz',compresslevel=1) as tar:tar.add(assets/'opt',arcname='opt')
 work='/home/workspace/'+('frontier-campaign' if kind=='game' else 'adaptive-allocation')
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
ln -sf /opt/runtime/venv/bin/python /usr/local/bin/python
chown -R agent:agent "$WORK"
/opt/runtime/venv/bin/python -c 'import numpy,scipy;print(numpy.__version__,scipy.__version__)'
'''.replace('WORK_PATH',work)
 if kind=='game':boot+="LD_LIBRARY_PATH=/opt/runtime/edge-game-libs /opt/runtime/wesnoth/bin/wesnoth --version\n"
 (context/'bootstrap.sh').write_text(boot);shutil.copyfile(OLD/'task-r4/environment/aliyun.json',context/'aliyun.json')
 instruction=(source/'instruction.md').read_text()+f'\n工作目录：{work}。只有 {work}/submission 的文件决定分数。使用 python 命令调用离线 numpy/scipy 环境。'
 instruction+='\n这是完整六小时学习运行，每十分钟自动冻结提交并评分，可用 sforge-submit 主动获取评分。成绩取最好有效提交；持续研究并改进，不因一次完成而停止。\n'
 (task/'instruction.md').write_text(instruction)
 profile={'workdir':work,'submission_root':work+'/submission','artifacts':[work+'/submission'],'selection':'valid_then_score','score_direction':'maximize','verifier_timeout_sec':600,'cooldown_sec':120,'grading_workers':1}
 dump(task/'pipeline-profile.json',profile)
 cfg=TaskConfig(metadata={'name':kind+'-cloud-pilot','reward_type':'bounded_continuous','formal_acceptance':False},
  environment=EnvironmentConfig(workdir=work,cpus=4,memory_mb=16384,storage_mb=15360,network_mode='no-network'),
  agent=AgentConfig(user='agent',timeout_sec=28800,network_mode='no-network'),verifier=VerifierConfig(timeout_sec=600,network_mode='no-network'),artifacts=profile['artifacts'])
 (task/'task.toml').write_text(cfg.model_dump_toml());(task/'tests').mkdir()
 (task/'tests/test.sh').write_text('#!/bin/sh\nset -eu\nexec /opt/runtime/venv/bin/python /judge/verifier/judge_entry.py\n')
 inventory={p.relative_to(framework).as_posix():sha(p) for p in framework.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
 tree=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest();dump(framework/'framework-version.json',{'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,'runtime_tree_sha256':tree,'runtime_file_hashes':inventory})
 agent_image=json.loads((OLD/'images-r4.json').read_text())['agent']['image_id'];dump(out/'images.json',{'agent':{'image_id':agent_image},'verifier':{'image_id':image}})
 dump(out/'preparation.json',{'kind':kind,'account':'raymone/1','source_task':str(source),'image_id':image,'base_image_id':base_id,'runtime_tree_sha256':tree,
  'runtime_archive_sha256':sha(archive),'runtime_archive_bytes':archive.stat().st_size,'controls_source':str(ROOT/(kind+'-reuse-controls-'+revision+('/report.json' if kind=='game' else '-extra/report.json'))),
  'official_codex_adapter_unchanged':True,'formal_acceptance':False})
 print('PREPARED',kind,out,flush=True)
if __name__=='__main__':p=argparse.ArgumentParser();p.add_argument('kind',choices=['game','finance']);main(p.parse_args().kind)
