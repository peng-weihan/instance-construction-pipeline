"""Fresh host admission for the user's added accounts; no cloud allocation."""
from pathlib import Path
import datetime
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
plan = json.loads((ROOT / 'launch-plan.json').read_text())
slots = ROOT / 'native-slots'
slots.mkdir(exist_ok=False)
homes = {str(Path('/ws/users/wcgu/new-codex-group/raymone') / n): n for n in ['4', '5', '6']}
seen = {n: [] for n in homes.values()}
for p in Path('/proc').glob('[0-9]*/environ'):
    try:
        env = dict(x.split(b'=', 1) for x in p.read_bytes().split(b'\0') if b'=' in x)
        home = env.get(b'CODEX_HOME', b'').decode()
        if env.get(b'CODEX_AUTH_JSON_PATH'):
            home = str(Path(env[b'CODEX_AUTH_JSON_PATH'].decode()).parent)
        args = (p.parent / 'cmdline').read_bytes().split(b'\0')
        explicit = [x.decode().split('=', 1)[1] for x in args if x.startswith(b'selected_codex_home=')]
        if explicit:
            home = explicit[-1]
        if home not in homes:
            continue
        comm = (p.parent / 'comm').read_text().strip()
        if comm == 'codex' or (b'run' in args and any(b'harbor' in x for x in args[:3])):
            seen[homes[home]].append({'pid': int(p.parent.name), 'comm': comm,
                'start_ticks': (p.parent / 'stat').read_text().rsplit(')', 1)[1].split()[19],
                'host_harbor': b'run' in args})
    except (OSError, ValueError):
        continue
stamp = time.time()
for n, rows in seen.items():
    # Any unidentified Harbor selector conservatively blocks that new account.
    assert not any(x['host_harbor'] for x in rows), 'Review pre-existing cloud selector before using ' + n
    assert len(rows) + 2 <= 10
    (slots / ('raymone' + n + '.json')).write_text(json.dumps({'account': 'raymone/' + n,
        'limit': 10, 'outside_observed': len(rows), 'observed_epoch': stamp, 'observed_processes': rows,
        'leases': {}, 'observer_scope': 'actual selected host roots; new homes absent from old20x observer',
        'shared_registry_modified': False}, indent=2) + '\n')
dispatched = []
for job in plan['jobs']:
    d = Path(job['cwd'])
    assert not (d / 'status.json').exists()
    with (d / 'supervisor.log').open('wb') as log:
        p = subprocess.Popen(['/usr/bin/python3', '-u', str(ROOT / 'scripts/worker.py'), job['id']],
            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    dispatched.append({'id': job['id'], 'account': job['account'], 'worker_pid': p.pid})
(ROOT / 'startup.json').write_text(json.dumps({'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'phase': 'authoring_only', 'dispatched': dispatched, 'teacher_rollouts_started': 0,
    'actual_account_observations': seen, 'shared_registry_modified': False}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dispatched, ensure_ascii=False), flush=True)
