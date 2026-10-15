"""Check inventory integrity only; never labels task/runtime/difficulty success."""
import collections, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
 plan=json.loads((ROOT/'plan.json').read_text())
 inventory=json.loads((ROOT/'candidates.json').read_text())
 manifests=json.loads((ROOT/'source-manifests.json').read_text())
 jobs=json.loads((ROOT/'authoring_queue.json').read_text())['jobs']
 ids=[x['id'] for x in plan['candidates']]
 errors=[];files_checked=0;anchors_checked=0;links_checked=0
 if len(ids)!=16 or len(set(ids))!=16:errors.append('expected 16 unique candidates')
 for name,items in [('design',inventory['candidates']),('manifest',manifests['candidates']),('queue',jobs)]:
  if sorted(x['id'] for x in items)!=sorted(ids):errors.append(name+' id mismatch')
 if manifests['failures']:errors.append('source harvest failures remain')
 for c in manifests['candidates']:
  if not re.fullmatch('[0-9a-f]{40}',c['revision']):errors.append(c['id']+' invalid commit')
  for f in c['files_acquired']:
   p=ROOT/'sources'/c['id']/'files'/f['path'];b=p.read_bytes();files_checked+=1
   if len(b)!=f['bytes'] or hashlib.sha256(b).hexdigest()!=f['sha256']:errors.append(str(p)+' digest mismatch')
  t=c['tree_manifest'];b=(ROOT/'sources'/c['id']/t['path']).read_bytes();tree=json.loads(b)
  if hashlib.sha256(b).hexdigest()!=t['sha256'] or tree.get('truncated') or sum(x['type']=='blob' for x in tree['tree'])!=t['blob_count']:errors.append(c['id']+' tree mismatch')
 for c in inventory['candidates']:
  if c['task_package_complete'] or c['six_hour_difficulty_verified'] or c['constructor_model_run_for_this_batch']:errors.append(c['id']+' incorrect readiness')
  for ev in c['evidence']:
   lines=(ROOT/ev['path']).read_text(errors='replace').splitlines();anchors_checked+=1
   if not 1<=ev['line']<=len(lines):errors.append(c['id']+' invalid evidence line')
  if len(c['post_two_hour_hypotheses'])<2 or not c['first_falsification_probe'] or not c['cheap_strong_baseline']:errors.append(c['id']+' missing screening design')
  if not (ROOT/'cards'/(c['id']+'.md')).exists():errors.append(c['id']+' missing card')
 for p in [ROOT/'REPORT.md',ROOT/'README.md',*(ROOT/'cards').glob('*.md')]:
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if '://' in target or target.startswith('#'):continue
   links_checked+=1
   if not (p.parent/target.split('#',1)[0]).exists():errors.append(str(p)+' broken local link '+target)
 if any(x['state']!='candidate_reviewed_not_started' or x['model']!='gpt-6.1-sol' for x in jobs):errors.append('queue state or requested model mismatch')
 result={'inventory_integrity_ok':not errors,'candidate_count':len(ids),'source_files_checked':files_checked,'source_anchors_checked':anchors_checked,'local_links_checked':links_checked,'family_counts':dict(collections.Counter(c['family'] for c in inventory['candidates'])),'errors':errors,'proof_scope':'inventory_only_not_construction_runtime_or_six_hour_difficulty'}
 (ROOT/'inventory-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False));return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
