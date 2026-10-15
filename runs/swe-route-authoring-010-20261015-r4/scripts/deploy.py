"""Copy previous owned inputs without changing them or their build outputs."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
OLD = Path('/ws/users/raymone/edgebench/swe-route-authoring-005-20261015-r3')
EXCLUDE = {'target', 'build', '.cache', 'cache', 'tmp', '.venv', '.git', '.cargo',
           '__pycache__', 'local', 'experiments', 'runs', 'toolchains',
           'trajectory.jsonl', 'codex.stderr.log', 'supervisor.log', 'status.json',
           'auth.json', 'static-egress.json', '.env'}


def main():
    assert not (ROOT / 'deployment.json').exists()
    for name in ['guidance', 'controller']:
        shutil.copytree(OLD / name, ROOT / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'), symlinks=True)
    rows = []
    for job in json.loads((ROOT / 'launch-plan.json').read_text())['jobs']:
        if not job.get('source_job'):
            continue
        src = Path(job['source_job']); dst = Path(job['cwd']) / 'previous-input'
        assert src.parent == OLD / 'jobs'
        shutil.copytree(src, dst, symlinks=True,
                        ignore=lambda _d, names: [n for n in names if n in EXCLUDE])
        files, links = [], []
        for p in sorted(dst.rglob('*')):
            if p.is_symlink():
                links.append({'path': str(p.relative_to(dst)), 'target': os.readlink(p)})
            elif p.is_file():
                files.append({'path': str(p.relative_to(dst)), 'bytes': p.stat().st_size,
                              'sha256': hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()})
        receipt = {'source': str(src), 'copy': str(dst), 'excluded_names': sorted(EXCLUDE),
                   'files': files, 'symlinks_preserved_not_followed': links,
                   'historical_controls_only': True, 'source_modified': False}
        (dst.parent / 'previous-input-manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
        rows.append({'job': job['id'], 'files': len(files), 'bytes': sum(f['bytes'] for f in files), 'links': len(links)})
        print(json.dumps(rows[-1]), flush=True)
    (ROOT / 'deployment.json').write_text(json.dumps({'copied_inputs': rows, 'old_jobs_unchanged': True}, indent=2) + '\n')


if __name__ == '__main__':
    main()
