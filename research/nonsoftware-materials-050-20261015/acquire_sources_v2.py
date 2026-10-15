"""Acquire source excerpts using shallow blob-free Git metadata, avoiding API quota."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess

from acquire_sources import fetch, digest

ROOT = Path(__file__).resolve().parent


def git(*args, cwd=None):
    result = subprocess.run(['git', *args], cwd=cwd, capture_output=True,
        timeout=240, env=dict(os.environ, GIT_TERMINAL_PROMPT='0'))
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-1000:])
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--files', nargs='*', default=[])
    parser.add_argument('--list', default='')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        raise ValueError('invalid repository')
    if not re.fullmatch(r'[a-z0-9_]+', args.id):
        raise ValueError('invalid source id')
    base = ROOT / 'sources' / args.id
    base.mkdir(parents=True, exist_ok=True)
    pin = base / 'revision.json'
    metadata = base / 'git-metadata.git'
    if not pin.exists():
        if not metadata.exists():
            git('clone', '--bare', '--filter=blob:none', '--depth', '1',
                '--single-branch', '--no-tags',
                f'https://github.com/{args.repo}.git', str(metadata))
        revision = git('rev-parse', 'HEAD', cwd=metadata).decode().strip()
        if not re.fullmatch('[0-9a-f]{40}', revision):
            raise ValueError('invalid commit')
        pin.write_text(json.dumps({'repo':args.repo, 'revision':revision,
            'resolved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'metadata_method':'shallow bare git with blob:none'},indent=2)+'\n')
        (base/'commit-response.json').write_text(json.dumps({'sha':revision,
            'html_url':f'https://github.com/{args.repo}/commit/{revision}',
            'source':'git rev-parse HEAD'},indent=2)+'\n')
    identity = json.loads(pin.read_text())
    if identity['repo'] != args.repo:
        raise ValueError('repository mismatch')
    revision = identity['revision']
    treefile = base/'tree.json'
    if not treefile.exists():
        entries=[]
        for row in git('ls-tree','-r','-z',revision,cwd=metadata).split(b'\0'):
            if not row:
                continue
            attrs,path=row.split(b'\t',1)
            mode,kind,oid=attrs.decode().split()
            entries.append({'path':path.decode('utf-8'), 'mode':mode,
                            'type':kind, 'sha':oid})
        treefile.write_text(json.dumps({'sha':git('rev-parse',revision+'^{tree}',cwd=metadata).decode().strip(),
            'tree':entries,'truncated':False,'source':'git ls-tree -r -z'},ensure_ascii=False)+'\n')
    treebytes=treefile.read_bytes()
    tree=json.loads(treebytes)
    paths={entry['path'] for entry in tree['tree'] if entry['type']=='blob'}
    if args.list:
        matches=sorted(path for path in paths if re.search(args.list,path))
        print(json.dumps({'repo':args.repo,'revision':revision,
            'matching_paths':matches[:65], 'match_count':len(matches),
            'tree_truncated':False},indent=2))
        return
    basics=[path for path in paths if '/' not in path and re.match(
        r'(?i)^(readme(?:\..*)?|licen[sc]e(?:[-.].*)?|copying(?:\..*)?|notice(?:\..*)?)$',path)]
    old=base/'manifest.json'
    prior=json.loads(old.read_text()) if old.exists() else {}
    files={entry['path']:entry for entry in prior.get('files_acquired',[])}
    missing=[];errors=[]
    for path in sorted(set(basics+args.files)):
        if path.startswith('/') or '..' in Path(path).parts:
            raise ValueError('unsafe path')
        if path not in paths:
            missing.append(path);continue
        output=base/'files'/path
        try:
            content=output.read_bytes() if output.exists() else fetch(
                f'https://raw.githubusercontent.com/{args.repo}/{revision}/{path}')
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(content)
            files[path]={'path':path,'bytes':len(content),'sha256':digest(content),
                'url':f'https://github.com/{args.repo}/blob/{revision}/{path}'}
        except (RuntimeError,subprocess.TimeoutExpired) as exc:
            errors.append({'path':path,'error':str(exc)})
    manifest={**identity,'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'tree_manifest':{'path':'tree.json','sha256':digest(treebytes),
                         'truncated':False,'blob_count':len(paths)},
        'files_acquired':sorted(files.values(),key=lambda entry:entry['path']),
        'missing_requested_paths':missing,'fetch_errors':errors,
        'status':'source_excerpts_acquired_not_full_checkout',
        'runtime_verified':False,'task_constructed':False,
        'six_hour_difficulty_verified':False}
    old.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'id':args.id,'repo':args.repo,'revision':revision,
        'files':len(files),'missing':missing,'errors':errors},ensure_ascii=False))


if __name__=='__main__':
    main()
