#!/usr/bin/env python3
"""Draft calibrated performance grader. Missing anchors invalidate; never invent a reward."""
import argparse,json,math,os,pathlib,resource,select,shutil,signal,statistics,subprocess,tempfile,time,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from workloads import CORRECTNESS,PERFORMANCE,expected
ROOT=pathlib.Path('/home/workspace/datafusion-sort-topk')
def isolated(uid, compile=False):
 def setup():
  os.setsid();resource.setrlimit(resource.RLIMIT_FSIZE,((1<<30,1<<30) if compile else (32<<20,32<<20)));resource.setrlimit(resource.RLIMIT_NOFILE,(256,256));resource.setrlimit(resource.RLIMIT_AS,(6<<30,6<<30))
  if uid is not None:os.setgroups([]);os.setgid(uid);os.setuid(uid)
 return setup
def execute(binary,spec,env,uid):
 with tempfile.TemporaryFile() as err:
  p=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,env=env,preexec_fn=isolated(uid))
  try:
   p.stdin.write(json.dumps(spec)+'\n');p.stdin.flush()
   deadline=time.monotonic()+30;ready=b''
   while not ready.endswith(b'\n') and len(ready)<32:
    remaining=deadline-time.monotonic()
    if remaining<=0 or not select.select([p.stdout],[],[],remaining)[0]:raise RuntimeError('candidate preparation timeout')
    chunk=os.read(p.stdout.fileno(),1)
    if not chunk:break
    ready+=chunk
   if ready!=b'READY\n':raise RuntimeError('candidate preparation/handshake failure')
   start=time.perf_counter();p.stdin.write('GO\n');p.stdin.flush()
   # collect starts only after GO; this timer is outside candidate code.
   p.stdin.close();deadline=time.monotonic()+30;chunks=[];size=0
   while True:
    remaining=deadline-time.monotonic()
    if remaining<=0 or not select.select([p.stdout],[],[],remaining)[0]:raise RuntimeError('candidate execution timeout')
    block=os.read(p.stdout.fileno(),65536)
    if not block:break
    size+=len(block)
    if size>8*1024*1024:raise RuntimeError('candidate output limit exceeded')
    chunks.append(block)
   p.wait(timeout=max(0.001,deadline-time.monotonic()));elapsed=time.perf_counter()-start
   result=json.loads(b''.join(chunks))
   return {'passed':p.returncode==0 and result=={'rows':expected(spec)},'elapsed_sec':elapsed,'exit_code':p.returncode,'output_bytes':size}
  except (ValueError,RuntimeError,subprocess.TimeoutExpired,KeyError) as e:return {'passed':False,'elapsed_sec':None,'error':str(e)}
  finally:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   p.wait()
def emit(out,result):
 out.mkdir(parents=True,exist_ok=True)
 for n in ['reward.txt','reward.json']:
  if (out/n).exists():(out/n).unlink()
 (out/'score.json').write_text(json.dumps(result,indent=2)+'\n')
 if result['valid']:(out/'reward.txt').write_text(f"{result['score']:.12f}\n")
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',default=str(ROOT/'submission'));ap.add_argument('--base',default='/opt/base');ap.add_argument('--anchors',default='/private/anchors.json');ap.add_argument('--output',default='/logs/verifier');ap.add_argument('--cargo',default='/usr/local/cargo/bin/cargo');ap.add_argument('--host-mode',action='store_true');args=ap.parse_args()
 out=pathlib.Path(args.output);result={'valid':False,'score':None,'pass_rate':None,'summary':'uninitialized','checks':[],'metrics':{}}
 try:
  anchors=json.loads(pathlib.Path(args.anchors).read_text())
  needed=[s['id'] for s in PERFORMANCE];baseline=anchors.get('baseline_medians_sec') or {}
  if not all(isinstance(baseline.get(k),(int,float)) and baseline[k]>0 for k in needed) or not isinstance(anchors.get('strong_reference_geomean_speedup'),(int,float)) or anchors['strong_reference_geomean_speedup']<=1:
   raise RuntimeError('hold_for_evidence: measured baseline and strong-reference anchors are missing; calibration is disabled')
  if not pathlib.Path(args.cargo).is_file():raise RuntimeError('promised Rust compiler/cargo absent')
  if not args.host_mode and os.geteuid()!=0:raise RuntimeError('root supervisor required to isolate compilation')
  candidate=pathlib.Path(args.candidate).resolve();base=pathlib.Path(args.base).resolve()
  if not (candidate/'Cargo.toml').is_file():
   result.update(valid=True,score=0.,pass_rate=0.,summary='candidate source workspace missing');emit(out,result);return 0
  uid=None if args.host_mode else 1000
  with tempfile.TemporaryDirectory(prefix='df-eval-') as td:
   t=pathlib.Path(td);os.chmod(t,0o755);merged=t/'source';shutil.copytree(base,merged,ignore=shutil.ignore_patterns('target','.git'))
   count=0
   for rel in ['datafusion/physical-plan/src/topk','datafusion/physical-plan/src/sorts']:
    for source in (candidate/rel).rglob('*.rs'):
     if source.is_symlink():raise ValueError('candidate symlink in allowed source tree')
     target=merged/source.relative_to(candidate);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);count+=1
   if count==0:
    result.update(valid=True,score=0.,pass_rate=0.,summary='no allowed Rust source submitted');emit(out,result);return 0
   bin_source=merged/'datafusion/physical-plan/src/bin/edgebench-sort.rs';bin_source.parent.mkdir(exist_ok=True);shutil.copyfile(pathlib.Path(__file__).with_name('edgebench-sort.rs'),bin_source)
   if uid is not None:
    os.chown(t,uid,uid)
    for p in [merged,*merged.rglob('*')]:os.chown(p,uid,uid)
   env={'PATH':str(pathlib.Path(args.cargo).parent)+':/usr/bin:/bin','CARGO_HOME':'/usr/local/cargo','CARGO_TARGET_DIR':str(t/'target'),'HOME':str(t),'CARGO_NET_OFFLINE':'true','LC_ALL':'C','RUSTUP_HOME':'/usr/local/rustup','RUSTUP_TOOLCHAIN':'1.99.0'}
   build_cmd=[args.cargo,'build','--offline','--release','--locked','-p','datafusion-physical-plan','--bin','edgebench-sort','--jobs','2']
   with tempfile.TemporaryFile() as log:
    p=subprocess.Popen(build_cmd,cwd=merged,env=env,stdout=log,stderr=log,preexec_fn=isolated(uid,compile=True))
    try:p.wait(timeout=1800)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    finally:
     try:os.killpg(p.pid,signal.SIGKILL)
     except ProcessLookupError:pass
    log.seek(0);result['build']={'command':build_cmd,'exit_code':p.returncode,'log':log.read(256000).decode(errors='replace')}
   if p.returncode:
    result.update(valid=True,score=0.,pass_rate=0.,summary='candidate compilation failed');emit(out,result);return 0
   binary=t/'target/release/edgebench-sort';checks=[];timings={}
   for s in CORRECTNESS:
    r=execute(binary,s,env,uid);checks.append({'name':s['id'],**r})
   if not all(c['passed'] for c in checks):
    result.update(valid=True,score=0.,pass_rate=sum(c['passed'] for c in checks)/len(checks),summary='correctness gate failed',checks=checks);emit(out,result);return 0
   for s in PERFORMANCE:
    runs=[execute(binary,s,env,uid) for _ in range(3)];checks.extend({'name':s['id'],**r} for r in runs)
    if not all(r['passed'] for r in runs):
     result.update(valid=True,score=0.,pass_rate=sum(c['passed'] for c in checks)/len(checks),summary='performance workload correctness gate failed',checks=checks);emit(out,result);return 0
    timings[s['id']]=statistics.median(r['elapsed_sec'] for r in runs)
   speedups={k:anchors['baseline_medians_sec'][k]/v for k,v in timings.items()};gm=math.exp(sum(math.log(v) for v in speedups.values())/len(speedups));upper=anchors['strong_reference_geomean_speedup'];score=max(0.,min(1.,math.log(gm)/math.log(upper)))
   result.update(valid=True,score=score,pass_rate=1.,summary='all correctness constraints passed',checks=checks,metrics={'candidate_medians_sec':timings,'speedup_by_workload':speedups,'geomean_speedup':gm,'strong_reference_anchor':upper});emit(out,result);return 0
 except Exception as e:
  result['summary']='infrastructure failure: '+repr(e);emit(out,result);return 2
if __name__=='__main__':raise SystemExit(main())
