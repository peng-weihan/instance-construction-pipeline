from pathlib import Path
import shutil,difflib,json
r=Path(__file__).resolve().parents[1];ref=r/'task/solution/reference';start=r/'task/environment/submission'
for name in ['no_auth_override','eager']:
 d=r/'controls'/name
 if d.exists():shutil.rmtree(d)
 shutil.copytree(ref,d)
 if name=='no_auth_override':
  p=d/'openapi_python_client/templates/endpoint_module.py.jinja';s=p.read_text();s=s.replace('    request.headers.pop(getattr(client, "auth_header_name", "Authorization"), None)','    # near-miss: leave inherited credential headers in place').replace('    request.headers.pop("Authorization", None)','');p.write_text(s)
 else:
  p=d/'openapi_python_client/templates/streaming_endpoint.py.jinja';s=p.read_text().replace('        _validate_stream(response)','        response.read()\n        _validate_stream(response)',1)
  idx=s.index('async def asyncio_stream')
  s=s[:idx]+s[idx:].replace('        _validate_stream(response)','        await response.aread()\n        _validate_stream(response)',1);p.write_text(s)
patch=[];changes=[]
for p in sorted(ref.rglob('*')):
 if not p.is_file() or any(x in p.parts for x in ['__pycache__','.ruff_cache','.pytest_cache','.mypy_cache']):continue
 rel=p.relative_to(ref);before=start/rel
 if before.exists() and before.read_bytes()==p.read_bytes():continue
 changes.append(str(rel));a=before.read_text().splitlines(keepends=True) if before.exists() else []
 patch.extend(difflib.unified_diff(a,p.read_text().splitlines(keepends=True),fromfile='a/'+str(rel) if before.exists() else '/dev/null',tofile='b/'+str(rel)))
(r/'task/solution/reference.patch').write_text(''.join(patch))
shutil.copyfile(r/'task/solution/reference.patch',r/'task/verifier/private/reference.patch')
(r/'evidence/reference-changed-files.json').write_text(json.dumps(changes,indent=2)+'\n')
