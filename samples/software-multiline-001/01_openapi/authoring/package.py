from pathlib import Path
import hashlib, json, shutil, tarfile, urllib.request
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Content address an official multi-platform base without executing a container.
u='https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/python:pull'
token=json.load(urllib.request.urlopen(u))['token']
req=urllib.request.Request('https://registry-1.docker.io/v2/library/python/manifests/3.12.13-slim-bookworm',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json'})
with urllib.request.urlopen(req) as response:
 base='python@'+response.headers['Docker-Content-Digest']
(ROOT/'authoring/base-image.json').write_text(json.dumps({'tag':'python:3.12.13-slim-bookworm','immutable':base,'platform':'linux/amd64','manifest_only':True},indent=2))
shutil.copyfile(ROOT/'authoring/sources/upstream.tar.gz',ROOT/'environment/starter.tar.gz')
lock=[]
for p in sorted((ROOT/'environment/wheels').glob('*.whl')):
 name,version=p.name.split('-')[:2]
 lock.append(f'{name}=={version} --hash=sha256:{sha(p)}')
(ROOT/'environment/requirements.lock').write_text('\n'.join(lock)+'\n')
shutil.copytree(ROOT/'environment/wheels',ROOT/'verifier/wheels',dirs_exist_ok=True)
shutil.copyfile(ROOT/'environment/requirements.lock',ROOT/'verifier/requirements.lock')
for p in (ROOT/'tests').glob('*.py'):
 shutil.copyfile(p,ROOT/'verifier'/p.name)
(ROOT/'tests/test.sh').write_text('#!/bin/sh\nset -eu\nunset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD\nexec /opt/venv/bin/python /tests/grader.py\n')
shutil.copyfile(ROOT/'tests/test.sh',ROOT/'verifier/test.sh')
(ROOT/'environment/Dockerfile').write_text(f'''FROM --platform=linux/amd64 {base}
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1
COPY wheels /wheels
COPY requirements.lock /requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-index --find-links=/wheels --require-hashes -r /requirements.lock && rm -rf /wheels
WORKDIR /home/workspace/openapi_composition
COPY starter.tar.gz /tmp/starter.tar.gz
RUN mkdir -p submission && tar -xzf /tmp/starter.tar.gz -C submission --strip-components=1 && rm /tmp/starter.tar.gz && chown -R 1000:1000 /home/workspace && groupadd -g 1000 solver && useradd -u 1000 -g 1000 -m solver
USER 1000:1000
CMD ["/bin/bash"]
''')
(ROOT/'verifier/Dockerfile').write_text(f'''FROM --platform=linux/amd64 {base}
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1
COPY wheels /wheels
COPY requirements.lock /requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-index --find-links=/wheels --require-hashes -r /requirements.lock && rm -rf /wheels
COPY grader.py cases.py test.sh /tests/
RUN chmod 700 /tests && chmod 600 /tests/*.py && chmod 700 /tests/test.sh && mkdir -p /logs/verifier /home/workspace/openapi_composition && chmod 700 /logs/verifier
WORKDIR /home/workspace/openapi_composition
CMD ["/tests/test.sh"]
''')
with tarfile.open(ROOT/'solution/reference.tar.gz','w:gz') as t:
 for p in sorted((ROOT/'solution/reference').rglob('*')):
  if p.is_file() and not any(x in p.parts for x in ['__pycache__','.pytest_cache','.mypy_cache']) and p.suffix not in ['.pyc']:
   t.add(p,arcname=str(p.relative_to(ROOT/'solution/reference')))
manifest={'base_image':base,'source_archive_sha256':sha(ROOT/'environment/starter.tar.gz'), 'reference_archive_sha256':sha(ROOT/'solution/reference.tar.gz'),'wheel_files':{p.name:sha(p) for p in sorted((ROOT/'environment/wheels').glob('*'))},'grader_sha256':sha(ROOT/'tests/grader.py'),'cases_sha256':sha(ROOT/'tests/cases.py'),'contexts':{'work':'environment','judge':'verifier'},'build_commands':['docker build --platform linux/amd64 -t edgebench-openapi-work:pilot -f environment/Dockerfile environment','docker build --platform linux/amd64 -t edgebench-openapi-judge:pilot -f verifier/Dockerfile verifier'],'container_build':'not_run_no_docker_authorization','linux_wheel_install':'not_verified_in_container'}
(ROOT/'authoring/build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
