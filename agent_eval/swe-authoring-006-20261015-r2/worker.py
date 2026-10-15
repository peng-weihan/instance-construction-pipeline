"""One real native author; reserve only this batch's slot and clean its own group."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
JOB = next(x for x in json.loads((ROOT / 'launch-plan.json').read_text())['jobs'] if x['id'] == sys.argv[1])
D = Path(JOB['cwd'])


def ticks(pid):
    return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]


state = {**JOB, 'state': 'starting', 'worker_pid': os.getpid(), 'worker_start_ticks': ticks(os.getpid()),
         'phase': 'authoring_only', 'teacher_rollouts_started': 0}


def save(**values):
    state.update(values, updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    p = D / 'status.tmp.json'
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    p.replace(D / 'status.json')


def change(fn):
    n = JOB['account'].split('/')[-1]
    registry = ROOT / 'native-slots' / ('raymone' + n + '.json')
    with registry.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        s = json.loads(registry.read_text())
        result = fn(s)
        tmp = registry.with_suffix('.tmp')
        tmp.write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n')
        tmp.replace(registry)
        return result


def members(group):
    out = []
    for p in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = p.read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == group and fields[0] != 'Z':
                out.append(int(p.parent.name))
        except OSError:
            pass
    return out


child = None
leased = False
try:
    save()
    def reserve(s):
        assert s['outside_observed'] + len(s['leases']) < 10
        assert time.time() - s['observed_epoch'] < 120
        s['leases'][JOB['id']] = {'worker_pid': os.getpid(), 'worker_start_ticks': ticks(os.getpid())}
    change(reserve)
    leased = True
    home = Path(JOB['codex_home'])
    binary = home / 'bin/codex'
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == JOB['expected_cli_sha256']
    assert (home / 'auth.json').is_file() and (home / 'static-egress.json').is_file()
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(('OPENAI_', 'CODEX_', 'AZURE_', 'ANTHROPIC_', 'E2B_', 'TBSCI_E2B_')):
            env.pop(key, None)
    env.update(CODEX_HOME=str(home), PATH=str(home / 'bin') + ':' + env.get('PATH', '/usr/bin:/bin'),
        PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0',
        TMPDIR=str(D / 'tmp'), PIP_CACHE_DIR=str(D / '.cache/pip'), CARGO_HOME=str(D / '.cargo'),
        UV_CACHE_DIR=str(D / '.cache/uv'), XDG_CACHE_HOME=str(D / '.cache'), RUSTUP_AUTO_INSTALL='0',
        EDGEBENCH_AUTHOR_JOB=JOB['id'])
    (D / 'tmp').mkdir()
    command = [str(binary), 'exec', '--model', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="high"',
        '-c', 'features.multi_agent=false', '--dangerously-bypass-approvals-and-sandbox', '--skip-git-repo-check',
        '-C', str(D), '--json', '--output-last-message', str(D / 'final.md'), '-']
    with (D / 'prompt.md').open() as inp, (D / 'trajectory.jsonl').open('a') as out, (D / 'codex.stderr.log').open('a') as err:
        child = subprocess.Popen(command, stdin=inp, stdout=out, stderr=err, env=env, cwd=D, start_new_session=True)
        save(state='native_started', native_pid=child.pid, native_start_ticks=ticks(child.pid),
             selected_binary=str(binary), resolved_binary=str(binary.resolve()), native_started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        code = child.wait()
    if members(child.pid):
        os.killpg(child.pid, signal.SIGTERM)
        time.sleep(1)
    if members(child.pid):
        os.killpg(child.pid, signal.SIGKILL)
        time.sleep(.2)
    assert not members(child.pid)
    change(lambda s: s['leases'].pop(JOB['id']))
    leased = False
    save(state='author_returned', native_exit_code=code, result_file_exists=(D / 'AUTHOR_RESULT.json').exists(),
         capacity_released=True, native_finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
except Exception as exc:
    if leased and child is None:
        change(lambda s: s['leases'].pop(JOB['id']))
        leased = False
    save(state='launch_or_supervision_error', error_type=type(exc).__name__, error_message=str(exc)[:500], capacity_released=not leased)
    raise
