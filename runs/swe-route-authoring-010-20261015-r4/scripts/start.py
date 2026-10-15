"""Launch enough explicitly authorized authors to reach ten including DataFusion."""
from pathlib import Path
from collections import Counter
import datetime
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def live(pid, ticks):
    try:
        f = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        return f[0] != 'Z' and f[19] == str(ticks)
    except OSError:
        return False


def main():
    plan = json.loads((ROOT / 'launch-plan.json').read_text())
    assert (ROOT / 'deployment.json').exists()
    assert not (ROOT / 'startup.json').exists()
    existing = json.loads(Path(plan['existing_author_status']).read_text())
    existing_active = existing.get('state') == 'native_started' and live(existing.get('native_pid'), existing.get('native_start_ticks'))
    count = plan['target_concurrent_authors'] - int(existing_active)
    jobs = plan['jobs'][:count]
    assert len(jobs) == count
    homes = {j['codex_home']: j['account'] for j in jobs}
    seen = {n: [] for n in homes.values()}
    for p in Path('/proc').glob('[0-9]*'):
        try:
            comm = (p / 'comm').read_text().strip()
            args = (p / 'cmdline').read_bytes().split(b'\0')
            native = comm == 'codex'
            harbor = b'run' in args and any(b'harbor' in a for a in args[:3])
            if not (native or harbor):
                continue
            env = dict(x.split(b'=', 1) for x in (p / 'environ').read_bytes().split(b'\0') if b'=' in x)
            home = env.get(b'CODEX_HOME', b'').decode()
            if env.get(b'CODEX_AUTH_JSON_PATH'):
                home = str(Path(env[b'CODEX_AUTH_JSON_PATH'].decode()).parent)
            explicit = [a.decode().split('=', 1)[1] for a in args if a.startswith(b'selected_codex_home=')]
            if explicit:
                home = explicit[-1]
            if home not in homes:
                continue
            fields = (p / 'stat').read_text().rsplit(')', 1)[1].split()
            if fields[0] == 'Z':
                continue
            seen[homes[home]].append({'pid': int(p.name), 'start_ticks': fields[19],
                                     'comm': comm, 'host_harbor': harbor})
        except (OSError, ValueError):
            pass
    planned = Counter(j['account'] for j in jobs)
    for home, account in homes.items():
        assert not any(r['host_harbor'] for r in seen[account]), 'Account has unresolved cloud selectors'
        assert len(seen[account]) + planned[account] <= 10, 'Actual account occupancy plus new work exceeds operational cap'
        binary = Path(home) / 'bin/codex'
        expected = next(j['expected_cli_sha256'] for j in jobs if j['account'] == account)
        assert hashlib.sha256(binary.read_bytes()).hexdigest() == expected
    slots = ROOT / 'native-slots'; slots.mkdir(exist_ok=False)
    stamp = time.time()
    for account, rows in seen.items():
        n = account.split('/')[-1]
        (slots / ('raymone' + n + '.json')).write_text(json.dumps({
            'account': account, 'limit': 10, 'outside_observed': len(rows),
            'observed_epoch': stamp, 'observed_processes': rows, 'leases': {},
            'observer_scope': 'current host native Codex roots and Harbor selectors; helper children excluded',
            'shared_registry_modified': False}, indent=2) + '\n')
    started = []
    for job in jobs:
        directory = Path(job['cwd'])
        assert not (directory / 'status.json').exists()
        assert hashlib.sha256((directory / 'prompt.md').read_bytes()).hexdigest() == job['prompt_sha256']
        with (directory / 'supervisor.log').open('wb') as log:
            child = subprocess.Popen(['/usr/bin/python3', '-u', str(ROOT / 'scripts/worker.py'), job['id']],
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        started.append({'id': job['id'], 'route': job['route'], 'kind': job['work_kind'],
                        'account': job['account'], 'worker_pid': child.pid})
    result = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'target_concurrent_authors': 10, 'new_author_workers_dispatched': len(started),
              'existing_author_count': int(existing_active),
              'existing_author': {k: existing.get(k) for k in ['id', 'account', 'native_pid', 'native_start_ticks']},
              'dispatched': started, 'standby_not_dispatched': [j['id'] for j in plan['jobs'][count:]],
              'account_observations': seen, 'teacher_rollouts_started': 0, 'shared_registry_modified': False}
    (ROOT / 'startup.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
