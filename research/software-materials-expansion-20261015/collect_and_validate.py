"""Merge material research and validate provenance, not task acceptance."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
INPUTS = ['roadmap-candidates.json', 'system-candidates.json',
          'performance-candidates.json', 'remaining-candidates.json',
          'expansion-a.json', 'expansion-b.json', 'expansion-c.json', 'expansion-d.json']
PREVIOUS = ['research/software-candidates-016-20261015/candidates.json',
            'research/swe-pipeline-v2-20261015/source-registry.json',
            'runs/swe-route-authoring-005-20261015-r3/source-registry.json',
            'research/source_candidate_registry.v1.json',
            'research/source_candidate_registry.v2.json']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def previous_repos(obj):
    result = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in ('repo', 'repository') and isinstance(value, str):
                match = re.fullmatch(r'(?:https://github.com/)?([\w.-]+/[\w.-]+?)(?:\.git)?/?', value)
                if match:
                    result.add(match[1].lower())
            else:
                result.update(previous_repos(value))
    elif isinstance(obj, list):
        for value in obj:
            result.update(previous_repos(value))
    return result


def main():
    prior = set()
    previous_sources = []
    for name in PREVIOUS:
        path = WORKSPACE / name
        data = path.read_bytes()
        prior.update(previous_repos(json.loads(data)))
        previous_sources.append({'path': name, 'sha256': sha(data)})
    candidates = []
    for name in INPUTS:
        obj = json.loads((ROOT / name).read_text())
        for entry in obj if isinstance(obj, list) else obj['candidates']:
            item = dict(entry)
            item['route_original'] = item['route']
            item['route'] = item['route'].split('_')[0]
            if item['priority'] == 'scope_probe':
                item['priority_original'] = item['priority']
                item['priority'] = 'build_scope_probe'
            item['card'] = item.get('card', f"cards/{item['id']}.md")
            item['source_manifest'] = item.get('source_manifest', f"sources/{item['id']}/manifest.json")
            for flag in ('task_constructed', 'runtime_verified', 'six_hour_difficulty_verified'):
                if item.get(flag) or item.get('flags', {}).get(flag):
                    raise ValueError(f"unexpected acceptance flag in {item['id']}")
                item[flag] = False
            for evidence in item['evidence']:
                if not evidence['path'].startswith('sources/'):
                    evidence['upstream_path'] = evidence['path']
                    source_parent = str(Path(item['source_manifest']).parent)
                    evidence['path'] = f"{source_parent}/files/{evidence['path']}"
            item['next_action'] = 'scope_probe_proposed_not_started' if item['priority'] == 'build_scope_probe' else 'screening_probe_proposed_not_started'
            candidates.append(item)
    candidates.sort(key=lambda x:x['id'])
    for index, item in enumerate(candidates, 1):
        item['pool_index'] = index
    errors = []
    ids = [x['id'] for x in candidates]
    repos = [x['repo'].lower() for x in candidates]
    expected = list(range(28,78))
    if [int(x.split('_')[0]) for x in ids] != expected:
        errors.append('candidate ID set mismatch')
    if len(set(ids)) != 50 or len(set(repos)) != 50:
        errors.append('duplicate candidate or repository')
    overlaps = sorted(set(repos) & prior)
    if overlaps:
        errors.append('previous primary repository overlap: '+str(overlaps))
    counts = Counter(x['route'] for x in candidates)
    if dict(counts) != {f'M{i}':10 for i in range(1,6)}:
        errors.append('expected ten sources per construction route')
    manifests = []
    file_count = byte_count = anchors = 0
    for item in candidates:
        source = (ROOT / item['source_manifest']).parent
        manifest = json.loads((source / 'manifest.json').read_text())
        if manifest['revision'] != item['revision'] or not re.fullmatch('[0-9a-f]{40}',item['revision']):
            errors.append(item['id']+' revision mismatch')
        tree_data = (source / manifest['tree_manifest']['path']).read_bytes()
        tree = json.loads(tree_data)
        if sha(tree_data) != manifest['tree_manifest']['sha256'] or tree.get('truncated'):
            errors.append(item['id']+' tree mismatch or truncation')
        if manifest.get('fetch_errors') or manifest.get('missing_requested_paths'):
            errors.append(item['id']+' acquisition gaps')
        for evidence_file in manifest['files_acquired']:
            data = (source / 'files' / evidence_file['path']).read_bytes()
            file_count += 1
            byte_count += len(data)
            if len(data) != evidence_file['bytes'] or sha(data) != evidence_file['sha256']:
                errors.append(item['id']+' file digest mismatch '+evidence_file['path'])
        for ev in item['evidence']:
            path = ROOT / ev['path']
            if not path.exists() or not 1 <= int(ev['line']) <= len(path.read_text(errors='replace').splitlines()):
                errors.append(item['id']+' bad evidence anchor '+str(ev))
            anchors += 1
        if not (ROOT / item['card']).exists():
            errors.append(item['id']+' missing card')
        if len(item['remaining_work_hypotheses']) < 2 or not item['first_probe'] or not item['cheap_baseline']:
            errors.append(item['id']+' insufficient screening design')
        manifests.append({'id':item['id'], **manifest})
    link_count = 0
    for path in [*ROOT.glob('*.md'), *(ROOT/'cards').glob('*.md')]:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if target.startswith(('http://','https://','#')):
                continue
            link_count += 1
            if not (path.parent / target.split('#',1)[0]).exists():
                errors.append(str(path.relative_to(ROOT))+' broken link '+target)
    result = {'inventory_integrity_ok':not errors, 'candidate_count':len(ids),
        'unique_primary_repositories':len(set(repos)), 'route_counts':dict(counts),
        'source_files_checked':file_count, 'source_excerpt_bytes':byte_count,
        'source_anchors_checked':anchors, 'local_links_checked':link_count,
        'previous_repository_overlaps':overlaps, 'errors':errors,
        'proof_scope':'source inventory and excerpt integrity only',
        'new_task_packages':0, 'new_runtime_experiments':0, 'new_model_runs':0,
        'six_hour_difficulty_verified':False}
    (ROOT/'candidates.json').write_text(json.dumps({'schema_version':1,
        'scope':'new primary material sources; proposed task scopes, not authored tasks',
        'candidates':candidates},ensure_ascii=False,indent=2)+'\n')
    (ROOT/'source-manifests.json').write_text(json.dumps({'sources':manifests},ensure_ascii=False,indent=2)+'\n')
    (ROOT/'previous-source-check.json').write_text(json.dumps({'checked_files':previous_sources,
        'known_primary_repositories':sorted(prior),'new_repositories':repos,
        'overlap':overlaps},ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'candidates.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        fields=['pool_index','id','route','repo','revision','title','priority','scope','cheap_baseline',
                'first_probe','license_observation','card','source_manifest']
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(candidates)
    (ROOT/'inventory-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
