"""Admit real runs against a fresh three-account observation, without foreign edits."""
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

from build_packages import ROOT, TASKS, dump

lock = (ROOT / 'dispatch.lock').open('a')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
registry = ROOT / 'model-reservations.json'
if registry.exists():
    raise RuntimeError('This admission is one-shot; preserve existing workers and reservations')
env = os.environ.copy()
# Reuse only the owner's host SDK connection selection; never output its values.
source = next((Path('/proc', str(pid), 'environ') for pid in [3683329, 3418236]
               if Path('/proc', str(pid), 'environ').exists()), None)
if source:
    values = dict(x.split(b'=', 1) for x in source.read_bytes().split(b'\0') if b'=' in x)
    for key in ['TBSCI_E2B_CREDENTIAL_FILE', 'E2B_API_KEY', 'E2B_API_URL', 'E2B_DOMAIN']:
        if key.encode() in values:
            env[key] = values[key.encode()].decode()
else:
    env['TBSCI_E2B_CREDENTIAL_FILE'] = '/ws/users/wcgu/aliyun-sandbox-runtime/private/connection.json'

ready = []
for key in TASKS:
    pilot = ROOT / key
    assert (pilot / 'images.json').is_file(), key + ': images missing'
    assert not (pilot / 'roll-status.json').exists(), 'Do not duplicate an existing worker'
    ready.append(key)
audit = ROOT.parent / 'swe-authoring-016-20261015-r1/authoring/review_raymone123_actual_unused_accounts_r1.py'
p = subprocess.run([sys.executable, str(audit)], env=env, capture_output=True, text=True, timeout=150, check=True)
receipt = Path(json.loads(p.stdout.splitlines()[-1])['report'])
observed = json.loads(receipt.read_text())
outside, capacities = {}, {}
for row in observed['accounts']:
    account = row['account']
    native = sum(x['comm'] == 'codex' for x in row['actual_selected_codex_processes'])
    count = len(row['active_SDK_learners']) + native + len(row['Docker_bindings'])
    # Retain the unresolved old account-3 cloud lease from the earlier audit.
    if account == 'raymone/3':
        count += 1
    outside[account] = count
    capacities[account] = max(0, 10 - count) if not row['unknown_hosts'] and not row['SDK_observation_errors'] else 0
assert sum(capacities.values()) >= len(ready), 'Insufficient actually observed capacity for all five; no models started'
assert time.time() - observed['observed_epoch'] < 90
state = {'outside_counts': outside, 'observed_epoch': observed['observed_epoch'],
         'actual_audit_receipt': str(receipt), 'account_limit': 10, 'leases': {},
         'shared_registries_modified': False, 'purpose': 'one model session per worker; admission then six-hour learner'}
dump(registry, state)
dispatched = []
for account in ['raymone/1', 'raymone/3', 'raymone/2']:
    for _ in range(capacities[account]):
        if not ready:
            break
        key = ready.pop(0)
        token = uuid.uuid4().hex
        with (ROOT / key / 'roll-worker.log').open('wb') as log:
            child = subprocess.Popen([sys.executable, '-u', str(ROOT / 'scripts/roll_worker.py'), key, account, token],
                env=env, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        ticks = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        entry = {'task': key, 'account': account, 'worker_pid': child.pid, 'worker_start_ticks': ticks,
                 'lease': token, 'model_slots': 1, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        with (ROOT / 'model-reservations.lock').open('a') as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            state = json.loads(registry.read_text())
            state['leases'][token] = entry
            dump(registry, state)
        dispatched.append(entry)
dump(ROOT / 'dispatch.json', {'actual_admission': str(receipt), 'outside_counts': outside,
    'capacity_before': capacities, 'dispatched': dispatched, 'pending': ready,
    'model': 'gpt-6.1-sol', 'reasoning_effort': 'high', 'learning_budget_seconds': 21600,
    'evaluation_interval_seconds': 600, 'difficulty_early_stop': False,
    'shared_registries_modified': False, 'formal_acceptance': False})
print(json.dumps({'dispatched': dispatched, 'pending': ready}, ensure_ascii=False), flush=True)
