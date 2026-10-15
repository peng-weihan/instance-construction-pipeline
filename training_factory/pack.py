"""Freeze two independent, original-sized optimization tasks from accepted cases."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from .calibrate import write_json
from .contract import digest, geometry_fingerprint, read_instance
from .generator import FAMILIES

README = '''# Optimize a C++17 CVRPTW solver

Improve the supplied general-purpose vehicle-routing solver. Submit only `src/`,
`include/`, and `Makefile`. `make` must produce `cvrptw_solver` with the interface:

    ./cvrptw_solver <input.txt> <output.txt> <time_budget_sec>

The six families C1, C2, R1, R2, RC1, RC2 contain 100 customers each. They vary
in clustered/random/mixed geometry, capacity, service duration and time windows.
All hidden inputs are freshly generated. Public examples are in instances/public/.
The feedback and final suites each contain 56 independent cases, with counts
C1=9, C2=8, R1=12, R2=11, RC1=8, RC2=8. Every customer must appear exactly once;
capacity, service-start windows, depot return horizon and MAX_VEHICLES are strict.
Distance is Euclidean rounded to 0.1 per edge (`std::round(distance * 10) / 10`).
Waiting is permitted. Routes begin/end at depot 0. Output syntax:

    Routes: 1
    Route 1: 0 1 2 0
    Cost: 123.40

The public C++ checker is tools/verify.cpp. It independently recomputes feasibility
and distance. Self-reported costs must agree within 0.05. The illustration above
is only syntax, not a valid solution for an example input.

Score prioritizes reducing vehicles, then distance. For feasible output (nv,td)
and a frozen checked reference (bnv,btd), per-case raw score is:

    s = max(0, 100 - 30*max(0,nv-bnv) - 0.5*max(0,100*(td-btd)/btd))
    if nv < bnv: s += 30*(bnv-nv)
    if nv <= bnv and td < btd: s += min(30,100*(btd-td)/btd)
    s = min(s,160)

Infeasible/timeout cases score zero. Mean raw score is reported; 100 means matching
the reference, not a proof of optimality. References can be beaten. Do not read
hidden inputs, reference solutions, author assets or grader internals. Do not
hard-code instances or install external solvers. Use the standard C++17 library.

Run `python3 feedback.py` to submit the permitted source files for aggregate
feedback. It can take about one minute. The pilot uses 1 second per case; final
validation uses 3 seconds per case. The full evaluation profile uses 60 seconds
per case and a 20-minute total deadline. Respect the budget argument in all modes.
Only feedback may guide changes; final evaluation runs once after code is frozen.

You have 10 minutes to develop. Test correctness, improve the heuristic, and leave
the best code in place. Explain your changes and actual tests in your final answer.
Run feedback.py on the exact final source before finishing; do not make untested
edits after the last feedback call. A successful trajectory needs all final cases
feasible and mean raw score at least 90. Strong improvements are useful even if
that acceptance threshold is not reached.
For trace reproducibility, make edits with shell commands (e.g. Python or heredoc)
so their exact text appears in the command log. Do not use apply_patch or subagents.
'''

FEEDBACK_CLIENT = '''#!/usr/bin/env python3
"""Submit an allowed source snapshot to the local aggregate-feedback queue."""
import base64, json, pathlib, time, uuid
root = pathlib.Path(__file__).resolve().parent
files = {}
for top in ["src", "include", "Makefile"]:
    target = root / top
    paths = [target] if target.is_file() else sorted(target.rglob("*"))
    for p in paths:
        if p.is_symlink(): raise SystemExit("Symlinks are not accepted")
        if p.is_file(): files[str(p.relative_to(root))] = base64.b64encode(p.read_bytes()).decode()
if sum(len(v) for v in files.values()) > 4_000_000: raise SystemExit("Submission too large")
queue = root / ".feedback"
queue.mkdir(exist_ok=True)
rid = uuid.uuid4().hex
temporary = queue / (rid + ".tmp")
temporary.write_text(json.dumps({"files": files}))
temporary.rename(queue / (rid + ".request.json"))
response = queue / (rid + ".response.json")
deadline = time.monotonic() + 180
while not response.exists():
    if time.monotonic() > deadline: raise SystemExit("Feedback service did not respond in 180 seconds")
    time.sleep(.25)
print(response.read_text())
'''


def snapshot(root):
    root = Path(root)
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def pack(pool, output, starter, tasks=2):
    pool, output, starter = map(Path, [pool, output, starter])
    source = json.loads((pool / 'summary.json').read_text())
    if not source['complete']:
        raise ValueError('Candidate pool must finish first')
    if (pool / 'alignment.json').exists() and not json.loads((pool / 'alignment.json').read_text())['passed']:
        raise ValueError('Difficulty alignment failed; mine more candidates before packing')
    profiles = json.loads((pool / 'profiles.json').read_text())
    excluded = set(json.loads((pool / 'excluded_original_fingerprints.json').read_text()))
    by_family = {f: [r for r in source['records'] if r['family'] == f and r['accepted']] for f in FAMILIES}
    required = {f: tasks * (2 * profiles[f]['source_count'] + 1) for f in FAMILIES}
    if any(len(by_family[f]) < required[f] for f in FAMILIES):
        raise ValueError({'insufficient_accepted': {f: (len(by_family[f]), required[f]) for f in FAMILIES}})
    output.mkdir(parents=True, exist_ok=False)
    seen, manifests = set(excluded), []
    for number in range(tasks):
        task_id = 'cvrptw_aligned_' + digest([number, [r['name'] for r in source['records']]])[:12]
        root = output / 'tasks' / task_id
        work = root / 'work'
        for name in ['src', 'include', 'tools']:
            shutil.copytree(starter / name, work / name, ignore=shutil.ignore_patterns('verify', '__pycache__'))
        shutil.copy2(starter / 'Makefile', work / 'Makefile')
        (work / 'README.md').write_text(README)
        (work / 'feedback.py').write_text(FEEDBACK_CLIENT)
        (work / 'NOTICE.txt').write_text('Starter, header, Makefile and checker adapted from ByteDance-Seed/EdgeBench '
            'vehicle_routing_time_windows public task images. Task assets: CC BY 4.0. '
            'https://huggingface.co/datasets/ByteDance-Seed/EdgeBench\n'
            'Fresh synthetic inputs and local feedback client by this factory; not official benchmark questions.\n')
        split_records = {'public': [], 'feedback': [], 'final': []}
        for family in FAMILIES:
            n = profiles[family]['source_count']
            for split, count in [('public', 1), ('feedback', n), ('final', n)]:
                for _ in range(count):
                    record = by_family[family].pop(0)
                    origin = pool / 'candidates' / record['name']
                    case = read_instance(origin / 'instance.txt')
                    fp = geometry_fingerprint(case)
                    if fp in seen:
                        raise ValueError('Original/permuted/duplicate case detected')
                    seen.add(fp)
                    destination = work / 'instances' / 'public' if split == 'public' else root / 'judge' / split
                    destination.mkdir(parents=True, exist_ok=True)
                    name = record['name'] + '.txt'
                    shutil.copy2(origin / 'instance.txt', destination / name)
                    # No witnesses, reference routes, seeds, or original inputs in work.
                    split_records[split].append({'name': record['name'], 'family': family, 'filename': name,
                        'fingerprint': fp, 'sha256': hashlib.sha256((destination / name).read_bytes()).hexdigest(),
                        'reference': record['reference'], 'starter_score': record['starter_score']})
        write_json(root / 'judge' / 'cases.json', split_records)
        policy = {'model': 'gpt-6.1-sol', 'teacher_seconds': 600, 'feedback_budget_seconds': 1,
            'final_budget_seconds': 3, 'minimum_final_raw_score': 90, 'minimum_feedback_gain': 20,
            'require_all_final_feasible': True, 'require_complete_real_trace': True,
            'require_private_files_denied': True, 'full_profile_per_case_seconds': 60,
            'full_profile_total_seconds': 1200}
        write_json(root / 'policy.json', policy)
        manifest = {'task_id': task_id, 'task_family': 'vehicle_routing_time_windows',
            'counts': {s: len(r) for s, r in split_records.items()},
            'family_counts': {s: dict(Counter(r['family'] for r in rows)) for s, rows in split_records.items()},
            'work_sha256': snapshot(work), 'judge_sha256': snapshot(root / 'judge'), 'policy': policy,
            'source_pool': str(pool.resolve()), 'status': 'source_aligned_proxy_screened',
            'code_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in Path(__file__).parent.glob('*.py')},
            'public_contains_original_test_inputs': False, 'sft_accepted': False}
        write_json(root / 'manifest.json', manifest)
        manifests.append(manifest)
    write_json(output / 'summary.json', {'tasks': len(manifests), 'cases': sum(sum(m['counts'].values()) for m in manifests),
        'original_test_inputs_exported': 0, 'duplicate_cases': 0, 'sft_episodes': 0, 'manifests': manifests})
    return manifests


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pool', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--starter', default='data/routing_alignment/original_work')
    parser.add_argument('--tasks', type=int, default=2)
    args = parser.parse_args()
    pack(args.pool, args.output, args.starter, args.tasks)
