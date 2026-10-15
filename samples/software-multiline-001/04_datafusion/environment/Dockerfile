FROM python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7 AS py
FROM rust:1.99.0-bookworm@sha256:114c7a4425406451c2866b6aafe69fe29b1b298832db1277d411ac73c82d04d6
COPY --from=py /usr/local /usr/local
ENV LD_LIBRARY_PATH=/usr/local/lib
WORKDIR /home/workspace/datafusion-sort-topk/submission
COPY upstream.tar.gz /tmp/source.tar.gz
RUN tar -xzf /tmp/source.tar.gz --strip-components=1 -C . && rm /tmp/source.tar.gz
# Author/build-time network only. Every registry artifact is checksum-locked in Cargo.lock.
RUN cargo fetch --locked
COPY probe /opt/devprobe
COPY build-probe.sh /opt/build-probe.sh
RUN chmod -R a+rX /usr/local/cargo/registry && chmod -R a+rwX /home/workspace/datafusion-sort-topk
WORKDIR /home/workspace/datafusion-sort-topk
CMD ["/bin/bash"]
