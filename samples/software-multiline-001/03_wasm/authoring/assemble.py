#!/usr/bin/env python3
"""Create packaging glue only. Does not generate truth or alter scoring cases."""
import pathlib,json,hashlib,shutil,collections,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
wasm=ROOT.name=='03_wasm';task='wasm-profile' if wasm else 'jq-profile'
def write(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
for d in ['environment/submission','verifier/tests','authoring/controls','solution']:(ROOT/d).mkdir(parents=True,exist_ok=True)
grader=ROOT/'tests/grader.py'
if not wasm:grader.write_text(grader.read_text().replace("TASK='wasm-profile'","TASK='jq-profile'"))
shutil.copy2(grader,ROOT/'verifier/tests/grader.py')
test='''#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD
exec /usr/local/bin/python3 -I /tests/grader.py
'''
write('tests/test.sh',test);write('verifier/tests/test.sh',test)
for p in ['tests/test.sh','verifier/tests/test.sh']:(ROOT/p).chmod(0o755)
raw=(ROOT/'verifier/private/cases.json').read_bytes();write('verifier/private/cases.sha256',hashlib.sha256(raw).hexdigest()+'\n')
if wasm:
    starter='''#!/usr/bin/env python3
import sys,json
for line in sys.stdin:
    request=json.loads(line)
    print(json.dumps({'error':'invalid'}))
'''
    write('environment/submission/runner.py',starter)
    write('solution/solve.sh','''#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${SUBMISSION_DIR:-/home/workspace/wasm-profile/submission}
mkdir -p "$target"
cp "$root/runtime.py" "$target/runner.py"
''')
    ref=(ROOT/'solution/runtime.py').read_text()
    for name,text in [('unsigned_division',ref.replace('aa=s(a) if op in (109,111) else a; bb=s(b) if op in (109,111) else b','aa=a; bb=b')),('no_store',ref.replace("self.memory[addr:addr+size]=(u(value)&((1<<(size*8))-1)).to_bytes(size,'little')","None"))]:write('authoring/near_misses/'+name+'/runner.py',text)
else:
    shutil.copy2(ROOT/'environment/starter.py',ROOT/'environment/submission/runner.py')
    starter=(ROOT/'environment/starter.py').read_text()
    for name,text in [('truncate_stream',starter.replace('for v in evaluate(program,value,env):','for v in evaluate(program,value,env)[:1]:')),('mask_runtime_errors',starter.replace("print('runtime error',file=sys.stderr);sys.exit(5)","sys.exit(0)"))]:write('authoring/near_misses/'+name+'/runner.py',text)
    write('solution/runner.py','''#!/usr/bin/env python3
import os,pathlib,sys
os.execv(str(pathlib.Path(__file__).resolve().with_name('jq')),['jq',*sys.argv[1:]])
''')
    shutil.copy2(ROOT/'authoring/sources/jq-1.7.1-release.tar.gz',ROOT/'solution/jq-1.7.1-release.tar.gz')
    release_hash=hashlib.sha256((ROOT/'solution/jq-1.7.1-release.tar.gz').read_bytes()).hexdigest()
    write('solution/solve.sh',f'''#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${{SUBMISSION_DIR:-/home/workspace/jq-profile/submission}}
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
python3 - "$root/jq-1.7.1-release.tar.gz" <<'PYCODE'
import hashlib,sys
assert hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()=='{release_hash}'
PYCODE
tar -xzf "$root/jq-1.7.1-release.tar.gz" -C "$build"
cd "$build/jq-1.7.1"
./configure --disable-docs --disable-maintainer-mode --disable-shared --enable-static --without-oniguruma
make -j2
mkdir -p "$target"
cp jq "$target/jq"
cp "$root/runner.py" "$target/runner.py"
''')
(ROOT/'solution/solve.sh').chmod(0o755)
write('environment/Dockerfile',f'''FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /home/workspace/{task}
COPY submission/ ./submission/
COPY dev_cases.json ./dev_cases.json
COPY profile.md ./profile.md
RUN chmod -R a+rX /home/workspace/{task}
CMD ["sleep", "infinity"]
''')
write('verifier/Dockerfile',f'''FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
WORKDIR /home/workspace/{task}
COPY tests/ /tests/
COPY private/ /private/
RUN mkdir -p /logs/verifier /home/workspace/{task}/submission && chmod 700 /private /tests /logs/verifier && chmod 600 /private/*
CMD ["/bin/sh", "/tests/test.sh"]
''')
write('task.toml',f'''schema_version = "1.4"
artifacts = ["/home/workspace/{task}/submission/"]
[metadata]
name = "{task}"
reward_type = "bounded_continuous"
score_formula = "mean(group passed / frozen group total), 8 equal groups"
authoring_status = "hold_for_evidence"
[agent]
timeout_sec = 21600
network_mode = "no-network"
[environment]
docker_image = "edgebench-{task}-work:pilot-001"
workdir = "/home/workspace/{task}"
network_mode = "no-network"
cpus = 2
memory_mb = 2048
storage_mb = 4096
[verifier]
timeout_sec = 900
network_mode = "no-network"
environment_mode = "separate"
[verifier.environment]
docker_image = "edgebench-{task}-judge:pilot-001"
workdir = "/home/workspace/{task}"
network_mode = "no-network"
cpus = 2
memory_mb = 2048
storage_mb = 4096
''')
write('pipeline-profile.json',json.dumps({'agent_image':f'edgebench-{task}-work:pilot-001','verifier_image':f'edgebench-{task}-judge:pilot-001','artifacts':[f'/home/workspace/{task}/submission/'],'selection':'valid_then_score','score_direction':'maximize'},indent=2)+'\n')
cases=json.loads(raw);groups=dict(collections.Counter(c['group'] for c in cases))
write('authoring/score-spec.json',json.dumps({'reward_type':'bounded_continuous','reference_mode':'ordinary_oracle','formula':'sum((1/8)*passed[g]/total[g] for g in frozen_groups)','constants':{'group_weight':0.125,'groups':groups,'per_case_wall_sec':3,'per_case_cpu_sec':2,'candidate_memory_bytes':536870912,'candidate_output_file_bytes':1048576},'unrun_and_failed_cases':'remain in fixed denominator; zero credit','raw_metric':'behavior checks passed, separately by semantic group','direction':'maximize','range':[0,1],'pass_rate':'sum(passed)/sum(total), not weighted score','reference_observation':None,'baseline_observation':None,'upper_bound':{'formula_clip':1,'global_semantic_completeness':'not claimed','attainment_evidence':'authoring/controls/reference/score.json when present'},'failure_classification':{'missing_or_wrong_submission':'valid=true, computed partial or 0','broken_dependency_or_fixture':'valid=false, score=null, no reward.txt/reward.json'}},indent=2)+'\n')
print(task,groups)
