from pathlib import Path
import hashlib,json,shutil,tarfile
r=Path(__file__).resolve().parents[1]
base='python@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for source,name in [('restler.tar.gz','starter.tar.gz'),('polaris.tar.gz','polaris.tar.gz')]:
 shutil.copyfile(r/'authoring/sources'/source,r/'environment'/name)
lock=[]
for p in sorted((r/'environment/wheels').glob('*.whl')):
 name,version=p.name.split('-')[:2];lock.append(f'{name}=={version} --hash=sha256:{sha(p)}')
(r/'environment/requirements.lock').write_text('\n'.join(lock)+'\n')
shutil.copytree(r/'environment/wheels',r/'verifier/wheels',dirs_exist_ok=True)
shutil.copyfile(r/'environment/requirements.lock',r/'verifier/requirements.lock')
for name in ['grader.py','cases.json','test.sh']:shutil.copyfile(r/'tests'/name,r/'verifier'/name)
(r/'environment/Dockerfile').write_text(f'''FROM --platform=linux/amd64 {base}
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1
COPY wheels /wheels
COPY requirements.lock /requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-index --find-links=/wheels --require-hashes -r /requirements.lock && rm -rf /wheels
WORKDIR /home/workspace/restler_campaign_recovery
COPY starter.tar.gz polaris.tar.gz /tmp/
RUN mkdir -p submission public/polaris && tar -xzf /tmp/starter.tar.gz -C submission --strip-components=1 && tar -xzf /tmp/polaris.tar.gz -C public/polaris --strip-components=1 && rm /tmp/*.tar.gz && groupadd -g 1000 solver && useradd -u 1000 -g 1000 -m solver && chown -R 1000:1000 /home/workspace
USER 1000:1000
CMD ["/bin/bash"]
''')
(r/'verifier/Dockerfile').write_text(f'''FROM --platform=linux/amd64 {base}
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1
COPY wheels /wheels
COPY requirements.lock /requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-index --find-links=/wheels --require-hashes -r /requirements.lock && rm -rf /wheels
COPY grader.py cases.json test.sh /tests/
RUN chmod 700 /tests && chmod 600 /tests/grader.py /tests/cases.json && chmod 700 /tests/test.sh && mkdir -p /logs/verifier /home/workspace/restler_campaign_recovery && chmod 700 /logs/verifier
WORKDIR /home/workspace/restler_campaign_recovery
# Held component context: no Polaris runtime. Formal entry fails with valid=false.
CMD ["/tests/test.sh"]
''')
with tarfile.open(r/'solution/reference-draft.tar.gz','w:gz') as archive:
 for p in sorted((r/'solution/reference-draft').rglob('*')):
  if p.is_file() and not any(x in p.parts for x in ['RestlerResults','__pycache__','.pytest_cache']) and p.suffix!='.pyc':
   archive.add(p,arcname=str(p.relative_to(r/'solution/reference-draft')))
manifest={'base_image':base,'platform':'linux/amd64','closure_status':'native_python_bundled; Polaris_JDK_Gradle_Maven_server_reset_incomplete','sources':{name:sha(r/'authoring/sources'/name) for name in ['restler.tar.gz','polaris.tar.gz']},'source_urls':{'restler.tar.gz':'https://codeload.github.com/microsoft/restler-fuzzer/tar.gz/6d984deedbc54aad957fa3da0c7e9e5df23a2aee','polaris.tar.gz':'https://codeload.github.com/apache/polaris/tar.gz/f838a62e20e7de72946d250883e8d9b1d6d2f68e'},'wheels':{p.name:sha(p) for p in (r/'environment/wheels').glob('*')},'reference_draft_sha256':sha(r/'solution/reference-draft.tar.gz'),'grader_sha256':sha(r/'tests/grader.py'),'contexts':{'work':'environment','judge':'verifier'},'build_commands':['docker build --platform linux/amd64 -f environment/Dockerfile -t edgebench-restler-work:draft environment','docker build --platform linux/amd64 -f verifier/Dockerfile -t edgebench-restler-judge:draft verifier'],'images_built':False,'formal_service_available':False}
(r/'authoring/build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
