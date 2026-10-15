FROM python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7 AS py
FROM rust:1.99.0-bookworm@sha256:114c7a4425406451c2866b6aafe69fe29b1b298832db1277d411ac73c82d04d6
COPY --from=py /usr/local /usr/local
ENV LD_LIBRARY_PATH=/usr/local/lib
WORKDIR /opt/base
COPY upstream.tar.gz /tmp/source.tar.gz
RUN tar -xzf /tmp/source.tar.gz --strip-components=1 -C . && rm /tmp/source.tar.gz && cargo fetch --locked && chmod -R a+rwX /usr/local/cargo/registry && chmod a+rw /usr/local/cargo/.package-cache
COPY tests /tests
COPY private /private
RUN mkdir -p /logs/verifier && chmod 700 /private /logs/verifier && chmod -R a+rX /tests /opt/base && chmod -R a-w /tests /opt/base
WORKDIR /home/workspace/datafusion-sort-topk
CMD ["/bin/sh", "/tests/test.sh"]
