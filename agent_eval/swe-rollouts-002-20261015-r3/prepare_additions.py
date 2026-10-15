"""Prepare OpenAPI retry and HTTPX pilot without changing original task scores."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

OLD = Path('/ws/users/raymone/edgebench/swe-rollouts-005-20261015-r1')
ROOT = OLD.parent / 'swe-rollouts-002-20261015-r3'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}

def main():
    ROOT.mkdir(exist_ok=False)
    (ROOT / 'scripts').mkdir()
    (ROOT / 'activity').mkdir(mode=0o700)
    subprocess.run(['cp', '-a', '--reflink=auto', str(OLD / 'framework'), str(ROOT / 'framework')], check=True)
    framework = ROOT / 'framework'
    for name in ['edgebench_harbor/account_model_slots.py', 'edgebench_harbor/static_native.py']:
        p = framework / name
        assert str(OLD) in p.read_text()
        p.write_text(p.read_text().replace(str(OLD), str(ROOT)))
    for name in ['build_packages.py', 'prepare_cloud_and_controls.py', 'run_native_controls.py',
                 'launch_run.py', 'roll_worker.py', 'dispatch.py']:
        text = (OLD / 'scripts' / name).read_text().replace(str(OLD), str(ROOT))
        if name == 'build_packages.py':
            start = text.index('TASKS = ')
            end = text.index('\n\n', start)
            text = text[:start] + "TASKS = ['01_openapi_streaming', '03_httpx_transport']" + text[end:]
            text = text.replace('edge-raymone-swe-roll-r1-', 'edge-raymone-swe-roll-r3-')
        if name == 'prepare_cloud_and_controls.py':
            anchor = "        elif key.startswith('04_'):"
            assert text.count(anchor) == 1
            text = text.replace(anchor,
                "        elif key.startswith('03_'):\n"
                "            shutil.rmtree(submission)\n"
                "            shutil.copytree(source / 'authoring/controls/uncapped_replay', submission)\n" + anchor)
        (ROOT / 'scripts' / name).write_text(text)
    files = {p.relative_to(framework).as_posix(): sha(p) for p in framework.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.name != 'framework-version.json'}
    (framework / 'framework-version.json').write_text(json.dumps({'status': 'frozen',
        'kind': 'six_hour_engineering_pilot', 'formal_acceptance': False,
        'runtime_file_hashes': files,
        'runtime_tree_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        'source': str(OLD / 'framework'),
        'changed_components': ['edgebench_harbor/account_model_slots.py', 'edgebench_harbor/static_native.py'],
        'change_reason': 'Rebase own reservation and activity paths; no scoring/supervision change'}, indent=2)+'\n')
    key = '01_openapi_streaming'
    new = ROOT / key
    new.mkdir()
    for name in ['task', 'controls']:
        subprocess.run(['cp', '-a', '--reflink=auto', str(OLD / key / name), str(new / name)], check=True)
    for name in ['images.json', 'scorer-controls.json']:
        shutil.copy2(OLD / key / name, new / name)
    controls = json.loads((new / 'scorer-controls.json').read_text())
    assert controls['passed'] and inventory(new / 'task') == controls['task_hashes']
    (new / 'source-component-attestation.json').write_text(json.dumps({
        'task_unchanged_from': str(OLD / key / 'task'), 'task_hashes': controls['task_hashes'],
        'periodic_controls_reused_from': str(OLD / key / 'scorer-controls.json'),
        'native_controls': 'must run afresh; prior native startup had systemd timeout'}, indent=2)+'\n')
    sys.path.insert(0, str(ROOT / 'scripts'))
    from build_packages import build
    build('03_httpx_transport')
    from prepare_cloud_and_controls import prepare
    prepare('03_httpx_transport')
    for key in ['01_openapi_streaming', '03_httpx_transport']:
        with (ROOT / key / 'native-preparation.log').open('wb') as log:
            subprocess.run([sys.executable, str(ROOT / 'scripts/run_native_controls.py'), key],
                stdout=log, stderr=subprocess.STDOUT, check=True)
    print('BOTH_PREPARED_WITH_NATIVE_CONTROLS', flush=True)

if __name__ == '__main__':
    main()
