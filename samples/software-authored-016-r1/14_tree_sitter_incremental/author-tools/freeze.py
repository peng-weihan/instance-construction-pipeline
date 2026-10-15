from pathlib import Path
import hashlib,json,subprocess,shutil
R=Path(__file__).resolve().parents[1];T=R/'task';D=T/'verifier/private';cases=json.loads((D/'cases.json').read_text());failures=[]
for c in cases:
 p=subprocess.run([str(R/'evidence/reference-probe')],input=(D/c['input']).read_bytes(),capture_output=True,timeout=15)
 if p.returncode:raise RuntimeError((c['id'],p.returncode))
 (D/c['expected']).write_bytes(p.stdout)
 sexp=p.stdout.decode().split('@sexp\n')[1].split('\n@end')[0]
 if 'native_expected' in c and sexp!=c['native_expected']:failures.append([c['id'],'native corpus mismatch'])
 for chunk in p.stdout.decode().split('@parsed\n')[1:]:
  if chunk.split('@end')[0]!=chunk.split('@fresh\n')[1].split('@end')[0]:failures.append([c['id'],'incremental vs fresh'])
(R/'evidence/reference-generation.json').write_text(json.dumps({'cases':len(cases),'native_cases':sum('native_expected' in c for c in cases),'failures':failures},indent=2)+'\n')
assert not failures,failures
weights={'initial':.1,'edit':.2,'lifecycle':.1,'parser':.2,'ranges':.15,'unicode':.1,'scanner':.15}
spec={'version':'tree-sitter-recovery-v1','reference_mode':'oracle','weights':weights,'group_tags':{'initial':['initial','sexp'],'edit':['edited','included'],'lifecycle':['copy','handle'],'parser':['parsed','fresh'],'ranges':['changed'],'unicode':['edited','included','parsed','fresh','changed'],'scanner':['parsed','changed']},'membership':{g:[c['id']+'/'+g for c in cases if g in c['groups']] for g in weights},'formula':'sum(weight[g] * passed[g] / frozen_total[g])','bounds':[0,1],'performance':{'enabled':False,'anchors':None},'identities':{'compile_uid':65534,'run_uid':65533},'limits':{'compile_seconds':90,'case_seconds':5,'memory_bytes':1073741824,'output_bytes':8388608,'diagnostic_bytes':8192,'compile_processes':32,'run_processes':1,'source_files':512,'source_bytes':16777216},'case_count':len(cases),'native_count':sum('native_expected' in c for c in cases),'intended_agent_seconds':21600,'verifier_seconds':600,'seed':None,'reward_precision':'17 significant digits; same scalar as structured score','failure_policy':{'candidate':'valid=true; failed checks; normal numerical score','infrastructure':'valid=false; score=null; remove all reward files; exit 2'},'group_policy':'Each named check compares every snapshot in that case for its listed tags. Membership is frozen, no skipped-case denominator changes.'}
for p in [T/'authoring/score-spec.json',T/'verifier/score-spec.json',T/'environment/score-spec.json']:p.write_text(json.dumps(spec,indent=2)+'\n')
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.iterdir() if p.suffix in ['.bin','.out'] or p.name=='cases.json'}
(D/'oracle-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
shutil.copytree(T/'tests',T/'verifier/tests',dirs_exist_ok=True)
# Public smoke: same trusted native API probe, only three disclosed inputs, no hidden expected output.
shutil.copy(R/'author-tools/probe.c',T/'environment/public/probe.c')
