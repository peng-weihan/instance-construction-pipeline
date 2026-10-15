from pathlib import Path
import json,hashlib,tarfile,shlex
R=Path(__file__).resolve().parents[1];T=R/'task';A=T/'authoring'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
required=['instruction.md','task.toml','environment/Dockerfile','verifier/Dockerfile','tests/test.sh','tests/grader.py','solution/solve.sh','solution/restore.patch','authoring/provenance.json','authoring/score-spec.json','authoring/build-manifest.json','pipeline-profile.json','AUTHORING_REPORT.json','MATERIALS.md','DIFFICULTY.md']
assert all((T/p).is_file() for p in required)
upstream_jsonc='environment/starter/lib/binding_web/tsconfig.json'
for p in T.rglob('*.json'):
 if str(p.relative_to(T))==upstream_jsonc:
  assert p.read_bytes()==(R/'material-src/tree-sitter/lib/binding_web/tsconfig.json').read_bytes()
  continue
 json.loads(p.read_text())
spec=json.loads((A/'score-spec.json').read_text());assert sum(spec['weights'].values())==1 and not spec['performance']['enabled']
for p in [T/'score-spec.json',T/'environment/score-spec.json',T/'verifier/score-spec.json']:assert p.read_bytes()==(A/'score-spec.json').read_bytes()
for n in ['test.sh','grader.py']:assert (T/'tests'/n).read_bytes()==(T/'verifier/tests'/n).read_bytes()
assert len([n for group in spec['membership'].values() for n in group])==198
copy_sources={}
for d in ['environment','verifier']:
 sources=[]
 for line in (T/d/'Dockerfile').read_text().splitlines():
  if line.startswith('COPY '):
   args=shlex.split(line)[1:]
   for src in args[:-1]:
    assert not src.startswith('/') and '..' not in Path(src).parts
    assert (T/d/src).exists(),(d,src)
    sources.append(src)
 copy_sources[d]=sources
assert 'private/' not in copy_sources['environment']
for p in (T/'environment').rglob('*'):
 assert p.name not in ['restore.patch','reference.tar','oracle-hashes.json']
with tarfile.open(T/'verifier/private/reference.tar') as tf:
 assert all(not m.name.startswith('/') and '..' not in Path(m.name).parts for m in tf.getmembers())
for p in (A/'evidence').glob('*/score.json'):
 r=json.loads(p.read_text());reward=p.parent/'reward.txt'
 if r['valid']:assert reward.is_file() and float(reward.read_text())==r['score'] and 0<=r['score']<=1
 else:assert r['score'] is None and not reward.exists()
r={'passed':True,'required_files':len(required),'all_authored_json_parsed':True,'preserved_upstream_jsonc':upstream_jsonc,'score_spec_copies_identical':True,'frozen_named_checks':198,'work_private_answer_absent':True,'self_contained_COPY_sources':copy_sources,'root_judge_tests_identical':True,'reward_structured_score_consistent':True,'safe_reference_archive_paths':True,'scope':'static closure/integrity, not container/runtime/difficulty acceptance'}
(R/'evidence/integrity.json').write_text(json.dumps(r,indent=2)+'\n');(A/'evidence/integrity.json').write_text(json.dumps(r,indent=2)+'\n')
# Append result to status without inflating verified stages.
for p in [T/'AUTHORING_REPORT.json',R/'AUTHOR_RESULT.json']:
 x=json.loads(p.read_text());x['static_integrity_evidence']='authoring/evidence/integrity.json' if p.parent==T else 'task/authoring/evidence/integrity.json';p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
files={str(p.relative_to(T)):sha(p) for p in sorted(T.rglob('*')) if p.is_file() and p.name!='file-manifest.json' and '__pycache__' not in p.parts}
(A/'file-manifest.json').write_text(json.dumps(files,indent=2)+'\n')
assert all(sha(T/n)==h for n,h in files.items());print('static integrity PASS; package files',len(files))
