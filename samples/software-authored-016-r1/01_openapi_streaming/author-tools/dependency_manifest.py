from pathlib import Path
from email.parser import BytesParser
import json,zipfile,hashlib,urllib.request,concurrent.futures
from packaging.utils import parse_wheel_filename
r=Path(__file__).resolve().parents[1]
packages={}
for p in (r/'downloads/wheelhouse').glob('*.whl'):
 name,version,_,_=parse_wheel_filename(p.name);packages[(str(name),str(version))]=None

def fetch(item):
 name,version=item
 if name=='openapi-python-client':return item,None
 try:
  with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=20) as response:data=json.load(response)
  return item,data
 except Exception as exc:return item,{'fetch_error':type(exc).__name__}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for key,value in pool.map(fetch,packages):packages[key]=value
records=[]
for p in sorted((r/'downloads/wheelhouse').glob('*.whl')):
 name,version,_,_=parse_wheel_filename(p.name)
 with zipfile.ZipFile(p) as z:
  metadata=BytesParser().parsebytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
  licenses=[n for n in z.namelist() if 'license' in n.lower() or 'copying' in n.lower()]
 digest=hashlib.sha256(p.read_bytes()).hexdigest();data=packages[(str(name),str(version))]
 record={'file':p.name,'name':str(name),'version':str(version),'sha256':digest,'bytes':p.stat().st_size,'license_expression':metadata.get('License-Expression'),'license_declared':metadata.get('License'),'license_classifiers':[c for c in metadata.get_all('Classifier',[]) if c.startswith('License')],'embedded_license_files':licenses}
 if str(name)=='openapi-python-client':record.update(origin='built from complete material-src at fixed source revision',source_revision='0a283fe21eeaa23046faf622d4ff4b2c826d2edb',build_tool_lock='../../downloads/wheel-build.lock')
 elif data and 'urls' in data:
  matches=[u for u in data['urls'] if u['filename']==p.name]
  if matches:
   record.update(url=matches[0]['url'],pypi_sha256=matches[0]['digests']['sha256'],pypi_hash_matches=matches[0]['digests']['sha256']==digest)
   assert record['pypi_hash_matches']
  else:record['origin_status']='filename not located in fetched release metadata'
 else:record['origin_status']=data
 records.append(record)
(r/'task/authoring/dependency-manifest.json').write_text(json.dumps({'runtime':'CPython 3.12','wheels':records,'metadata_source':'PyPI version JSON; exact-source project wheel built locally','arm_runtime_verified':False},indent=2)+'\n')
print('dependency wheels:',len(records),'PyPI hash verified:',sum(x.get('pypi_hash_matches',False) for x in records))
