FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
COPY wheelhouse /wheels
COPY requirements-hashed.txt /requirements-hashed.txt
RUN python -m venv /opt/venv && /opt/venv/bin/python -m pip install --no-cache-dir --no-index --find-links=/wheels --require-hashes -r /requirements-hashed.txt
COPY NOTICE /opt/edgebench/NOTICE
COPY tests /tests
COPY private /opt/edgebench/private
RUN useradd --uid 21001 --create-home candidate && chmod 700 /opt/edgebench/private && chmod -R go-rwx /opt/edgebench/private && chmod -R a-w /tests && mkdir -p /logs/verifier /home/workspace/openapi-streaming/submission && chmod 700 /logs/verifier
WORKDIR /home/workspace/openapi-streaming
USER root
CMD ["/tests/test.sh"]
