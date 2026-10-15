"""Evidence-led SWE authoring plans and fail-closed static admission.

This module never calls a model and never certifies six-hour difficulty.
"""
import argparse
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / 'task_factory/swe_routes.json'
ORIGINALS = ROOT / 'research/software-engineering-2026-10-15/software-task-map.csv'


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value): raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def harvest(registry, output):
    """Collect primary-source leads, not validated task candidates or full checkouts."""
    if output.exists(): raise FileExistsError(output)
    output.mkdir(parents=True)
    results = []
    for source in read(registry)['jobs']:
        directory = output / source['id']; directory.mkdir()
        result = {'id': source['id'], 'repo': source['repo'], 'revision': source['revision'],
            'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'status': 'source_leads_only', 'files': [], 'errors': [],
            'warning': 'Issue state is current, not proof of a missing feature at the fixed revision. Build/reproduce before selecting a contract.'}
        repo = source['repo']; revision = source['revision']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) or not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise ValueError('Invalid pinned source identity')
        urls = [('tree.json', f'https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1'),
                ('recent-issues-and-prs.json', f'https://api.github.com/repos/{repo}/issues?state=all&per_page=20')]
        for name, url in urls:
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'EdgeBench-source-authoring', 'Accept': 'application/vnd.github+json'})
                with urllib.request.urlopen(request, timeout=30) as response: content = response.read()
                decoded = json.loads(content)
                (directory / name).write_bytes(content)
                result['files'].append({'path': name, 'url': url, 'sha256': hashlib.sha256(content).hexdigest()})
                if name == 'tree.json': result['tree_truncated'] = decoded.get('truncated', False)
            except Exception as exc:
                result['errors'].append({'url': url, 'type': type(exc).__name__, 'message': str(exc)[:200]})
        if result['errors']: result['status'] = 'partial_source_leads'
        write(directory / 'receipt.json', result); results.append(result)
    summary = {'schema_version': 2, 'sources': results, 'completed_tasks': 0,
               'source_selection_validated': False, 'next': 'Native author reads fixed complete sources, investigates multiple scopes and reproduces strongest ordinary baselines.'}
    write(output / 'summary.json', summary)
    return summary


def catalog():
    data = read(ROUTES)
    with ORIGINALS.open(encoding='utf-8-sig') as file:
        tasks = list(csv.DictReader(file))
    assert len(tasks) == len({r['task_id'] for r in tasks}) == 36
    assert set(r['mechanism_code'] for r in tasks) == set(data['routes'])
    for code, route in data['routes'].items():
        rows = [r for r in tasks if r['mechanism_code'] == code]
        route['original_tasks'] = [r['task_id'] for r in rows]
        route['original_count'] = len(rows)
        route['public_count'] = sum(r['public_definition'].lower() == 'true' for r in rows)
    data.update(original_task_count=36, public_task_count=12,
                source_sha256=hashlib.sha256(ORIGINALS.read_bytes()).hexdigest())
    assert sum(r['public_count'] for r in data['routes'].values()) == 12
    return data


AUTHOR_CONTRACT = '''
本轮任务是造出具有足够真实工程量/优化深度的长程软工题，不是把一个小特性包装成大仓库题。
依次完成 MATERIAL_MINING.json → SCOPE_CARD.json → REQUIREMENTS.json → task/ → AUTHOR_RESULT.json。
先阅读 guidance 中三套factory原始规约、原EdgeBench分类/尺度报告、开发机作者规范。
原EdgeBench素材仅供作者理解类型和尺度，不复制其题面/测试/答案到训练环境。

1. 素材：完整获取固定revision、许可、文档、原生测试，保存哈希。审阅至少三个有真实来源的候选范围，逐项记录已有能力、真正缺失的交付、普通强基线、探针、保留/否定理由。只换同一窄feature的三个参数不算三个范围。
2. 工程范围：列出目标系统边界、所有核心交付能力、公开API/生产模块、共享状态及端到端场景。必须说明学生得到什么、还要实现什么；作者写grader/下载依赖/等待编译不计求解工程量。参考原题产品roadmap、完整引擎、多crate恢复、兼容重建，禁止静默收缩成一个helper/journal/retry。
3. 参考和题面：先得到完整可运行的真实参考与清晰可实现合同，再构造starter/规格。产品roadmap应有多组实质目标；系统重建保留正常依赖但不暴露目标实现；消融保留完整gold/求逆/回归，不只删几个条件。模块/LOC/检查数量只描述规模，不能自动宣称难度。
4. 便宜否证：实际测试最强正常工具、配置、库组合和包装。独立方案与gold mutation分开。若合理捷径已饱和，换真正的需求范围或拒绝该候选，不能临时禁库、减弱基线、加无关case/等待或改旧奖励。
5. 评分：公开任务/权重/分母，独立结构化valid/score/checks/raw metrics；原生reward与周期score同一权威值。每项得分对应真实交付，部分实现可局部验证；可使用功能覆盖，不强迫所有题加性能。性能题先做强基线、代表性负载、独立计时、在线候选配对重评；未启用性能或starter达当前上限只能held，不能交“可训练完整题”。
6. 构造：独立agent/verifier构建上下文，公开仅starter/契约/开发反馈，私有参考/评分器/保留集。交完整task.toml、instruction、Dockerfiles、solution、tests、来源/许可/依赖清单、真实控制记录。运行都在当前job下；禁止全局安装、共享配置/daemon操作、清理别人的文件。每个构建最多-j4。
7. SCOPE_CARD遵循guidance/scope-card.schema-example.json。所有evidence是当前job内的实际文件和SHA256；至少包含starter/reference/independent_baseline控制的真实结构化结果。若只是语义探针，标注probe_only，不冒充同一完整grader分数。执行swe gate --job当前目录只得到静态检查，不得称难度/运行验收。
8. 两条后期改进路径必须写具体能力、前置成果、可冻结产物和原始指标变化；不能承诺必需几小时。作者同时写gold/测试存在偏差，独立审查在之后进行。
9. 用户本轮仅授权出题；不得启动教师、云实例、其他模型/CLI agent/子代理，不改已有题和轨迹。实际作者使用gpt-6.1-sol。拒绝/hold是有效结果，但不能因第一个小合同失败就不再调查其他真实范围。
'''


def plan(sources, output, remote_root):
    if output.exists():
        raise FileExistsError(output)
    data = catalog(); jobs = read(sources)['jobs']; seen = set()
    for job in jobs:
        assert re.fullmatch(r'[a-zA-Z0-9_-]+', job['id'])
        assert re.fullmatch(r'[0-9a-f]{40}', job['revision'])
        assert job['route'] in data['routes']
        identity = (job['repo'].lower().removesuffix('.git'), job['revision'], job['route'])
        if identity in seen:
            raise ValueError('Duplicate source/route')
        seen.add(identity)
        assert job['url'] == 'https://github.com/' + job['repo'] + '.git'
    output.mkdir(parents=True)
    write(output / 'taxonomy.json', data)
    write(output / 'source-registry.json', read(sources))
    prepared = []
    for job in jobs:
        route = data['routes'][job['route']]
        directory = output / 'jobs' / job['id']; directory.mkdir(parents=True)
        prompt = ('# 类别专用长程软工构造\n\n' + AUTHOR_CONTRACT + '\n\n'
                  + json.dumps({'source': job, 'route': route}, ensure_ascii=False, indent=2)
                  + '\n\n本题特定的范围要求：\n' + job['scope_brief'] + '\n')
        (directory / 'prompt.md').write_text(prompt)
        (directory / 'AGENTS.md').write_text('Authorized native AUTHOR job. Follow prompt.md. Write only beneath this job. Do not launch models, subagents, teachers or cloud sandboxes. Preserve shared sources and previous tasks.\n')
        prepared.append({**job, 'cwd': str(remote_root / 'jobs' / job['id']),
                         'model': 'gpt-6.1-sol', 'reasoning_effort': 'high',
                         'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()})
    write(output / 'launch-plan.json', {'schema_version': 2, 'phase': 'authoring_only',
                                      'jobs': prepared, 'teacher_runs_authorized_in_this_batch': False})
    return {'jobs': len(prepared), 'routes': sorted(set(j['route'] for j in jobs)), 'output': str(output)}


def checked_file(job, item):
    relative = Path(item['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Evidence must stay inside the author job')
    path = job / relative
    if any(p.is_symlink() for p in [path, *list(path.parents)[:len(relative.parts)]]):
        raise ValueError('Symlink evidence is not frozen evidence')
    if not path.is_file() or not path.resolve().is_relative_to(job.resolve()):
        raise ValueError('Missing or escaping evidence')
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('Evidence hash mismatch')
    return path


def gate(job):
    """Inspect actual report bytes; a static pass never implies runtime/difficulty pass."""
    result = {'schema_version': 2, 'job': str(job), 'outcome': 'blocked', 'issues': [],
              'controller_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'six_hour_verified': False, 'runtime_verified': False, 'independent_scope_review': 'not_performed',
              'scope_note': 'File/contract/report consistency only; does not prove execution or engineering difficulty.'}
    issues = result['issues']
    try:
        card = read(job / 'SCOPE_CARD.json')
        route = catalog()['routes'][card['route']]
        if not re.fullmatch(r'[0-9a-f]{40}', card['source']['revision']):
            issues.append('source_revision_not_pinned')
        if not card['source'].get('license'):
            issues.append('source_license_missing')
        if not set(card['anchors']) & set(route['original_tasks']):
            issues.append('missing_original_task_anchor')
        for field in ['system_boundary', 'provided_components', 'missing_capabilities', 'requirements',
                      'integration_scenarios', 'late_work_paths', 'shortcut_probes']:
            if not card.get(field): issues.append('missing_' + field)
        evidence = {}
        for item in card['evidence']:
            if item['id'] in evidence: raise ValueError('Duplicate evidence ID')
            evidence[item['id']] = checked_file(job, item)
        ids = {r['id'] for r in card['requirements']}
        if len(ids) != len(card['requirements']): issues.append('duplicate_requirement_ids')
        for req in card['requirements']:
            if not all(req.get(k) for k in ['behavior', 'production_modules', 'acceptance', 'milestone', 'evidence_ids']):
                issues.append('incomplete_requirement_' + req['id'])
            if not set(req.get('evidence_ids', [])) <= evidence.keys(): issues.append('unknown_requirement_evidence')
        for scenario in card['integration_scenarios']:
            if not set(scenario['requirements']) <= ids: issues.append('unknown_integration_requirement')
        if len(card['late_work_paths']) < 2: issues.append('missing_specific_late_work_paths')
        if len({json.dumps(x, sort_keys=True) for x in card['late_work_paths']}) < 2:
            issues.append('duplicate_late_work_paths')
        for late in card['late_work_paths']:
            if not all(late.get(k) for k in ['capability', 'prerequisites', 'artifact', 'metric_effect']):
                issues.append('incomplete_late_work_path')
        scoring = card['scoring']
        ceiling = scoring['active_ceiling']
        if not isinstance(ceiling, (float, int)) or isinstance(ceiling, bool) or not math.isfinite(ceiling):
            raise ValueError('Nonfinite score ceiling')
        if scoring.get('direction') != 'higher_is_better':
            issues.append('normalized_reward_direction_not_supported')
        if not scoring.get('formula') or scoring.get('spec_evidence_id') not in evidence:
            issues.append('missing_machine_readable_score_contract')
        if card['route'] == 'M3':
            perf = scoring.get('performance', {})
            if perf.get('enabled') is not True: issues.append('performance_reward_disabled')
            if not perf.get('formula') or not perf.get('measured_anchors'): issues.append('performance_contract_incomplete')
        controls = {}
        for control in card['controls']:
            role = control['role']
            if role in controls: raise ValueError('Duplicate control role')
            report = read(evidence[control['report_evidence_id']])
            if report.get('valid') is not True: issues.append('control_not_valid_' + role); continue
            score = report.get('score')
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
                issues.append('control_missing_real_score_' + role); continue
            if not 0 <= score <= ceiling + 1e-10: issues.append('control_score_outside_active_range_' + role)
            if control.get('score') is not None and abs(control['score'] - score) > 1e-10:
                issues.append('claimed_score_disagrees_' + role)
            if role == 'independent_baseline' and control.get('provenance') != 'independent':
                issues.append('reference_mutation_is_not_independent_baseline')
            controls[role] = score
        for role in ['starter', 'reference', 'independent_baseline']:
            if role not in controls: issues.append('missing_full_score_control_' + role)
        for role in ['starter', 'independent_baseline']:
            if controls.get(role, -1) >= ceiling - 1e-10:
                issues.append(role + '_already_saturates_active_score')
        for relative in ['task/instruction.md', 'task/task.toml', 'task/environment/Dockerfile',
                         'task/verifier/Dockerfile', 'task/tests/test.sh', 'task/solution/solve.sh']:
            if not (job / relative).is_file(): issues.append('missing_package_file:' + relative)
        result['observed_controls'] = controls
        result['workload_signals'] = {'requirements': len(card['requirements']),
            'production_modules': len({m for r in card['requirements'] for m in r.get('production_modules', [])}),
            'milestones': len({r.get('milestone') for r in card['requirements']}),
            'interpretation': 'Descriptive only; counts do not establish engineering volume or six-hour potential.'}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append('incomplete_or_invalid_evidence:' + type(exc).__name__ + ':' + str(exc))
    if not issues: result['outcome'] = 'needs_independent_scope_and_runtime_review'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    show = commands.add_parser('catalog'); show.add_argument('--output', type=Path)
    collect = commands.add_parser('harvest')
    collect.add_argument('--sources', required=True, type=Path)
    collect.add_argument('--output', required=True, type=Path)
    prepare = commands.add_parser('plan')
    prepare.add_argument('--sources', required=True, type=Path)
    prepare.add_argument('--output', required=True, type=Path)
    prepare.add_argument('--remote-root', required=True, type=Path)
    inspect = commands.add_parser('gate')
    inspect.add_argument('--job', required=True, type=Path); inspect.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'catalog': result = catalog()
    elif args.command == 'harvest': result = harvest(args.sources, args.output)
    elif args.command == 'plan': result = plan(args.sources, args.output, args.remote_root)
    else: result = gate(args.job)
    if getattr(args, 'output', None) and args.command not in ['plan', 'harvest']: write(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(args.command == 'gate' and result['outcome'] == 'blocked')


if __name__ == '__main__':
    sys.exit(main())
