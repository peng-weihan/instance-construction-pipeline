"""Adapt an owned copy of the proven cloud supervisor; preserve shared code."""
from pathlib import Path
import hashlib
import json
import shutil

from build_packages import ROOT, dump

F = ROOT / 'framework'

selected = '''def selected_binding(home):
    home = Path(home).resolve(strict=True)
    allowed = {str(Path('/ws/users/wcgu/new-codex-group/raymone') / n): 'raymone/' + n
               for n in ['1', '2', '3']}
    if str(home) not in allowed:
        raise ValueError('Only the three user-specified identities are authorized')
    account = allowed[str(home)]
    lock = json.loads((Path(__file__).resolve().parents[1] / 'selected-account-bindings.json').read_text())[account]
    if not (home / 'auth.json').is_file() or digest(home / 'bin/codex') != EXPECTED_CLI_SHA256:
        raise ValueError('Selected CLI/login identity missing or changed')
    binding = json.loads((home / 'static-egress.json').read_text())
    if {k: binding.get(k) for k in lock} != lock:
        raise ValueError('Selected account proxy identity changed')
    if not binding.get('username') or not binding.get('password'):
        raise ValueError('Missing selected proxy authentication')
    return {'account': account, 'proxy_ip': binding['host'], 'http_port': binding['http_port'],
            'socks_port': binding['socks_port'], 'expected_exit_ip': binding['expected_exit_ip'],
            'cli_sha256': EXPECTED_CLI_SHA256,
            'daemon_execution_policy': 'official codex exec inline engine; no shared daemon copied'}


'''

path = F / 'edgebench_harbor/static_native.py'
text = path.read_text()
a, b = text.index('def selected_binding(home):'), text.index('def configure_native_transport(')
text = text[:a] + selected + text[b:]
text = text.replace("parent=Path('/ws/users/raymone/edgebench/remaining-three-001/science-pilot/activity')",
                    "parent=Path(" + repr(str(ROOT / 'activity')) + ")")
text = text.replace("'account':'raymone/1','operation'", "'account':os.environ['EDGEBENCH_SELECTED_ACCOUNT'],'operation'")
path.write_text(text)
locks = {}
for n in ['1', '2', '3']:
    value = json.loads((Path('/ws/users/wcgu/new-codex-group/raymone') / n / 'static-egress.json').read_text())
    locks['raymone/' + n] = {k: value[k] for k in ['host', 'http_port', 'socks_port', 'expected_exit_ip']}
dump(F / 'selected-account-bindings.json', locks)

# A batch-local reservation is held by the worker across its sequential admission
# and formal run. The cloud environment still checks actual deletion on every stop.
slots = '''"""Verify this learner's owned live-admission reservation; never edit shared registries."""
import json, os, time
from pathlib import Path
ROOT = Path(ROOT_LITERAL)
_BORROWED = None
def ticks(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
def acquire(registry=None):
    global _BORROWED
    if _BORROWED is not None: raise RuntimeError('Cannot share one slot between simultaneous learners')
    token = os.environ['EDGEBENCH_SLOT_TOKEN']
    state = json.loads((ROOT / 'model-reservations.json').read_text())
    lease = state['leases'][token]
    assert lease['account'] == os.environ['EDGEBENCH_SELECTED_ACCOUNT']
    assert ticks(lease['worker_pid']) == lease['worker_start_ticks']
    parent = os.getpid()
    found = False
    for _ in range(12):
        if parent == lease['worker_pid']: found = True; break
        parent = int(Path('/proc', str(parent), 'stat').read_text().rsplit(')', 1)[1].split()[1])
        if parent <= 1: break
    if not found: raise RuntimeError('Reservation must belong to this actual worker process')
    assert state['outside_counts'][lease['account']] + sum(x['account'] == lease['account'] for x in state['leases'].values()) <= 10
    _BORROWED = dict(lease)
    return dict(lease)
def release(lease, reason, registry=None):
    global _BORROWED
    if lease != _BORROWED: raise RuntimeError('Wrong learner lease')
    with (ROOT / 'activity' / ('release-' + os.environ['EDGEBENCH_SLOT_TOKEN'] + '.jsonl')).open('a') as f:
        f.write(json.dumps({'reason': reason, 'time': time.time(), 'harbor_pid': os.getpid()}) + '\\n')
    _BORROWED = None
'''.replace('ROOT_LITERAL', repr(str(ROOT)))
(F / 'edgebench_harbor/account_model_slots.py').write_text(slots)
path = F / 'edgebench_harbor/unleased_official_cloud_environment.py'
text = path.read_text().replace(':/usr/local/bin:/usr/bin:/bin', ':/opt/venv/bin:/usr/local/bin:/usr/bin:/bin')
path.write_text(text)
path = F / 'edgebench_harbor/official_cloud_supervision.py'
text = path.read_text().replace('from .restler_scorer import DockerScorer', 'from .package_scorer import DockerScorer')
path.write_text(text)
(ROOT / 'activity').mkdir(mode=0o700, exist_ok=True)

# Invoke the unchanged Harbor CLI from the frozen copy. Do not edit the shared
# executable, foreign guard, account configuration, or any other running framework.
(F / 'harbor_entry.py').write_text('from harbor.cli.main import app\nif __name__ == "__main__": app()\n')
path = F / 'check_docker_admission.py'
text = path.read_text().replace("[str(Path(sys.executable).parent/'harbor'),'run'",
                               "[sys.executable,str(ROOT/'harbor_entry.py'),'run'")
path.write_text(text)
official = F / 'harbor/agents/installed/codex.py'
assert hashlib.sha256(official.read_bytes()).hexdigest() == 'ee0ca8ec43617f3909d2195afe8f9e7cbd7313a8b3b558b01fde388f65b7c39c'
inventory = {p.relative_to(F).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name != 'framework-version.json'}
dump(F / 'framework-version.json', {'status': 'frozen', 'kind': 'six_hour_engineering_pilot',
    'formal_acceptance': False, 'runtime_file_hashes': inventory,
    'runtime_tree_sha256': hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest(),
    'official_codex_adapter_unchanged': True,
    'source': '/ws/users/raymone/edgebench/remaining-three-001/science-pilot/framework-r2'})
print('FROZEN', len(inventory), flush=True)
