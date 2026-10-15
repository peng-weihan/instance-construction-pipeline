"""Prepare an isolated retry; retain prior measurements and their real provenance."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess

SOURCE = Path('/ws/users/raymone/edgebench/swe-rollouts-005-20261015-r1')
ROOT = SOURCE.parent / 'swe-rollouts-003-20261015-r2'
KEYS = ['02_restler_recovery', '04_pytest_fixtures', '09_valkey_transactions']

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def inventory(root, exclude_cache=False):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Unexpected symlink: ' + str(path))
        if path.is_file() and not (exclude_cache and '__pycache__' in path.parts):
            result[path.relative_to(root).as_posix()] = sha(path)
    return result

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    ROOT.mkdir(exist_ok=False)
    (ROOT / 'scripts').mkdir()
    (ROOT / 'activity').mkdir(mode=0o700)
    subprocess.run(['cp', '-a', '--reflink=auto', str(SOURCE / 'framework'), str(ROOT / 'framework')], check=True)
    framework = ROOT / 'framework'
    before = inventory(framework, exclude_cache=True)
    changed = []
    for name in ['edgebench_harbor/account_model_slots.py', 'edgebench_harbor/static_native.py']:
        path = framework / name
        text = path.read_text()
        assert str(SOURCE) in text
        path.write_text(text.replace(str(SOURCE), str(ROOT)))
        changed.append(name)
    for name in ['build_packages.py', 'launch_run.py', 'roll_worker.py', 'dispatch.py']:
        text = (SOURCE / 'scripts' / name).read_text().replace(str(SOURCE), str(ROOT))
        if name == 'build_packages.py':
            begin = text.index('TASKS = ')
            end = text.index('\n\n', begin)
            text = text[:begin] + 'TASKS = ' + repr(KEYS) + text[end:]
        (ROOT / 'scripts' / name).write_text(text)
    evidence = {}
    for key in KEYS:
        old, new = SOURCE / key, ROOT / key
        new.mkdir()
        subprocess.run(['cp', '-a', '--reflink=auto', str(old / 'task'), str(new / 'task')], check=True)
        original = json.loads((old / 'scorer-controls.json').read_text())
        native = json.loads((old / 'native-controls/report.json').read_text())
        assert original['passed'] and native['passed']
        assert all(native['results'][role]['passed'] for role in ['oracle', 'nop', 'partial'])
        assert inventory(new / 'task') == inventory(old / 'task') == original['task_hashes']
        assert native['source_task_hashes'] == original['task_hashes']
        for name in ['images.json', 'scorer-controls.json']:
            shutil.copy2(old / name, new / name)
        (new / 'native-controls').mkdir()
        shutil.copy2(old / 'native-controls/report.json', new / 'native-controls/report.json')
        images = json.loads((new / 'images.json').read_text())
        for image in images.values():
            actual = subprocess.check_output(['docker', 'image', 'inspect', image['image_id'], '--format', '{{.Id}}'], text=True).strip()
            assert actual == image['image_id']
        evidence[key] = {'task_hashes': original['task_hashes'], 'controls_measured_in': str(old),
            'native_report_sha256': sha(old / 'native-controls/report.json'),
            'periodic_report_sha256': sha(old / 'scorer-controls.json'),
            'reused_measurements_not_new_runs': True}
    same = ['edgebench_harbor/package_scorer.py', 'edgebench_harbor/native_controls_runtime.py',
        'edgebench_harbor/official_cloud_supervision.py', 'edgebench_harbor/official_supervision.py',
        'sdk/aliyun_environment.py', 'harbor/agents/installed/codex.py']
    for name in same:
        assert sha(SOURCE / 'framework' / name) == sha(framework / name)
    files = {k: v for k, v in inventory(framework, exclude_cache=True).items() if k != 'framework-version.json'}
    dump(framework / 'framework-version.json', {'status': 'frozen',
        'kind': 'six_hour_engineering_pilot', 'formal_acceptance': False,
        'runtime_file_hashes': files,
        'runtime_tree_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        'source': str(SOURCE / 'framework'), 'changed_components': changed,
        'change_reason': 'Rebase own reservation and activity paths into a new retry directory'})
    dump(ROOT / 'source-component-attestation.json', {
        'prepared_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'prior_attempts_preserved': True, 'task_scoring_and_learning_supervision_unchanged': True,
        'unchanged_components': {name: sha(framework / name) for name in same},
        'changed_components': {name: {'before': before[name], 'after': sha(framework / name)} for name in changed},
        'tasks': evidence, 'model': 'gpt-6.1-sol', 'learning_budget_seconds': 21600,
        'evaluation_interval_seconds': 600, 'difficulty_early_stop': False})
    print(json.dumps({'prepared': str(ROOT), 'tasks': KEYS}))

if __name__ == '__main__':
    main()
