FROM --platform=linux/amd64 python@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1
COPY wheels /wheels
COPY requirements.lock /requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-index --find-links=/wheels --require-hashes -r /requirements.lock && rm -rf /wheels
COPY grader.py cases.json test.sh /tests/
RUN chmod 700 /tests && chmod 600 /tests/grader.py /tests/cases.json && chmod 700 /tests/test.sh && mkdir -p /logs/verifier /home/workspace/restler_campaign_recovery && chmod 700 /logs/verifier
WORKDIR /home/workspace/restler_campaign_recovery
# Held component context: no Polaris runtime. Formal entry fails with valid=false.
CMD ["/tests/test.sh"]
