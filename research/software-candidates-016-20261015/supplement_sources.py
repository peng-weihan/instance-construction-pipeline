from concurrent.futures import ThreadPoolExecutor
import json, hashlib
from pathlib import Path
from harvest_sources import fetch, ROOT

def process(c):
 base=ROOT/'sources'/c['id']; rev=c['revision']
 treepath=base/'git-tree.json'
 try:
  content=treepath.read_bytes() if treepath.exists() else fetch(f"https://api.github.com/repos/{c['repo']}/git/trees/{rev}?recursive=1")
  data=json.loads(content); treepath.write_bytes(content)
  assert not data.get('truncated'), 'truncated tree'
 except Exception as e:
  return {'id':c['id'],'tree_error':str(e)}
 paths=[t['path'] for t in data['tree'] if t['type']=='blob']
 targets={
 '01_openapi_streaming':['openapi_python_client/templates/endpoint_module.py.jinja'],
 '02_restler_recovery':['restler/utils/saver.py'],
 '05_uv_resolution':['crates/uv/tests/lock/lock.rs','crates/uv/tests/lock_scenarios/lock_conflict.rs','crates/uv-resolver/src/resolver/mod.rs'],
 '06_wasm_validation':['document/core/LICENSE','test/LICENSE','interpreter/LICENSE','interpreter/valid/valid.ml'],
 '07_arrow_ipc':['format/Schema.fbs'],
 '09_valkey_transactions':['tests/unit/multi.tcl'],
 '11_rocksdb_compaction':['LICENSE.Apache'],
 '12_croaring_kernels':['tests/mixed_container_unit.c','tests/robust_deserialization_unit.c'],
 '13_toml_lossless':['crates/toml_edit/tests/testsuite/edit.rs'],
 '14_tree_sitter_incremental':['crates/cli/src/tests/parser_test.rs','crates/cli/src/tests/helpers/edits.rs'],
 '16_libarchive_cli':['tar/test/test_option_C_upper.c','tar/test/test_option_O.c','tar/test/test_basic.c']
 }.get(c['id'],[])
 got=[]
 for p in targets:
  if p not in paths: continue
  dest=base/'files'/p
  body=dest.read_bytes() if dest.exists() else fetch(f"https://raw.githubusercontent.com/{c['repo']}/{rev}/{p}")
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
  entry={'path':p,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'url':f"https://github.com/{c['repo']}/blob/{rev}/{p}"}
  if not any(x['path']==p for x in c['files_acquired']): c['files_acquired'].append(entry)
  if p in c['missing_paths']: c['missing_paths'].remove(p)
  got.append(p)
 c['tree_manifest']={'path':'git-tree.json','sha256':hashlib.sha256(content).hexdigest(),'blob_count':len(paths),'truncated':False}
 (base/'manifest.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
 return {'id':c['id'],'blob_count':len(paths),'added':got,'interesting_paths':[p for p in paths if any(q in p for q in ['test_option_C','lock/mod.rs','toplevel.c','transactions.tcl','saver.py'])][:15]}
if __name__=='__main__':
 manifest=json.loads((ROOT/'source-manifests.json').read_text())
 with ThreadPoolExecutor(max_workers=4) as pool:
  for result in pool.map(process,manifest['candidates']): print(json.dumps(result),flush=True)
 manifest['candidates']=[json.loads((ROOT/'sources'/c['id']/'manifest.json').read_text()) for c in manifest['candidates']]
 (ROOT/'source-manifests.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
