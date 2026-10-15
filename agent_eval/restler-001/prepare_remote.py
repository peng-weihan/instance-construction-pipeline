"""Prepare our isolated cloud learner + offline Docker judge pilot."""
import hashlib,json,shutil,sys
from pathlib import Path

ROOT=Path('/ws/users/raymone/edgebench/restler-agent-001')
F=ROOT/'framework'
SOURCE=Path('/ws/users/raymone/edgebench/restler-007-smoke-20261014/run-001/restler_resilient_execution')
TASK=ROOT/'task'
WORK='/home/workspace/restler-resilient'
sys.path[:0]=[str(F),str(F/'sdk')]
from harbor.models.task.config import TaskConfig,EnvironmentConfig,AgentConfig,VerifierConfig

def main():
 TASK.mkdir(exist_ok=False)
 shutil.copytree(SOURCE/'public',TASK/'environment/public')
 shutil.copytree(SOURCE/'solution',TASK/'solution')
 shutil.copytree(SOURCE/'environment/verifier',TASK/'verifier')
 shutil.copytree(F/'public-native-audit',TASK/'environment/native-audit')
 (TASK/'tests').mkdir()
 spec={'template_id':'x4inxbpfrrak70x7jqwp','build_id':'00688d58-632e-4e80-a0c5-c5310559b429','cpus':4,'memory_mb':16384,'timeout_seconds':3600,'codex_only':True,'codex_toolchain':'codex'}
 (TASK/'environment/aliyun.json').write_text(json.dumps(spec,indent=2)+'\n')
 instruction=(SOURCE/'instruction.md').read_text().replace('/workspace/repo/restler',WORK+'/submission')
 instruction+='\n工作目录为 '+WORK+'。完整上游工程在 repo/，其中 repo/restler 指向 submission/；请直接修改 submission/ 中的真实引擎。公开接口说明和 probe.py 在工作目录。Python 解释器为 python3。\n运行预算为六小时；每十分钟自动评分，可用 sforge-submit 主动提交并查看反馈。请持续检查、修复并改进实现；不要仅因一次检查通过就停止。评分取本轮有效提交中的最好分数。\n'
 (TASK/'instruction.md').write_text(instruction)
 bootstrap='''set -eu
CTX=/opt/tbsci-bootstrap
WORK=/home/workspace/restler-resilient
mkdir -p "$WORK" /opt/edgebench-native-audit /logs/agent /logs/artifacts
cp -a "$CTX/public/." "$WORK/"
mv "$WORK/repo/restler" "$WORK/submission"
ln -s ../../submission "$WORK/repo/restler"
cp -a "$CTX/native-audit/." /opt/edgebench-native-audit/
chmod -R a+rX,go-w /opt/edgebench-native-audit
chmod 755 /opt/edgebench-native-audit/bin/*
python3 - <<'PY'
import pathlib,site,zipfile
target=site.getsitepackages()[0]
for p in pathlib.Path('/opt/tbsci-bootstrap/wheels').glob('*.whl'):
 with zipfile.ZipFile(p) as z:z.extractall(target)
import requests,applicationinsights,pytest
PY
ln -sf /opt/codex-static/codex-path/rg /usr/local/bin/rg
chown -R agent:agent "$WORK" /logs/agent /logs/artifacts
'''.replace('ln -s ../../submission','ln -s ../submission')
 (TASK/'environment/bootstrap.sh').write_text(bootstrap)
 (TASK/'solution/solve.sh').write_text('#!/bin/sh\nset -eu\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\ncp -a "$HERE/reference/." '+WORK+'/submission/\n')
 cfg=TaskConfig(metadata={'name':'restler-resilient-cloud-pilot','reward_type':'bounded_continuous','source_batch':'007','formal_acceptance':False},environment=EnvironmentConfig(workdir=WORK,cpus=4,memory_mb=16384,storage_mb=15360,network_mode='no-network'),agent=AgentConfig(user='agent',timeout_sec=25200,network_mode='no-network'),verifier=VerifierConfig(timeout_sec=300,network_mode='no-network'),artifacts=[WORK+'/submission'])
 (TASK/'task.toml').write_text(cfg.model_dump_toml())
 profile={'workdir':WORK,'artifacts':[WORK+'/submission'],'selection':'valid_then_score','score_direction':'maximize','verifier_timeout_sec':300,'cooldown_sec':120,'grading_workers':1}
 (TASK/'pipeline-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
 # The actual candidate process becomes UID/GID2000 before starting bwrap.
 runtime=TASK/'verifier/verifier/runtime.py'
 text=runtime.read_text().replace('        os.setsid()','        os.setsid()\n        os.setgroups([]); os.setgid(2000); os.setuid(2000)')
 text=text.replace("    cmd=['bwrap'", "    os.chown(work,2000,2000)\n    cmd=['bwrap'")
 runtime.write_text(text)
 shutil.copyfile(ROOT/'judge_entry.py',TASK/'verifier/verifier/judge_entry.py')
 (TASK/'tests/test.sh').write_text('#!/bin/sh\nset -eu\nunset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD\nexec /opt/runtime/venv/bin/python /judge/verifier/judge_entry.py\n')
 shutil.copyfile(TASK/'tests/test.sh',TASK/'verifier/test.sh')
 docker=TASK/'verifier/Dockerfile'
 docker.write_text(docker.read_text().replace('ENTRYPOINT ["/opt/runtime/venv/bin/python", "/judge/verifier/entry.py"]','COPY test.sh /tests/test.sh\nRUN chmod 700 /judge/private /logs 2>/dev/null || true\nENTRYPOINT ["/bin/sh", "/tests/test.sh"]'))
 # Keep account identity, fixed package, official adapter and source provenance.
 manifest=json.loads((F/'toolchain-manifest.json').read_text())
 (F/'toolchain-manifest.json').write_text(json.dumps({'codex':manifest['codex']},indent=2)+'\n')
 activity=F/'edgebench_harbor/static_native.py'
 activity.write_text(activity.read_text().replace("Path('/tmp/edgebench-1013-account7-activity')", "Path('/ws/users/raymone/edgebench/restler-agent-001/activity')"))
 supervision=F/'edgebench_harbor/official_cloud_supervision.py'
 supervision.write_text(supervision.read_text().replace('from .docker_runtime import DockerScorer','from .restler_scorer import DockerScorer'))
 shutil.copyfile(ROOT/'restler_scorer.py',F/'edgebench_harbor/restler_scorer.py')
 provenance={'source_task':str(SOURCE),'source_manifest_sha256':hashlib.sha256((SOURCE/'files.sha256.json').read_bytes()).hexdigest(),'source_framework':'/ws/users/wcgu/edgebench/dev/task/1013/_framework-account7-cloud-probe-r2','backend':'aliyun learner + independent offline Docker verifier','account':7,'model':'gpt-6.1-sol','reasoning_effort':'high','learning_budget_sec':21600,'interval_sec':600,'formal_acceptance':False,'changes':['canonical submission path','public offline Python dependencies','candidate UID2000','score output wrapper','own scorer transport and activity directory']}
 (ROOT/'preparation.json').write_text(json.dumps(provenance,indent=2)+'\n')
 print('PREPARED',TASK)

if __name__=='__main__':main()
