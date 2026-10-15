#!/usr/bin/env python3
"""Assemble pinned full source and independent contexts without running Docker/network."""
from pathlib import Path
import shutil,json,hashlib
r=Path(__file__).resolve().parents[1];archive=r/'authoring/sources/upstream.tar.gz'
for target in ['environment/upstream.tar.gz','verifier/upstream.tar.gz','solution/reference.tar.gz']:shutil.copyfile(archive,r/target)
for base in ['environment/probe','verifier/tests']:
 t=r/base
 if t.exists():shutil.rmtree(t)
 shutil.copytree(r/'tests',t)
images=json.loads((r/'authoring/base-images.json').read_text());assert images['rust']['image'] and images['python']['image']
base=f"FROM {images['python']['image']} AS py\nFROM {images['rust']['image']}\nCOPY --from=py /usr/local /usr/local\nENV LD_LIBRARY_PATH=/usr/local/lib\n"
(r/'environment/Dockerfile').write_text(base+'''WORKDIR /home/workspace/datafusion-sort-topk/submission
COPY upstream.tar.gz /tmp/source.tar.gz
RUN tar -xzf /tmp/source.tar.gz --strip-components=1 -C . && rm /tmp/source.tar.gz
# Author/build-time network only. Every registry artifact is checksum-locked in Cargo.lock.
RUN cargo fetch --locked
COPY probe /opt/devprobe
COPY build-probe.sh /opt/build-probe.sh
RUN chmod -R a+rX /usr/local/cargo/registry && chmod -R a+rwX /home/workspace/datafusion-sort-topk
WORKDIR /home/workspace/datafusion-sort-topk
CMD ["/bin/bash"]
''')
(r/'verifier/Dockerfile').write_text(base+'''WORKDIR /opt/base
COPY upstream.tar.gz /tmp/source.tar.gz
RUN tar -xzf /tmp/source.tar.gz --strip-components=1 -C . && rm /tmp/source.tar.gz && cargo fetch --locked && chmod -R a+rwX /usr/local/cargo/registry && chmod a+rw /usr/local/cargo/.package-cache
COPY tests /tests
COPY private /private
RUN mkdir -p /logs/verifier && chmod 700 /private /logs/verifier && chmod -R a+rX /tests /opt/base && chmod -R a-w /tests /opt/base
WORKDIR /home/workspace/datafusion-sort-topk
CMD ["/bin/sh", "/tests/test.sh"]
''')
manifest={str(p.relative_to(r)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for base in ['environment','verifier','tests','solution'] for p in sorted((r/base).rglob('*')) if p.is_file()}
(r/'authoring/context-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('source contexts assembled; Docker cargo-fetch/build and timing NOT performed')
