"""Merge 5 x 10 source materials and verify inventory, not task difficulty."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
INPUTS = ['science.json', 'optimization.json', 'formal.json',
          'knowledge-root.json', 'knowledge-extra.json', 'games.json']
CATEGORIES = {'science': '科学问题与机器学习', 'optimization': '组合优化',
              'formal': '形式化数学与定理证明', 'knowledge': '专业知识工作',
              'games': '交互游戏与模拟器'}
PREFIXES = dict(zip(CATEGORIES, ['s', 'o', 'f', 'k', 'g']))
PRIORITY = {'scope_probe': '先验证范围', 'hold_baseline': '待强基线',
            'hold_reference': '待健康参考', 'hold_data': '待新数据/情景',
            'hold_license': '待许可核实'}
PREVIOUS = ['research/source_candidate_registry.v1.json',
            'research/source_candidate_registry.v2.json',
            'research/remaining-three-2026-10-15/single-cell-source-manifest.json',
            'research/software-materials-expansion-20261015/candidates.json',
            'research/software-candidates-016-20261015/candidates.json',
            'research/swe-pipeline-v2-20261015/source-registry.json',
            'runs/swe-route-authoring-005-20261015-r3/source-registry.json',
            'runs/swe-route-authoring-010-20261015-r4/source-registry.json']
KNOWN_EXCLUSIONS = ['modflow-org/modflow6-examples', 'fatiando/harmonica',
                    'snap-stanford/ogb', 'esicup/datasets',
                    'remydegenne/brownian-motion', 'wesnoth/wesnoth',
                    'santiontanon/microrts']
FIELDS = ['id', 'category', 'name', 'repo', 'revision', 'source_manifest',
          'source_unit', 'title', 'proposed_task', 'deliverable',
          'difficulty_sources', 'baseline', 'first_probe', 'stop_condition',
          'grader_plan', 'generation_and_split', 'novelty_and_overlap',
          'offline_and_compute', 'license_observation', 'evidence',
          'read_scope', 'potential', 'priority', 'card']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_chunks(path, value):
    with path.open('w') as handle:
        for start in range(0, len(value), 4000):
            handle.write(value[start:start + 4000])


def repo_names(obj, key=''):
    names = set()
    if isinstance(obj, dict):
        for k, value in obj.items():
            names.update(repo_names(value, k))
    elif isinstance(obj, list):
        for value in obj:
            names.update(repo_names(value, key))
    elif isinstance(obj, str):
        names.update('/'.join(x).lower().removesuffix('.git') for x in
                     re.findall(r'https://github\.com/([\w.-]+)/([\w.-]+)', obj))
        if key in ('repo', 'repository') and re.fullmatch(r'[\w.-]+/[\w.-]+', obj):
            names.add(obj.lower().removesuffix('.git'))
    return names


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def main():
    items = []
    for name in INPUTS:
        items.extend(json.loads((ROOT / 'drafts' / name).read_text()))
    order = {category: n for n, category in enumerate(CATEGORIES)}
    items.sort(key=lambda x: (order[x['category']], x['id']))
    errors = []
    counts = Counter(x['category'] for x in items)
    if len(items) != 50 or counts != Counter({c: 10 for c in CATEGORIES}):
        errors.append('expected five categories with exactly ten materials each')
    ids = [x['id'] for x in items]
    repos = [x['repo'].lower() for x in items]
    if len(set(ids)) != 50 or len(set(repos)) != 50:
        errors.append('duplicate ID or primary repository')
    for category, prefix in PREFIXES.items():
        nums = sorted(int(x['id'][1:3]) for x in items if x['category'] == category)
        if nums != list(range(1, 11)):
            errors.append(category + ' expected 01 through 10')
    prior = set(KNOWN_EXCLUSIONS)
    previous_checks = []
    for name in PREVIOUS:
        path = WORKSPACE / name
        if not path.exists():
            errors.append('missing prior registry: ' + name)
            continue
        data = path.read_bytes()
        prior.update(repo_names(json.loads(data)))
        previous_checks.append({'path': name, 'sha256': sha(data)})
    overlaps = sorted(set(repos) & prior)
    if overlaps:
        errors.append('previous primary repository overlap: ' + str(overlaps))
    manifests = []
    files_checked = bytes_checked = anchors = read_ranges = 0
    for index, x in enumerate(items, 1):
        x['pool_index'] = index
        missing = [key for key in FIELDS if not x.get(key)]
        if missing:
            errors.append(x['id'] + ' missing: ' + str(missing))
            continue
        if x['priority'] not in PRIORITY or x['potential'] not in ('high', 'medium', 'unclear'):
            errors.append(x['id'] + ' invalid classification')
        for flag in ('task_constructed', 'runtime_verified', 'difficulty_verified'):
            if x.get(flag) is not False:
                errors.append(x['id'] + ' must explicitly leave ' + flag + ' false')
        if len(x['difficulty_sources']) < 2 or len(x['evidence']) < 2 or len(x['read_scope']) < 2:
            errors.append(x['id'] + ' insufficient design or evidence')
        source = (ROOT / x['source_manifest']).parent
        m = json.loads((source / 'manifest.json').read_text())
        if not re.fullmatch(r'[0-9a-f]{40}', x['revision']) or m['revision'] != x['revision']:
            errors.append(x['id'] + ' revision mismatch')
        if m['repo'].lower() != x['repo'].lower():
            errors.append(x['id'] + ' source repository mismatch')
        tree_data = (source / m['tree_manifest']['path']).read_bytes()
        if sha(tree_data) != m['tree_manifest']['sha256'] or json.loads(tree_data).get('truncated'):
            errors.append(x['id'] + ' invalid file-tree provenance')
        if m.get('fetch_errors') or m.get('missing_requested_paths'):
            errors.append(x['id'] + ' acquisition errors')
        for f in m['files_acquired']:
            data = (source / 'files' / f['path']).read_bytes()
            files_checked += 1
            bytes_checked += len(data)
            if len(data) != f['bytes'] or sha(data) != f['sha256']:
                errors.append(x['id'] + ' invalid file digest: ' + f['path'])
        for ev in x['evidence']:
            path = ROOT / ev['path']
            if not path.exists() or not 1 <= ev['line'] <= len(path.read_text(errors='replace').splitlines()):
                errors.append(x['id'] + ' invalid anchor: ' + str(ev))
            expected = f"https://github.com/{x['repo']}/blob/{x['revision']}/".lower()
            if not ev['url'].lower().startswith(expected):
                errors.append(x['id'] + ' unpinned or mismatched evidence URL')
            anchors += 1
        for span in x['read_scope']:
            path = ROOT / span['path']
            if not path.exists() or not 1 <= span['start'] <= span['end'] <= len(path.read_text(errors='replace').splitlines()):
                errors.append(x['id'] + ' invalid read range: ' + str(span))
            read_ranges += 1
        card = ROOT / x['card']
        if not card.exists() or not 20 <= len(card.read_text().splitlines()) <= 35:
            errors.append(x['id'] + ' missing card or unexpected card length')
        manifests.append({'id': x['id'], **m})
    cross = json.loads((ROOT / 'drafts' / 'root-cross-checks.json').read_text())
    for span in cross:
        path = ROOT / span['path']
        if not path.exists() or not 1 <= span['start'] <= span['end'] <= len(path.read_text(errors='replace').splitlines()):
            errors.append('invalid root cross-check: ' + str(span))
    if errors:
        print(json.dumps({'errors': errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    meta = {'schema_version': 1, 'date': '2026-10-15',
            'scope': '50 new non-software material sources; task scopes are proposals',
            'task_constructed': False, 'runtime_verified': False, 'difficulty_verified': False}
    write_chunks(ROOT / 'candidates.json', json.dumps({**meta, 'candidates': items}, ensure_ascii=False, indent=2) + '\n')
    write_chunks(ROOT / 'source-manifests.json', json.dumps({'sources': manifests}, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'previous-source-check.json').write_text(json.dumps({'checked_files': previous_checks,
        'known_primary_repositories': sorted(prior), 'explicit_exclusions': KNOWN_EXCLUSIONS,
        'new_repositories': repos, 'overlap': overlaps,
        'scope_note': 'Primary repository uniqueness only; original hidden assets and semantic lineage not cleared.'}, ensure_ascii=False, indent=2) + '\n')
    fields = ['pool_index', 'id', 'category', 'name', 'repo', 'revision', 'title', 'source_unit',
              'priority', 'potential', 'proposed_task', 'deliverable', 'baseline', 'first_probe',
              'stop_condition', 'grader_plan', 'generation_and_split', 'novelty_and_overlap',
              'offline_and_compute', 'license_observation', 'card', 'source_manifest']
    with (ROOT / 'candidates.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(items)
    lines = ['# 非软工素材总目录：五类各10项', '',
             '共50个独立主来源，均固定commit并保存定向材料。每项是可构题研究方向；'
             '不是已完成题包、已获得完整数据或已验证高难。', '',
             '[总报告](ANALYSIS_REPORT.md) · [CSV](candidates.csv) · [完整JSON](candidates.json) · '
             '[来源清单](source-manifests.json) · [完整性检查](inventory-check.json)', '']
    (ROOT / 'categories').mkdir(exist_ok=True)
    for category, label in CATEGORIES.items():
        section = [f'## {label}：10项', '',
                   '| 序号 / ID | 素材与卡片 | 可构造的任务 | 下一步 |',
                   '|---|---|---|---|']
        for x in items:
            if x['category'] != category:
                continue
            section.append(f"| {x['pool_index']} / {x['id']} | [{x['name']}]({x['card']}) | {cell(x['title'])} | {PRIORITY[x['priority']]} |")
        section.append('')
        lines.extend(section)
        standalone = ['# ' + label + '：10份素材', '',
                      '[返回总目录](../CATALOG_50.md) · [总报告](../ANALYSIS_REPORT.md)', '',
                      *[line.replace('](cards/', '](../cards/') for line in section[2:]]]
        write_chunks(ROOT / 'categories' / (category + '.md'), '\n'.join(standalone))
    write_chunks(ROOT / 'CATALOG_50.md', '\n'.join(lines))
    links = 0
    for path in [*ROOT.glob('*.md'), *(ROOT / 'cards').glob('*.md'), *(ROOT / 'categories').glob('*.md')]:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('http://', 'https://', '#')):
                continue
            links += 1
            target_path = path.parent / target.split('#', 1)[0]
            if target_path == ROOT / 'inventory-check.json':
                continue
            if not target_path.exists():
                errors.append(str(path.relative_to(ROOT)) + ' broken link: ' + target)
    result = {**meta, 'inventory_integrity_ok': not errors, 'candidate_count': len(items),
              'unique_primary_repositories': len(set(repos)), 'category_counts': dict(counts),
              'priority_counts': dict(Counter(x['priority'] for x in items)),
              'source_files_checked': files_checked, 'source_excerpt_bytes': bytes_checked,
              'evidence_anchors_checked': anchors, 'read_ranges_checked': read_ranges,
              'root_cross_check_ranges': len(cross), 'local_links_checked': links,
              'previous_repository_overlaps': overlaps, 'errors': errors,
              'proof_scope': 'inventory integrity and evidence locations; no runtime, full-data or difficulty acceptance',
              'new_model_runs': 0, 'new_candidate_executions': 0}
    (ROOT / 'inventory-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
