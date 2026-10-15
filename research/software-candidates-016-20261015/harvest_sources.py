"""Freeze primary documents/source evidence for sixteen candidate cards.

Does not construct tasks or start models. Git HEAD is resolved once, then raw
documents use that immutable SHA. Missing paths remain explicit evidence gaps.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parent
LICENSE_PATHS=['LICENSE','LICENSE.txt','LICENSE.md','COPYING','LICENSE-APACHE','LICENSE-MIT']


def fetch(url):
    result=subprocess.run(['curl','--fail','--silent','--show-error','--location',
        '--retry','3','--retry-delay','1','--connect-timeout','12','--max-time','45',url],
        capture_output=True,timeout=195)
    if result.returncode:
        if b'404' in result.stderr:
            raise urllib.error.HTTPError(url,404,'not found',None,None)
        raise RuntimeError(result.stderr.decode(errors='replace')[-700:])
    return result.stdout


def harvest(candidate):
    base=ROOT/'sources'/candidate['id'];base.mkdir(parents=True,exist_ok=True)
    revision=candidate.get('revision')
    cached=base/'revision.json'
    if not revision and cached.exists():
        revision=json.loads(cached.read_text())['revision']
    if not revision and (base/'manifest.json').exists():
        revision=json.loads((base/'manifest.json').read_text())['revision']
    if not revision:
        revision=json.loads(fetch('https://api.github.com/repos/'+candidate['repo']+'/commits/HEAD'))['sha']
    assert len(revision)==40 and all(x in '0123456789abcdef' for x in revision)
    cached.write_text(json.dumps({'revision':revision})+'\n')
    successes=[];missing=[]
    for path in candidate['files']+LICENSE_PATHS:
        url=f"https://raw.githubusercontent.com/{candidate['repo']}/{revision}/{path}"
        try:
            destination=base/'files'/path
            content=destination.read_bytes() if destination.exists() else fetch(url)
        except urllib.error.HTTPError as error:
            if error.code==404:
                missing.append(path);continue
            raise
        destination=base/'files'/path
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(content)
        successes.append({'path':path,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'url':f"https://github.com/{candidate['repo']}/blob/{revision}/{path}"})
    result={**candidate,'revision':revision,'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files_acquired':successes,'missing_paths':missing,'runtime_validation':False,'six_hour_difficulty_verified':False}
    (base/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


if __name__=='__main__':
    plan=json.loads((ROOT/'plan.json').read_text());results=[];failures=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(harvest,c):c for c in plan['candidates']}
        for future in as_completed(futures):
            candidate=futures[future]
            try:
                result=future.result();results.append(result)
                print(json.dumps({'id':result['id'],'revision':result['revision'],'acquired':len(result['files_acquired']),'missing':result['missing_paths']},ensure_ascii=False),flush=True)
            except Exception as error:
                failures.append({'id':candidate['id'],'error':str(error)})
                print(json.dumps(failures[-1]),flush=True)
    results.sort(key=lambda r:r['id'])
    (ROOT/'source-manifests.json').write_text(json.dumps({'candidates':results,'failures':failures},ensure_ascii=False,indent=2)+'\n')
