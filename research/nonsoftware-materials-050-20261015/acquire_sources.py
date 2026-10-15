"""Acquire immutable primary-source excerpts; does not build or author tasks."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent


def fetch(url):
    result = subprocess.run(
        ['curl', '-sS', '-L', '--fail', '--retry', '1', '--connect-timeout', '10',
         '--max-time', '45', url], capture_output=True, timeout=100)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-500:])
    return result.stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--files', nargs='*', default=[])
    parser.add_argument('--list', default='')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        raise ValueError('expected owner/repo')
    if not re.fullmatch(r'[a-z0-9_]+', args.id):
        raise ValueError('invalid source id')
    dest = ROOT / 'sources' / args.id
    dest.mkdir(parents=True, exist_ok=True)
    pin = dest / 'revision.json'
    if not pin.exists():
        data = fetch('https://api.github.com/repos/' + args.repo + '/commits/HEAD')
        obj = json.loads(data)
        rev = obj['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', rev):
            raise ValueError('invalid commit')
        (dest / 'commit-response.json').write_bytes(data)
        pin.write_text(json.dumps({'repo': args.repo, 'revision': rev,
            'resolved_utc': dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2)+'\n')
    identity = json.loads(pin.read_text())
    if identity['repo'] != args.repo:
        raise ValueError('cached repository identity mismatch')
    rev = identity['revision']
    treefile = dest / 'tree.json'
    if not treefile.exists():
        treefile.write_bytes(fetch(f'https://api.github.com/repos/{args.repo}/git/trees/{rev}?recursive=1'))
    treedata = treefile.read_bytes()
    tree = json.loads(treedata)
    paths = {item['path'] for item in tree['tree'] if item['type'] == 'blob'}
    if args.list:
        hits = sorted(p for p in paths if re.search(args.list, p))
        print(json.dumps({'repo': args.repo, 'revision': rev,
            'tree_truncated': tree.get('truncated'), 'matching_paths': hits[:100]}, indent=2))
        return
    basics = [p for p in paths if '/' not in p and re.match(
        r'(?i)^(readme(?:\..*)?|licen[sc]e(?:[-.].*)?|copying(?:\..*)?|notice(?:\..*)?)$', p)]
    old = dest / 'manifest.json'
    prior = json.loads(old.read_text()) if old.exists() else {}
    acquired = {item['path']: item for item in prior.get('files_acquired', [])}
    missing = []
    errors = []
    for path in sorted(set(basics + args.files)):
        if path.startswith('/') or '..' in Path(path).parts:
            raise ValueError('unsafe path')
        if path not in paths:
            missing.append(path)
            continue
        output = dest / 'files' / path
        try:
            content = output.read_bytes() if output.exists() else fetch(
                f'https://raw.githubusercontent.com/{args.repo}/{rev}/{path}')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)
            acquired[path] = {'path': path, 'bytes': len(content),
                'sha256': digest(content),
                'url': f'https://github.com/{args.repo}/blob/{rev}/{path}'}
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            errors.append({'path': path, 'error': str(exc)})
    manifest = {**identity, 'retrieved_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'tree_manifest': {'path': 'tree.json', 'sha256': digest(treedata),
            'truncated': bool(tree.get('truncated')), 'blob_count': len(paths)},
        'files_acquired': sorted(acquired.values(), key=lambda x:x['path']),
        'missing_requested_paths': missing, 'fetch_errors': errors,
        'status': 'source_excerpts_acquired_not_full_checkout',
        'runtime_verified': False, 'task_constructed': False,
        'six_hour_difficulty_verified': False}
    old.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'id':args.id, 'repo':args.repo, 'revision':rev,
        'files':len(acquired), 'missing':missing, 'errors':errors}, ensure_ascii=False))


if __name__ == '__main__':
    main()
