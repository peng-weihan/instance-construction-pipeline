"""Apply the user's full-score stop instruction only to explicitly named owned runs."""
from pathlib import Path
import datetime
import fcntl
import json
import sys
import time

BASE = Path('/ws/users/raymone/edgebench')
ROOT = BASE / 'swe-rollouts-005-20261015-r5'
TARGETS = ['20_libcst_project_migration', '21_coverage_context_merge']
sys.path.insert(0, str(ROOT / 'framework/sdk'))
from sandbox_smoke import connection, api_options
from e2b import Sandbox


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(p, default=None):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return default


def dump(p, d):
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(d, indent=2) + '\n'); tmp.replace(p)


def main():
    lock = (ROOT / 'authorized-full-score-stop.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    deadline = time.monotonic() + 23400
    outcomes = {}
    while time.monotonic() < deadline and len(outcomes) < len(TARGETS):
        for key in TARGETS:
            if key in outcomes:
                continue
            run = ROOT / key / 'run-6h-001'
            manifest = read(run / 'run-manifest.json', {})
            if manifest.get('status') == 'host_finished':
                outcomes[key] = {'status': 'host_already_finished', 'checked_utc': now()}
                continue
            h = read(run / 'evaluation/history.json', {})
            if h.get('best_valid') is not True or h.get('best_score') != 1.0:
                continue
            try:
                files = list((run / 'jobs/trial').glob('*/aliyun-*.json'))
                assert len(files) == 1
                cloud = read(files[0], {})
                if not cloud.get('created') or cloud.get('destroyed'):
                    outcomes[key] = {'status': 'sandbox_already_absent', 'checked_utc': now()}
                    continue
                receipt = run / 'user-requested-saturation-stop.json'
                record = {'reason': 'user_authorized_stop_full_score_runs_to_release_resources',
                          'requested_utc': now(), 'run': str(run), 'sandbox_id': cloud['sandbox_id'],
                          'best_score': 1.0, 'best_round': h.get('best_round'),
                          'formal_six_hour_completed': False, 'original_history_retained': True,
                          'result_classification': 'user_stopped_early_after_full_score'}
                dump(receipt, record)
                box = Sandbox.connect(cloud['sandbox_id'], **api_options(connection()))
                cmd = "/usr/bin/python3 -I -c \"import runpy,json; g=runpy.run_path('/opt/edgebench-runtime/learning_guardian.py'); print(json.dumps(g['freeze']('user_requested_full_score_stop')))\""
                response = box.commands.run(cmd, user='root', timeout=30)
                assert response.exit_code == 0
                stop = json.loads(response.stdout)
                assert not stop['surviving_learning_processes']
                record.update(trusted_stop=stop, stop_checked_utc=now())
                dump(receipt, record)
                outcomes[key] = {'status': 'full_score_learning_stopped', 'checked_utc': now(), 'receipt': str(receipt)}
            except Exception as exc:
                dump(ROOT / key / 'full-score-stop-last-error.json', {'utc': now(), 'error_type': type(exc).__name__})
        dump(ROOT / 'authorized-full-score-stop-status.json', {
            'updated_utc': now(), 'target_runs': [str(ROOT / k / 'run-6h-001') for k in TARGETS],
            'outcomes': outcomes, 'poll_seconds': 60, 'max_observation_seconds': 23400,
            'only_stop_condition': 'valid best_score exactly 1.0 under the unchanged grader',
            'other_scores_never_trigger_stop': True, 'source': 'user instruction to terminate full-score runs and release resources'})
        if len(outcomes) < len(TARGETS):
            time.sleep(60)


if __name__ == '__main__':
    main()
