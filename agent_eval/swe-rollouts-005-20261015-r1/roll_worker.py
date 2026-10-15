"""Hold one owned account reservation through admission and one formal learner."""
from pathlib import Path
import fcntl
import json
import os
import subprocess
import sys
import time
import traceback

from build_packages import ROOT, dump

KEY, ACCOUNT, TOKEN = sys.argv[1:4]
P = ROOT / KEY
F = ROOT / 'framework'
state = {'task': KEY, 'account': ACCOUNT, 'phase': 'waiting_owned_reservation',
         'worker_pid': os.getpid(), 'model': 'gpt-6.1-sol', 'budget_seconds': 21600,
         'interval_seconds': 600, 'formal_acceptance': False}


def save():
    dump(P / 'roll-status.json', state)


def call(command, filename):
    with (P / filename).open('wb') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(filename + ' failed; inspect owned evidence')


env = os.environ.copy()
env.update(EDGEBENCH_SELECTED_ACCOUNT=ACCOUNT, EDGEBENCH_SLOT_TOKEN=TOKEN,
           PYTHONPATH=os.pathsep.join([str(F), str(F / 'sdk')]), PYTHONDONTWRITEBYTECODE='1')
save()
try:
    for _ in range(100):
        registry = ROOT / 'model-reservations.json'
        if registry.exists() and TOKEN in json.loads(registry.read_text())['leases']:
            break
        time.sleep(.1)
    else:
        raise RuntimeError('No owned reservation')
    state.update(phase='waiting_preflight', model_started=False)
    save()
    until = time.monotonic() + 3600
    while True:
        periodic_path = P / 'scorer-controls.json'
        native_path = P / 'native-controls/report.json'
        periodic = json.loads(periodic_path.read_text()) if periodic_path.exists() else {}
        native = json.loads(native_path.read_text()) if native_path.exists() else {}
        basic = native.get('results', {})
        native_ok = all(basic.get(x, {}).get('passed') for x in ['oracle', 'nop'])
        if periodic.get('passed') and native_ok:
            break
        if any(not x.get('passed') for x in basic.values()):
            raise RuntimeError('Native preflight has a recorded failed control')
        if time.monotonic() > until:
            raise RuntimeError('Preflight did not finish; no teacher started')
        time.sleep(10)
    state.update(phase='official_cloud_admission')
    save()
    call([sys.executable, str(F / 'check_docker_admission.py'), '--task', str(P / 'task'),
          '--images', str(P / 'images.json'), '--codex-home', '/ws/users/wcgu/new-codex-group/' + ACCOUNT,
          '--output', str(P / 'admission'), '--backend', 'aliyun',
          '--cloud-context', str(P / 'task/environment'), '--native-transport', 'responses-websocket'],
         'admission-supervisor.log')
    assert json.loads((P / 'admission/report.json').read_text())['passed']
    state.update(phase='six_hour_run_starting')
    save()
    call([sys.executable, str(ROOT / 'scripts/launch_run.py'), KEY, ACCOUNT], 'run-supervisor.log')
    state.update(phase='formal_run_returned')
    save()
except Exception as exc:
    state.update(phase='roll_failed', error=repr(exc), traceback=traceback.format_exc())
    save()
finally:
    # Keep an uncertain reservation if any owned learner lacks destruction proof.
    ledgers = list((P / 'admission/jobs').glob('**/aliyun-*.json'))
    ledgers += list((P / 'run-6h-001/jobs').glob('**/aliyun-*.json'))
    safe = all(not json.loads(p.read_text()).get('created') or json.loads(p.read_text()).get('destroyed')
               for p in ledgers)
    with (ROOT / 'model-reservations.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        registry = ROOT / 'model-reservations.json'
        s = json.loads(registry.read_text())
        if safe:
            lease = s['leases'].pop(TOKEN, None)
            s.setdefault('released', []).append({'lease': lease, 'reason': 'owned workers ended; all created learners destroyed'})
            dump(registry, s)
        state['owned_reservation_released'] = safe
        save()
