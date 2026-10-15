"""Validate 50 source-grounded design assessments; do not run any candidate."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MATERIALS = ROOT.parent / 'software-materials-expansion-20261015'
WORKSPACE = ROOT.parents[1]
INPUTS = ['product-cli.json', 'system-state.json', 'restoration.json', 'performance.json']
ROUTES = {'M1': '产品演进', 'M2': '系统能力', 'M3': '性能优化',
          'M4': '实现恢复', 'M5': '行为兼容'}
TIERS = {'A': '优先细化', 'B': '条件保留', 'C': '重设范围', 'D': '当前搁置'}
LEVELS = {'high': '高', 'medium': '中', 'low': '低', 'unclear': '未明'}
FIELDS = ['id', 'tier', 'potential', 'authoring_cost', 'recommended_scope',
          'difficulty_reason', 'shortcut_risk', 'judge_plan', 'residual_milestones',
          'first_probe', 'stop_condition', 'evidence', 'caveat', 'read_scope']


def write_text_chunks(path, value):
    with path.open('w') as handle:
        for start in range(0, len(value), 4000):
            handle.write(value[start:start + 4000])


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def resolve_path(value):
    if value.startswith('research/'):
        return WORKSPACE / value
    return MATERIALS / value


def main():
    source_data = (MATERIALS / 'candidates.json').read_bytes()
    sources = json.loads(source_data)['candidates']
    by_id = {x['id']: x for x in sources}
    records = []
    for name in INPUTS:
        records.extend(json.loads((ROOT / 'drafts' / name).read_text()))
    errors = []
    counts = Counter(x['id'] for x in records)
    if set(counts) != set(by_id) or any(n != 1 for n in counts.values()):
        errors.append('assessment IDs must cover all 50 sources exactly once')
    evidence_count = read_range_count = 0
    for x in records:
        missing = [key for key in FIELDS if key not in x or not x[key]]
        if missing:
            errors.append(f"{x['id']} missing fields: {missing}")
            continue
        if x['tier'] not in TIERS or x['potential'] not in LEVELS or x['authoring_cost'] not in LEVELS:
            errors.append(x['id'] + ' invalid assessment enum')
        if len(x['residual_milestones']) < 2 or len(x['evidence']) < 2:
            errors.append(x['id'] + ' needs two milestones and evidence anchors')
        for ev in x['evidence']:
            path = resolve_path(ev['path'])
            if not path.exists() or not 1 <= int(ev['line']) <= len(path.read_text(errors='replace').splitlines()):
                errors.append(x['id'] + ' invalid evidence location: ' + ev['path'])
            evidence_count += 1
        for span in x['read_scope']:
            if not isinstance(span, dict):
                errors.append(x['id'] + ' unstructured read scope')
                continue
            if 'line_start' in span:
                span['start'] = span.pop('line_start')
                span['end'] = span.pop('line_end')
            path = resolve_path(span['path'])
            if not path.exists() or not 1 <= span['start'] <= span['end'] <= len(path.read_text(errors='replace').splitlines()):
                errors.append(x['id'] + ' invalid read range: ' + str(span))
            read_range_count += 1
        kinds = {span.get('kind') for span in x['read_scope'] if isinstance(span, dict)}
        if 'implementation' not in kinds or not kinds.intersection({'test', 'test_or_spec', 'specification'}):
            errors.append(x['id'] + ' needs implementation and test/spec read ranges')
        source = by_id.get(x['id'])
        if source:
            x.update({key: source[key] for key in ['repo', 'revision', 'route', 'pool_index']})
            x['source_card'] = '../software-materials-expansion-20261015/' + source['card']
            x['initial_screening_priority'] = source['priority']
            x['difficulty_empirically_verified'] = False
            x['scope_constructed'] = False
    if errors:
        print(json.dumps({'errors': errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    records.sort(key=lambda x: x['pool_index'])
    metadata = {'date': '2026-10-15', 'scope': 'All 50 pinned material sources; design potential only',
                'rubric': 'RUBRIC.md', 'source_registry_sha256': hashlib.sha256(source_data).hexdigest(),
                'not_model_evaluation': True, 'new_task_or_runtime_runs': 0}
    write_text_chunks(ROOT / 'assessments.json', json.dumps({**metadata, 'assessments': records}, ensure_ascii=False, indent=2) + '\n')
    fields = ['pool_index', 'id', 'route', 'repo', 'tier', 'potential', 'authoring_cost',
              'recommended_scope', 'difficulty_reason', 'shortcut_risk', 'first_probe',
              'stop_condition', 'caveat', 'source_card']
    with (ROOT / 'assessments.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    lines = ['# 50 项素材的高难题潜力逐项判断', '',
             '全部评估绑定材料登记的固定 commit。分档是作者研究顺序；潜力是合理范围下的难度上限，'
             '二者不能等同。未构造本次推荐范围，未运行求解或性能实验。', '',
             '[总报告](ANALYSIS_REPORT.md) · [完整 JSON](assessments.json) · '
             '[CSV](assessments.csv) · [判据](RUBRIC.md)', '']
    for route, label in ROUTES.items():
        lines += [f'## {route} {label}', '',
                  '| 序号 | 素材 | 分档 / 潜力 / 作者成本 | 推荐范围与难度来源 | 首个淘汰探针 |',
                  '|---|---|---|---|---|']
        for x in records:
            if x['route'] != route:
                continue
            name = f"[{x['repo']}]({x['source_card']})"
            rank = f"{x['tier']} {TIERS[x['tier']]} / {LEVELS[x['potential']]} / {LEVELS[x['authoring_cost']]}"
            reason = x['recommended_scope'] + '；' + x['difficulty_reason']
            lines.append(f"| {x['pool_index']} | {name} | {rank} | {cell(reason)} | {cell(x['first_probe'])} |")
        lines.append('')
    lines += ['JSON 中逐项保留了简单解法风险、独立判据、剩余里程碑、停止条件、'
              '源码证据及实际阅读行区间。C/D 评价针对当前拟题边界，不表示整个项目无法产生高难题。', '']
    write_text_chunks(ROOT / 'ALL_50.md', '\n'.join(lines))
    cross_checks = json.loads((ROOT / 'drafts' / 'root-cross-checks.json').read_text())
    for span in cross_checks:
        path = resolve_path(span['path'])
        if not path.exists() or not 1 <= span['start'] <= span['end'] <= len(path.read_text(errors='replace').splitlines()):
            errors.append('invalid root cross-check range: ' + str(span))
    links = 0
    for path in ROOT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            links += 1
            target_path = path.parent / target.split('#', 1)[0]
            # The result file is emitted after these checks, including on a fresh run.
            if target_path == ROOT / 'validation.json':
                continue
            if not target_path.exists():
                errors.append(path.name + ' broken link: ' + target)
    result = {**metadata, 'all_50_covered_once': True,
              'tier_counts': dict(sorted(Counter(x['tier'] for x in records).items())),
              'route_tier_counts': {route: dict(sorted(Counter(x['tier'] for x in records if x['route'] == route).items())) for route in ROUTES},
              'evidence_anchors_checked': evidence_count, 'read_ranges_checked': read_range_count,
              'additional_root_cross_check_ranges': len(cross_checks),
              'local_links_checked': links, 'errors': errors,
              'validation_ok': not errors,
              'validation_scope': 'coverage, schema and provenance locations; no empirical difficulty claim'}
    (ROOT / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
