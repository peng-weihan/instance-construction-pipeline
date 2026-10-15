"""Verify the frozen archive, extract into a fresh directory and run Docker smoke.

Upload this file and restler-007-smoke.tar.gz to the personal Linux directory.
This entry does not invoke a model or claim Harbor acceptance.
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tarfile
from pathlib import Path


ARCHIVE_SHA256 = 'ba212c47aeb1d0a31a6cd6c763b272db5a2698a9e1f49dd6ca8107574b80be3f'


def unpack(archive, destination):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('archive digest mismatch')
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as stream:
        stream.extractall(destination, filter='data')
    task = destination / 'restler_resilient_execution'
    manifest = json.loads((task / 'files.sha256.json').read_text())
    expected = {entry['path'] for entry in manifest}
    actual = {str(p.relative_to(task)) for p in task.rglob('*') if p.is_file()}
    if actual != expected | {'files.sha256.json'}:
        raise ValueError('task file inventory mismatch')
    for entry in manifest:
        p = task / entry['path']
        if p.stat().st_size != entry['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('task digest mismatch: ' + entry['path'])
    return task, len(manifest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.run_root.resolve()
    if platform.system() != 'Linux' or not root.is_relative_to('/ws/users/raymone'):
        raise SystemExit('Execute only in the personal /ws/users/raymone subtree on Linux.')
    task, count = unpack(args.archive.resolve(), root)
    (root / 'transfer_verified.json').write_text(json.dumps({
        'archive_sha256': ARCHIVE_SHA256, 'task_files_verified': count,
        'model_runs': 0, 'six_hour_runs': 0, 'accepted': False,
    }, indent=2) + '\n')
    return subprocess.call([sys.executable, str(root / 'smoke.py'),
                            '--task', str(task), '--output', str(root / 'results')])


if __name__ == '__main__':
    sys.exit(main())
