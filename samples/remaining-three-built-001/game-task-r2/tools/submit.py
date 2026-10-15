#!/usr/bin/env python3
"""Manual submission harness. No model launch; fresh offline judge per snapshot."""
import argparse,hashlib,json,math,shutil,subprocess,tempfile,time,tomllib,uuid
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--judge-image',required=True);ap.add_argument('--submission',required=True)
    ap.add_argument('--run-state',required=True)
    ap.add_argument('--record',required=True);ap.add_argument('--suite',choices=['public','feedback','audit'],default='feedback');a=ap.parse_args()
    contract=tomllib.loads((Path(__file__).resolve().parents[1]/'task.toml').read_text())
    src=Path(a.submission).resolve();record=Path(a.record);record.parent.mkdir(parents=True,exist_ok=True)
    previous=[json.loads(x) for x in record.read_text().splitlines()] if record.exists() else []
    state=json.loads(Path(a.run_state).read_text());t=time.time();start=state['started_unix']
    if t-start>state['agent_budget_seconds']:raise SystemExit('agent budget exhausted before snapshot')
    image_id=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',a.judge_image],text=True).strip()
    if previous and any(r['suite']!=a.suite or r['judge_image_id']!=image_id or r['run_id']!=state['run_id'] for r in previous):raise SystemExit('one curve must use the same run, suite and immutable judge image')
    with tempfile.TemporaryDirectory(prefix='edge-snapshot-') as tmp:
        snap=Path(tmp)/'submission';snap.mkdir();total=0
        for p in sorted(src.rglob('*')):
            if p.is_symlink():raise SystemExit('submission symlinks forbidden')
            if p.is_dir():continue
            if not p.is_file():raise SystemExit('only regular files allowed')
            total+=p.stat().st_size
            if total>100_000_000:raise SystemExit('snapshot byte limit exceeded')
            q=snap/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
        digest=hashlib.sha256()
        for p in sorted(snap.rglob('*')):
            if p.is_file():digest.update(str(p.relative_to(snap)).encode()+b'\0'+p.read_bytes())
        t=time.time()
        if t-start>state['agent_budget_seconds']:raise SystemExit('agent budget exhausted before snapshot was frozen')
        container='edge-submit-'+uuid.uuid4().hex
        cmd=['docker','run','--name',container,'--rm','--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=12g',
         '--cap-drop','ALL','--cap-add','SYS_ADMIN','--security-opt','seccomp=unconfined',
         '--security-opt','apparmor=unconfined','--pids-limit','512','--memory',str(contract['resources']['memory_mb'])+'m','--cpus',str(contract['resources']['cpus']),
         '--mount',f'type=bind,source={snap},target=/submission,readonly',image_id,
         '--submission','/submission','--suite',a.suite]
        try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=contract['verifier']['timeout_seconds'])
        except subprocess.TimeoutExpired:
            raise SystemExit(json.dumps({'status':'verifier_error','summary':'total grading wall-time budget exceeded; no numeric reward'}))
        finally:
            subprocess.run(['docker','rm','-f',container],capture_output=True,timeout=30)
    try:report=json.loads(r.stdout)
    except Exception:raise SystemExit('judge output was not one JSON object: '+r.stderr[-1000:])
    if r.returncode or report.get('status')!='scored':raise SystemExit(json.dumps(report))
    if not {'score','valid','checks','raw_metrics'}<=set(report):raise SystemExit('incomplete feedback schema')
    score=report['score']
    if type(score) not in (int,float) or not math.isfinite(score) or not 0<=score<=1 or type(report['valid'])!=bool:raise SystemExit('invalid score or validity flag')
    if not isinstance(report['checks'],list) or not report['checks'] or any(not isinstance(c,dict) or not isinstance(c.get('name'),str) or type(c.get('pass'))!=bool for c in report['checks']):raise SystemExit('invalid named checks')
    if not isinstance(report['raw_metrics'],dict):raise SystemExit('invalid raw metrics')
    if not report['valid'] and score!=0:raise SystemExit('invalid submission received nonzero score')
    entry={'run_id':state['run_id'],'run_start_unix':start,'submitted_at_seconds':t-start,
           'elapsed_interaction_seconds':time.time()-start,'grading_seconds':time.time()-t,
           'submission_sha256':digest.hexdigest(),'judge_image':a.judge_image,'judge_image_id':image_id,'suite':a.suite,'feedback':report}
    valid_scores=[x['feedback']['score'] for x in previous if x['feedback']['valid']]
    if report['valid']:valid_scores.append(report['score'])
    entry['best_score_so_far']=max(valid_scores,default=0)
    with record.open('a') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    print(json.dumps(entry,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
