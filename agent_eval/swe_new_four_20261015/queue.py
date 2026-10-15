"""Dispatch only prepared new tasks, preserving observed and reserved occupancy."""
from pathlib import Path
import datetime
import fcntl
import json
import os
import subprocess
import sys
import time
import uuid

from build_packages import ROOT, TASKS, BASE, dump

ACCOUNT = 'raymone/1'
AUDIT = BASE / 'swe-authoring-016-20261015-r1/authoring/review_raymone123_actual_unused_accounts_r1.py'


def read(path, default=None):
    try: return json.loads(path.read_text())
    except (OSError, ValueError): return default


def ready(key):
    p = ROOT / key
    if (p / 'roll-status.json').exists(): return False
    a = read(p / 'scorer-controls.json', {})
    b = read(p / 'native-controls/report.json', {})
    return a.get('passed') is True and b.get('passed') is True and all(
        b.get('results', {}).get(role, {}).get('passed') for role in ['oracle', 'nop', 'partial'])


def dispatch(keys):
    result = subprocess.run([sys.executable, str(AUDIT)], capture_output=True, text=True,
                            check=True, timeout=180)
    receipt = Path(json.loads(result.stdout.splitlines()[-1])['report'])
    report = read(receipt)
    assert time.time() - report['observed_epoch'] < 90
    row = next(x for x in report['accounts'] if x['account'] == ACCOUNT)
    if row['unknown_hosts'] or row['SDK_observation_errors']:
        return [{'event': 'observation_incomplete', 'account': ACCOUNT, 'receipt': str(receipt)}]
    actual = len(row['active_SDK_learners']) + len(row['Docker_bindings']) + sum(
        p['comm'] == 'codex' for p in row['actual_selected_codex_processes'])
    outside_actual = len([x for x in row['active_SDK_learners']
                          if not str(x.get('task', '')).startswith(str(ROOT) + '/')])
    outside_actual += len(row['Docker_bindings']) + sum(
        p['comm'] == 'codex' for p in row['actual_selected_codex_processes'])
    external = row.get('existing_external_reservations', 0)
    foreign = len(row.get('existing_foreign_leases_preserved', []))
    other_owned = []
    for p in BASE.glob('swe-*/model-reservations.json'):
        if p.parent == ROOT: continue
        other_owned.extend(x for x in read(p, {}).get('leases', {}).values() if x['account'] == ACCOUNT)
    with (ROOT / 'model-reservations.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        registry = ROOT / 'model-reservations.json'
        state = read(registry, {'leases': {}, 'released': [], 'account_limit': 10,
                                'shared_registries_modified': False})
        own = sum(x['account'] == ACCOUNT for x in state['leases'].values())
        # Conservative union upper bound: preserve foreign/other owned reservations,
        # including their overlap with actual learners, rather than assuming free slots.
        occupied = max(outside_actual, foreign) + external + len(other_owned) + own
        state.update(actual_observed=actual, external_reserved_preserved=external,
                     other_owned_reserved_preserved=len(other_owned), foreign_leases_preserved=foreign,
                     outside_counts={ACCOUNT: max(outside_actual, foreign) + external + len(other_owned)},
                     actual_audit_receipt=str(receipt), observed_epoch=report['observed_epoch'])
        dump(registry, state)
        launched = []
        for key in keys:
            if occupied >= 10 or not ready(key): break
            token = uuid.uuid4().hex
            with (ROOT / key / 'roll-worker.log').open('xb') as log:
                child = subprocess.Popen([sys.executable, '-u', str(ROOT / 'scripts/roll_worker.py'),
                                          key, ACCOUNT, token], stdout=log, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL, start_new_session=True)
            entry = {'task': key, 'account': ACCOUNT, 'worker_pid': child.pid,
                     'worker_start_ticks': Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19],
                     'lease': token, 'model_slots': 1,
                     'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            state['leases'][token] = entry; dump(registry, state)
            launched.append(entry); occupied += 1
        return launched


def main():
    with (ROOT / 'ready-queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        deadline = time.monotonic() + 21600
        events = []
        while time.monotonic() < deadline:
            candidates = [key for key in TASKS if ready(key)]
            if candidates:
                try: events.extend(dispatch(candidates))
                except Exception as exc:
                    events.append({'event': 'dispatch_error', 'error_type': type(exc).__name__,
                                   'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
            pending = [key for key in TASKS if not (ROOT / key / 'roll-status.json').exists()]
            dump(ROOT / 'ready-queue-status.json', {
                'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'pid': os.getpid(), 'pending_preparation_or_account_capacity': pending,
                'attempted': events, 'queue_active': bool(pending), 'model': 'gpt-6.1-sol',
                'account': ACCOUNT, 'account_cap': 10, 'foreign_reservations_preserved': True,
                'learning_budget_seconds': 21600, 'grade_interval_seconds': 600})
            if not pending: break
            time.sleep(30)


if __name__ == '__main__': main()
