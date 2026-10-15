#!/usr/bin/env python3
"""One authoritative scorer. Candidate Rust is always compiled/executed out of process."""
import argparse,collections,json,os,pathlib,resource,shutil,signal,subprocess,tempfile,time
GROUPS={'decode':1/7,'multiline':1/7,'format':1/7,'edit':1/7,'serialize':1/7,'diagnostic':1/7,'integration':1/7}
def run(cmd, *, cwd, env, input_text=None, timeout=120, uid=None):
 def limits():
  os.setsid()
  resource.setrlimit(resource.RLIMIT_CPU,(100,100))
  resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
  resource.setrlimit(resource.RLIMIT_NOFILE,(256,256))
  if uid is not None:
   os.setgroups([]);os.setgid(uid);os.setuid(uid)
 with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
  p=subprocess.Popen(cmd,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,preexec_fn=limits)
  timed=False
  try:p.communicate(input_text,timeout=timeout)
  except subprocess.TimeoutExpired:timed=True;os.killpg(p.pid,signal.SIGKILL);p.communicate()
  finally:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  out.seek(0);err.seek(0)
  return {'command':cmd,'exit_code':p.returncode,'timeout':timed,'stdout':out.read(256000).decode(errors='replace'),'stderr':err.read(256000).decode(errors='replace')}
def write(output,result):
 output.mkdir(parents=True,exist_ok=True)
 for name in ['reward.txt','reward.json']:
  p=output/name
  if p.exists():p.unlink()
 (output/'score.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if result['valid']:(output/'reward.txt').write_text(f"{result['score']:.12f}\n")
def main():
 a=argparse.ArgumentParser();a.add_argument('--candidate',default='/home/workspace/toml-string-recovery/submission');a.add_argument('--private',default='/private/cases.json');a.add_argument('--vendor',default='/opt/vendor');a.add_argument('--cargo',default='/usr/local/cargo/bin/cargo');a.add_argument('--output',default='/logs/verifier');a.add_argument('--host-mode',action='store_true');args=a.parse_args()
 output=pathlib.Path(args.output);candidate=pathlib.Path(args.candidate).resolve();here=pathlib.Path(__file__).resolve().parent
 result={'valid':False,'score':None,'pass_rate':None,'summary':'infrastructure not ready','checks':[],'metrics':{},'execution_context':'host_assistance_unisolated' if args.host_mode else 'linux_candidate_uid_1000'}
 try:
  if not pathlib.Path(args.cargo).is_file():raise RuntimeError('promised cargo missing')
  if not pathlib.Path(args.vendor,'serde_json').is_dir():raise RuntimeError('vendored dependency closure missing')
  cases=json.loads(pathlib.Path(args.private).read_text())
  assert len(cases)==35 and set(c['group'] for c in cases)==set(GROUPS)
  if not args.host_mode and (os.name!='posix' or os.geteuid()!=0):raise RuntimeError('judge must run as root to isolate candidate compilation')
  uid=None if args.host_mode else 1000
  if not (candidate/'Cargo.toml').is_file():
   result.update(valid=True,score=0.,pass_rate=0.,summary='submission workspace missing');write(output,result);return 0
  with tempfile.TemporaryDirectory(prefix='toml-eval-',dir=None if args.host_mode else '/tmp') as td:
   t=pathlib.Path(td);os.chmod(t,0o755)
   probe=t/'probe';shutil.copytree(here/'probe',probe)
   manifest=probe/'Cargo.toml';manifest.write_text(manifest.read_text().replace('/home/workspace/toml-string-recovery/submission',str(candidate)))
   cargo_home=t/'cargo-home';cargo_home.mkdir();(cargo_home/'config.toml').write_text('[source.crates-io]\nreplace-with="vendored-sources"\n[source.vendored-sources]\ndirectory='+json.dumps(str(pathlib.Path(args.vendor).resolve()))+'\n[net]\noffline=true\n')
   for p in [t,probe,cargo_home]:
    if uid is not None:os.chown(p,uid,uid)
   if uid is not None:
    for p in probe.rglob('*'):os.chown(p,uid,uid)
    os.chown(cargo_home/'config.toml',uid,uid)
   env={'PATH':str(pathlib.Path(args.cargo).resolve().parent)+':/usr/bin:/bin','CARGO_HOME':str(cargo_home),'CARGO_TARGET_DIR':str(t/'target'),'HOME':str(t),'CARGO_NET_OFFLINE':'true','LC_ALL':'C','RUST_BACKTRACE':'0','RUSTUP_HOME':'/usr/local/rustup','RUSTUP_TOOLCHAIN':'1.90.0'}
   build=run([args.cargo,'build','--offline','--locked','--manifest-path',str(manifest),'--jobs','2'],cwd=t,env=env,timeout=120,uid=uid)
   result['build']=build
   if build['exit_code'] or build['timeout']:
    result.update(valid=True,score=0.,pass_rate=0.,summary='candidate compilation failed or exceeded build budget');write(output,result);return 0
   binary=t/'target/debug/edgebench-toml-probe';passed=collections.Counter();totals=collections.Counter(c['group'] for c in cases);checks=[];raw=[]
   for c in cases:
    r=run([str(binary)],cwd=t,env=env,input_text=json.dumps(c['request'])+'\n',timeout=3,uid=uid)
    try:actual=json.loads(r['stdout']);ok=r['exit_code']==0 and not r['timeout'] and actual==c['expected']
    except (ValueError,TypeError):ok=False
    passed[c['group']]+=ok;checks.append({'name':c['id'],'group':c['group'],'passed':ok});raw.append({'id':c['id'],**r})
   score=sum(GROUPS[g]*passed[g]/totals[g] for g in GROUPS)
   result.update(valid=True,score=score,pass_rate=sum(passed.values())/len(cases),summary=f'{sum(passed.values())}/{len(cases)} behavioral cases passed',checks=checks,metrics={'group_passed':dict(passed),'group_total':dict(totals),'weights':GROUPS},runs=raw)
   write(output,result);return 0
 except Exception as e:
  result['summary']='infrastructure failure: '+repr(e);write(output,result);return 2
if __name__=='__main__':raise SystemExit(main())
