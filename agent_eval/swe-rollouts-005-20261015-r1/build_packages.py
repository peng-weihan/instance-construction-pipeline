"""Freeze authored packages and build uniquely owned pilot images."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import traceback

ROOT = Path('/ws/users/raymone/edgebench/swe-rollouts-005-20261015-r1')
SOURCE = ROOT.parent / 'swe-authoring-016-20261015-r1/jobs'
TASKS = ['01_openapi_streaming', '02_restler_recovery', '04_pytest_fixtures',
         '09_valkey_transactions', '14_tree_sitter_incremental']


def dump(path, obj):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def inventory(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('Unreviewed task symlink: ' + str(p))
        if p.is_file():
            result[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def build(key):
    out = ROOT / key
    out.mkdir(exist_ok=False)
    status = {'task': key, 'phase': 'freezing', 'model_runs_started': 0,
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save = lambda: dump(out / 'prepare-status.json', status)
    save()
    try:
        source = SOURCE / key / 'task'
        hashes = inventory(source)
        subprocess.run(['cp', '-a', '--reflink=auto', str(source), str(out / 'source-task')], check=True)
        assert hashes == inventory(source) == inventory(out / 'source-task')
        dump(out / 'source-freeze.json', {'source': str(source), 'file_hashes': hashes,
             'source_preserved': True, 'formal_acceptance': False})
        images = {}
        for side, context in [('agent', 'environment'), ('verifier', 'verifier')]:
            status.update(phase='building_' + side)
            save()
            tag = 'edge-raymone-swe-roll-r1-' + key.lower().replace('_', '-') + ':' + side
            command = ['docker', 'build', '--network', 'default' if key.startswith('14_') else 'none',
                       '--pull=false', '-t', tag, str(out / 'source-task' / context)]
            with (out / (side + '-build.log')).open('wb') as f:
                result = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, timeout=1800)
            if result.returncode:
                raise RuntimeError(side + ' build failed; see owned build log')
            image = subprocess.check_output(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}'], text=True).strip()
            images[side] = {'tag': tag, 'image_id': image, 'command': command}
            dump(out / 'images.json', images)
        status.update(phase='images_built', images=images)
        save()
    except Exception as exc:
        status.update(phase='preparation_failed', error=repr(exc), traceback=traceback.format_exc())
        save()
    print(json.dumps(status, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(build, TASKS))
