FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
# The timestamped, signed Debian archive is immutable. Build alone uses network.
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
 && echo 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20250113T000000Z bookworm main' > /etc/apt/sources.list \
 && apt-get -o Acquire::Check-Valid-Until=false update \
 && apt-get install -y --no-install-recommends gcc=4:12.2.0-3 libc6-dev=2.36-9+deb12u9 make=4.3-4.1 patch=2.7.6-7 \
 && mkdir -p /opt \
 && dpkg-query -W > /opt/toolchain-installed.txt \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /home/workspace/tree-sitter
COPY public/ /opt/judge/public/
COPY private/ /opt/judge/private/
COPY probe.c score-spec.json /opt/judge/
COPY toolchain-snapshot.json /opt/toolchain-source-lock.json
COPY tests/ /tests/
RUN chmod -R go-rwx /opt/judge/private /tests \
 && mkdir -p /logs/verifier /candidate-builds /home/workspace/tree-sitter/submission \
 && chmod 700 /logs/verifier \
 && chmod 755 /candidate-builds
USER root
CMD ["/bin/sh", "/tests/test.sh"]
