"""Read-only source/contract audit. No model, solution, grader or container execution."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(batch):
    profiles = json.loads((HERE / 'authoring_profiles.json').read_text())['profiles']
    rows = []
    for profile in profiles:
        task = batch / profile['task_id']
        repo = ROOT / 'materials/repos' / profile['source_repo']
        provenance = json.loads((task / 'source_provenance.json').read_text())
        actual_commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        sources = []
        for source in provenance['sources']:
            checks = []
            for entry in source['files']:
                path = repo / entry['path']
                actual_hash = sha(path) if path.is_file() else None
                checks.append({'path': entry['path'], 'expected_sha256': entry['sha256'],
                               'actual_sha256': actual_hash, 'matches': actual_hash == entry['sha256']})
            sources.append({'repository': source['repository'], 'expected_commit': source['commit'],
                            'actual_commit': actual_commit, 'commit_matches': actual_commit == source['commit'],
                            'key_files': checks})
        contracts = [{'path': rel, 'exists': (task / 'public' / rel).is_file()}
                     for rel in profile['public_contract_paths']]
        anchor = ROOT / 'data/EdgeBench' / (profile['anchor'] + '.json')
        rows.append({**profile, 'source_checks': sources, 'public_contract_checks': contracts,
                     'anchor_definition_sha256': sha(anchor),
                     'anchor_definition': str(anchor.relative_to(ROOT)),
                     'negative_control_status': 'designed_not_executed',
                     'six_hour_status': 'design_hypothesis_only',
                     'review_pass': all(c['exists'] for c in contracts)
                        and all(s['commit_matches'] and all(c['matches'] for c in s['key_files']) for s in sources)})
    report = {'batch': str(batch.relative_to(ROOT)), 'scope': 'pinned source files and public contract presence; qualitative authoring review',
              'not_established': ['runtime correctness', 'full original-asset deduplication', 'statistical distribution match', 'training gain', 'six-hour difficulty'],
              'model_runs': 0, 'grader_runs': 0, 'rows': rows}
    (batch / 'authoring_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 素材与题目构造复核', '',
             '此报告逐题核对上游 commit、已登记关键文件摘要和公开接口材料。工作链、来源筛选和反例是出题设计，不是运行成绩。原始 EdgeBench 定义只在作者侧用于对照。', '',
             '| 当前题目 | 对照原题 | 固定来源与公开契约 |', '|---|---|---|']
    for row in rows:
        lines.append(f"| [{row['task_id']}]({row['task_id']}/instruction.md) | {row['anchor']} | {'通过' if row['review_pass'] else '有缺口'} |")
    for row in rows:
        lines += ['', '## ' + row['task_id'], '',
                  '**候选来源：** ' + row['candidate_pool'], '',
                  '**素材准入：** ' + row['admission'], '',
                  '**构造方法：** ' + row['construction'], '',
                  '**保留的能力结构：** ' + row['preserved_work'], '',
                  '**新任务差异：** ' + row['new_work'], '',
                  '**预计改进层次：** ' + ' → '.join(row['progression']), '',
                  '**需要后续运行的反例：** ' + '; '.join(row['near_miss_candidates']), '',
                  '**未决问题：** ' + row['risk']]
    lines += ['', '没有运行上述反例、求解器或评分器；不得将源码与材料检查标为任务验收。', '']
    (batch / 'AUTHORING_REVIEW.md').write_text('\n'.join(lines))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('batch')
    args = parser.parse_args()
    report = review(Path(args.batch).resolve())
    for row in report['rows']:
        print(row['task_id'], 'source_and_contract_ok=' + str(row['review_pass']))
    raise SystemExit(0 if all(row['review_pass'] for row in report['rows']) else 1)
