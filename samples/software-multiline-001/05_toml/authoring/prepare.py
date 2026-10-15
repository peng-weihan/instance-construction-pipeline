#!/usr/bin/env python3
"""Author-time deterministic context assembly; runtime never fetches sources/deps."""
from pathlib import Path
import shutil,tarfile,json,hashlib
r=Path(__file__).resolve().parents[1]
assert (r/'environment/starter.tar.gz').is_file()
with tarfile.open(r/'environment/vendor.tar.gz','w:gz') as tf:
 for p in sorted((r/'authoring/vendor').rglob('*')):
  if p.is_file():tf.add(p,arcname='vendor/'+p.relative_to(r/'authoring/vendor').as_posix())
shutil.copyfile(r/'environment/vendor.tar.gz',r/'verifier/vendor.tar.gz')
for target in [r/'environment/probe',r/'verifier/tests/probe']:
 if target.exists():shutil.rmtree(target)
 shutil.copytree(r/'tests/probe',target)
for p in ['grader.py','test.sh']:shutil.copyfile(r/'tests'/p,r/'verifier/tests'/p)
(r/'environment/cargo-config.toml').write_text('[source.crates-io]\nreplace-with="vendored-sources"\n[source.vendored-sources]\ndirectory="/opt/vendor"\n[net]\noffline=true\n')
images=json.loads((r/'authoring/base-images.json').read_text())
base=f"FROM {images['python']['image']} AS py\nFROM {images['rust']['image']}\nCOPY --from=py /usr/local /usr/local\nENV LD_LIBRARY_PATH=/usr/local/lib\n"
(r/'environment/Dockerfile').write_text(base+'''WORKDIR /home/workspace/toml-string-recovery
COPY starter.tar.gz /tmp/starter.tar.gz
RUN tar -xzf /tmp/starter.tar.gz -C . && rm /tmp/starter.tar.gz
COPY vendor.tar.gz /tmp/vendor.tar.gz
RUN tar -xzf /tmp/vendor.tar.gz -C /opt && rm /tmp/vendor.tar.gz
COPY probe /opt/devprobe
COPY dev-cases.json /opt/dev-cases.json
COPY cargo-config.toml /usr/local/cargo/config.toml
RUN chmod -R a+rX /opt && chmod -R a+rwX /home/workspace/toml-string-recovery /opt/devprobe
CMD ["/bin/bash"]
''')
(r/'verifier/Dockerfile').write_text(base+'''WORKDIR /home/workspace/toml-string-recovery
COPY vendor.tar.gz /tmp/vendor.tar.gz
RUN tar -xzf /tmp/vendor.tar.gz -C /opt && rm /tmp/vendor.tar.gz
COPY tests /tests
COPY private /private
RUN mkdir -p /logs/verifier && chmod 700 /private /logs/verifier && chmod -R a+rX /opt && chmod -R a+rX /tests && chmod -R a-w /tests /opt/vendor
CMD ["/bin/sh", "/tests/test.sh"]
''')
manifest={str(p.relative_to(r)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for base in ['environment','verifier','tests','solution'] for p in sorted((r/base).rglob('*')) if p.is_file()}
(r/'authoring/context-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('assembled work/judge contexts; root tests and copied judge tests byte-identical')
