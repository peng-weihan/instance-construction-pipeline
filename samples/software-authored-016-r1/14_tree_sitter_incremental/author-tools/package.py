from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parents[1];T=R/'task'
pin=json.loads(Path('/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1/guidance/python-3.12.8-image-pin.json').read_text())
base='python:3.12.8-slim-bookworm@'+pin['digest']
common=f'''FROM {base}
# The timestamped, signed Debian archive is immutable. Build alone uses network.
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \\
 && echo 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20250113T000000Z bookworm main' > /etc/apt/sources.list \\
 && apt-get -o Acquire::Check-Valid-Until=false update \\
 && apt-get install -y --no-install-recommends gcc=4:12.2.0-3 libc6-dev=2.36-9+deb12u9 make=4.3-4.1 patch=2.7.6-7 \\
 && mkdir -p /opt \\
 && dpkg-query -W > /opt/toolchain-installed.txt \\
 && rm -rf /var/lib/apt/lists/*
WORKDIR /home/workspace/tree-sitter
'''
(T/'environment/Dockerfile').write_text(common+'''COPY starter/ /home/workspace/tree-sitter/submission/
COPY grammar/ /home/workspace/tree-sitter/grammar/
COPY public/ /home/workspace/tree-sitter/public/
COPY score-spec.json /home/workspace/tree-sitter/score-spec.json
COPY toolchain-snapshot.json /opt/toolchain-source-lock.json
USER root
CMD ["/bin/bash"]
''')
(T/'verifier/Dockerfile').write_text(common+'''COPY public/ /opt/judge/public/
COPY private/ /opt/judge/private/
COPY probe.c score-spec.json /opt/judge/
COPY toolchain-snapshot.json /opt/toolchain-source-lock.json
COPY tests/ /tests/
RUN chmod -R go-rwx /opt/judge/private /tests \\
 && mkdir -p /logs/verifier /candidate-builds /home/workspace/tree-sitter/submission \\
 && chmod 700 /logs/verifier \\
 && chmod 755 /candidate-builds
USER root
CMD ["/bin/sh", "/tests/test.sh"]
''')
for d in ['environment','verifier']:
 shutil.copy(R/'evidence/toolchain-snapshot.json',T/d/'toolchain-snapshot.json')
 (T/d/'.dockerignore').write_text('**/.git\n**/__pycache__\n**/*.pyc\n')
(T/'task.toml').write_text('''schema_version = "1.4"
artifacts = ["/home/workspace/tree-sitter/submission"]

[task]
name = "edgebench/tree-sitter-edit-recovery"
version = "0.1.0-draft"
description = "Recover linked incremental editing semantics in the native tree-sitter C core"

[metadata]
reward_type = "bounded_continuous"
construction_status = "constructed_unverified"
difficulty_status = "held_for_evidence"
intended_model = "gpt-6.1-sol"
score_spec = "authoring/score-spec.json"
work_build_context = "environment"
verifier_build_context = "verifier"

[agent]
timeout_sec = 21600
network_mode = "no-network"

[environment]
docker_image = "edgebench-tree-sitter-work:author-v1"
workdir = "/home/workspace/tree-sitter"
network_mode = "no-network"
cpus = 2
memory_mb = 4096
storage_mb = 4096
build_timeout_sec = 1200

[verifier]
timeout_sec = 600
network_mode = "no-network"
environment_mode = "separate"

[verifier.environment]
docker_image = "edgebench-tree-sitter-judge:author-v1"
workdir = "/home/workspace/tree-sitter"
network_mode = "no-network"
cpus = 2
memory_mb = 4096
storage_mb = 4096
build_timeout_sec = 1200
''')
(T/'pipeline-profile.json').write_text(json.dumps({'agent_image':'edgebench-tree-sitter-work:author-v1','verifier_image':'edgebench-tree-sitter-judge:author-v1','artifacts':['/home/workspace/tree-sitter/submission'],'selection':'valid_then_score','score_direction':'maximize'},indent=2)+'\n')
(T/'environment/public/smoke.sh').write_text('''#!/bin/sh
set -eu
cd /home/workspace/tree-sitter
mkdir -p submission/build
cc -std=c11 -D_DEFAULT_SOURCE -O1 -Isubmission/lib/include -Isubmission/lib/src public/probe.c submission/lib/src/lib.c grammar/src/parser.c grammar/src/scanner.c -o submission/build/probe
for input in public/*.bin; do
  echo "$input"
  submission/build/probe < "$input" > submission/build/"$(basename "$input")".out
done
''')
(T/'environment/public/smoke.sh').chmod(0o755)
(T/'solution/solve.sh').write_text('''#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "${SUBMISSION_ROOT:-/home/workspace/tree-sitter/submission}"
patch -p1 < "$here/restore.patch"
''');(T/'solution/solve.sh').chmod(0o755)
for n in ['score-spec.json']:
 shutil.copy(T/'authoring'/n,T/n)
shutil.copytree(T/'tests',T/'verifier/tests',dirs_exist_ok=True)
