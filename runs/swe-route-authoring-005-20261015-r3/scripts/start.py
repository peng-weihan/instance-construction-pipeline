"""Admit our new batch from current native roots, then start author workers only."""
from pathlib import Path
from collections import Counter
import datetime
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
plan = json.loads((ROOT / 'launch-plan.json').read_text())
slots = ROOT / 'native-slots'; slots.mkdir(exist_ok=False)
homes = {j['codex_home']: j['account'] for j in plan['jobs']}
seen = {n: [] for n in homes.values()}
for proc in Path('/proc').glob('[0-9]*'):
    try:
        comm = (proc / 'comm').read_text().strip()
        args = (proc / 'cmdline').read_bytes().split(b'\0')
        native = comm == 'codex' and b'exec' in args and b'--model' in args
        harbor = b'run' in args and any(b'harbor' in a for a in args[:3])
        if not (native or harbor): continue
        # Never output environment values or auth; inspect only identity selectors.
        selected = {}
        for row in (proc / 'environ').read_bytes().split(b'\0'):
            if row.startswith((b'CODEX_HOME=', b'CODEX_AUTH_JSON_PATH=')):
                k, value = row.split(b'=', 1); selected[k] = value.decode()
        home = selected.get(b'CODEX_HOME')
        if selected.get(b'CODEX_AUTH_JSON_PATH'): home = str(Path(selected[b'CODEX_AUTH_JSON_PATH']).parent)
        explicit = [a.decode().split('=', 1)[1] for a in args if a.startswith(b'selected_codex_home=')]
        if explicit: home = explicit[-1]
        if home not in homes: continue
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        if fields[0] == 'Z': continue
        seen[homes[home]].append({'pid': int(proc.name), 'comm': comm, 'start_ticks': fields[19], 'host_harbor': harbor})
    except (OSError, ValueError): pass
planned = Counter(j['account'] for j in plan['jobs'])
for home, account in homes.items():
    assert not any(r['host_harbor'] for r in seen[account]), 'Unresolved cloud selector on account'
    assert len(seen[account]) + planned[account] <= 10
    binary = Path(home) / 'bin/codex'
    expected = next(j['expected_cli_sha256'] for j in plan['jobs'] if j['account'] == account)
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == expected
stamp = time.time()
for account, rows in seen.items():
    n = account.split('/')[-1]
    (slots / ('raymone' + n + '.json')).write_text(json.dumps({'account': account, 'limit': 10,
        'outside_observed': len(rows), 'observed_epoch': stamp, 'observed_processes': rows, 'leases': {},
        'observer_scope': 'current host native CLI exec roots; helpers excluded; account cap is operational, not provider quota',
        'shared_registry_modified': False}, indent=2) + '\n')
started = []
for job in plan['jobs']:
    d = Path(job['cwd']); assert not (d / 'status.json').exists()
    assert hashlib.sha256((d / 'prompt.md').read_bytes()).hexdigest() == job['prompt_sha256']
    with (d / 'supervisor.log').open('wb') as log:
        proc = subprocess.Popen(['/usr/bin/python3', '-u', str(ROOT / 'scripts/worker.py'), job['id']],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    started.append({'id': job['id'], 'route': job['route'], 'account': job['account'], 'worker_pid': proc.pid})
result = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'phase': 'authoring_only',
    'dispatched': started, 'account_observations': seen, 'teacher_rollouts_started': 0, 'shared_registry_modified': False}
(ROOT / 'startup.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False), flush=True)
