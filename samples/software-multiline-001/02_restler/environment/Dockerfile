FROM --platform=linux/amd64 python@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1
COPY wheels /wheels
COPY requirements.lock /requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-index --find-links=/wheels --require-hashes -r /requirements.lock && rm -rf /wheels
WORKDIR /home/workspace/restler_campaign_recovery
COPY starter.tar.gz polaris.tar.gz /tmp/
RUN mkdir -p submission public/polaris && tar -xzf /tmp/starter.tar.gz -C submission --strip-components=1 && tar -xzf /tmp/polaris.tar.gz -C public/polaris --strip-components=1 && rm /tmp/*.tar.gz && groupadd -g 1000 solver && useradd -u 1000 -g 1000 -m solver && chown -R 1000:1000 /home/workspace
USER 1000:1000
CMD ["/bin/bash"]
