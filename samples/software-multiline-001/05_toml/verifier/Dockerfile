FROM python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7 AS py
FROM rust:1.90.0-bookworm@sha256:3914072ca0c3b8aad871db9169a651ccfce30cf58303e5d6f2db16d1d8a7e58f
COPY --from=py /usr/local /usr/local
ENV LD_LIBRARY_PATH=/usr/local/lib
WORKDIR /home/workspace/toml-string-recovery
COPY vendor.tar.gz /tmp/vendor.tar.gz
RUN tar -xzf /tmp/vendor.tar.gz -C /opt && rm /tmp/vendor.tar.gz
COPY tests /tests
COPY private /private
RUN mkdir -p /logs/verifier && chmod 700 /private /logs/verifier && chmod -R a+rX /opt && chmod -R a+rX /tests && chmod -R a-w /tests /opt/vendor
CMD ["/bin/sh", "/tests/test.sh"]
