"""Retry five previously authorized, pre-model quota failures with new evidence paths."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid

BASE = Path('/ws/users/raymone/edgebench')
JOBS = [
    ('swe-rollouts-002-20261015-r6', '01_openapi_streaming'),
    ('swe-rollouts-005-20261015-r5', '18_polars_streaming'),
    ('swe-rollouts-005-20261015-r5', '19_ruff_project_analysis'),
    ('swe-rollouts-005-20261015-r5', '20_libcst_project_migration'),
    ('swe-rollouts-005-20261015-r5', '21_coverage_context_merge'),
]
ACCOUNT = 'raymone/1'
ATTEMPT = '002'


def dump(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def main():
    selected = []
    for batch, key in JOBS:
        root = BASE / batch; task = root / key
        controls = json.loads((task / 'scorer-controls.json').read_text())
        native = json.loads((task / 'native-controls/report.json').read_text())
        assert controls['passed'] and native['passed']
        assert all(native['results'][k]['passed'] for k in ['oracle', 'nop', 'partial'])
        assert not any(p.is_dir() for p in task.glob('run-6h-*'))
        assert not (task / ('admission-' + ATTEMPT)).exists()
        old = json.loads((task / 'roll-status.json').read_text())
        assert old['phase'] == 'roll_failed' and old.get('owned_reservation_released') is True
        failures = [json.loads(p.read_text()).get('exception_info') or {} for p in (task / 'admission/jobs').rglob('result.json')]
        assert any(e.get('exception_type') == 'RateLimitException' and 'Account resource quota exceeded' in e.get('exception_message', '') for e in failures)
        for p in (task / 'admission/jobs').rglob('aliyun-*.json'):
            d = json.loads(p.read_text()); assert not d.get('created') or d.get('destroyed')
        selected.append((root, task, key, old))
    audit = BASE / 'swe-authoring-016-20261015-r1/authoring/review_raymone123_actual_unused_accounts_r1.py'
    r = subprocess.run([sys.executable, str(audit)], capture_output=True, text=True, timeout=150, check=True)
    receipt = Path(json.loads(r.stdout.splitlines()[-1])['report'])
    report = json.loads(receipt.read_text()); assert time.time() - report['observed_epoch'] < 90
    row = next(a for a in report['accounts'] if a['account'] == ACCOUNT)
    assert not row['unknown_hosts'] and not row['SDK_observation_errors']
    count = len(row['active_SDK_learners']) + len(row['Docker_bindings']) + sum(p['comm'] == 'codex' for p in row['actual_selected_codex_processes'])
    existing_leases = []
    for batch in {b for b, _ in JOBS}:
        existing_leases.extend(json.loads((BASE / batch / 'model-reservations.json').read_text()).get('leases', {}).values())
    assert not existing_leases, 'Reconcile owned reservations first'
    assert count + len(selected) <= 10
    started = []
    for root, task, key, old in selected:
        evidence = task / ('retry-attempt-' + ATTEMPT); evidence.mkdir(exist_ok=False)
        dump(evidence / 'previous-roll-status.json', old)
        launcher = root / 'scripts' / ('launch_' + key + '_retry_' + ATTEMPT + '.py')
        worker = root / 'scripts' / ('worker_' + key + '_retry_' + ATTEMPT + '.py')
        assert not launcher.exists() and not worker.exists()
        src = (root / 'scripts/launch_run.py').read_text()
        assert src.count("'admission/report.json'") == 1
        src = src.replace("'admission/report.json'", repr('admission-' + ATTEMPT + '/report.json'))
        compile(src, str(launcher), 'exec'); launcher.write_text(src)
        src = (root / 'scripts/roll_worker.py').read_text()
        replacements = {
            "'admission'": repr('admission-' + ATTEMPT),
            "'admission/report.json'": repr('admission-' + ATTEMPT + '/report.json'),
            "'admission/jobs'": repr('admission-' + ATTEMPT + '/jobs'),
            "'admission-supervisor.log'": repr('admission-' + ATTEMPT + '-supervisor.log'),
            "'scripts/launch_run.py'": repr('scripts/' + launcher.name),
            "'run-supervisor.log'": repr('run-supervisor-retry-' + ATTEMPT + '.log'),
        }
        for before, after in replacements.items():
            assert before in src, before
            src = src.replace(before, after)
        compile(src, str(worker), 'exec'); worker.write_text(src)
        token = uuid.uuid4().hex
        with (root / 'model-reservations.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads((root / 'model-reservations.json').read_text())
            state.setdefault('outside_counts', {})[ACCOUNT] = count
            state.update(observed_epoch=report['observed_epoch'], actual_audit_receipt=str(receipt))
            with (evidence / 'supervisor.log').open('xb') as log:
                child = subprocess.Popen([sys.executable, '-u', str(worker), key, ACCOUNT, token],
                    stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            ticks = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            entry = {'task': key, 'account': ACCOUNT, 'worker_pid': child.pid,
                     'worker_start_ticks': ticks, 'lease': token, 'model_slots': 1,
                     'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'attempt': ATTEMPT}
            state['leases'][token] = entry; dump(root / 'model-reservations.json', state)
        dump(evidence / 'dispatch.json', {**entry, 'fresh_audit': str(receipt),
             'previous_cloud_quota_failure_preserved': True, 'task_and_frozen_framework_unchanged': True,
             'launcher_sha256': hashlib.sha256(launcher.read_bytes()).hexdigest(),
             'worker_sha256': hashlib.sha256(worker.read_bytes()).hexdigest()})
        started.append(entry)
    dest = BASE / 'rollout-status-20261015' / 'retry-ready-five-002.json'
    dump(dest, {'dispatched': started, 'account_outside_actual_count': count, 'fresh_account_audit': str(receipt),
                'model': 'gpt-6.1-sol', 'learning_budget_seconds': 21600, 'interval_seconds': 600,
                'does_not_claim_cloud_or_model_admission': True})
    print(json.dumps({'receipt': str(dest), 'dispatched': len(started), 'account': ACCOUNT,
                      'actual_outside_count_before_dispatch': count}), flush=True)


if __name__ == '__main__':
    main()
