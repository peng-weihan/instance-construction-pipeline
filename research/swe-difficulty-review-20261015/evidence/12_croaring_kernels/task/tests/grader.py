#!/usr/bin/env python3
"""One authority for native reward and structured score. Root judge only."""
import argparse,ctypes,hashlib,struct,importlib.util,json,os,pathlib,resource,shutil,signal,subprocess,sys,tempfile,time
P=argparse.ArgumentParser();P.add_argument('--root',default='/opt');P.add_argument('--submission',default='/home/workspace/croaring/submission');P.add_argument('--logs',default='/logs/verifier');P.add_argument('--scratch',default='/home/workspace/croaring/judge-work');P.add_argument('--split',choices=['feedback','author_audit'],default='feedback');args=P.parse_args()
root=pathlib.Path(args.root).resolve();private=root/'private';pub=root/'public';logs=pathlib.Path(args.logs).resolve();logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700)
for name in ['reward.txt','reward.json']:(logs/name).unlink(missing_ok=True)
class CandidateFailure(Exception):pass

def finish(valid,checks,metrics,reason=None):
    score=None
    if valid:
        groups=spec['groups'];passed_native=next((x['passed'] for x in checks if x['name']=='native_regressions'),False)
        score=0.0
        if passed_native:
            for group,weight in groups.items():
                groupchecks=[x for x in checks if x.get('group')==group]
                score+=weight*sum(x['passed'] for x in groupchecks)/len(groupchecks)
        score=min(1.0,max(0.0,score))
    result={'valid':valid,'score':score,'pass_rate':sum(x['passed'] for x in checks)/len(checks) if checks else 0,'checks':checks,'metrics':metrics,'summary':reason or 'Frozen semantic score; performance contribution disabled.'}
    (logs/'score.json').write_text(json.dumps(result,indent=2))
    if valid:(logs/'reward.txt').write_text(format(score,'.17g')+'\n')
    print(json.dumps({k:result[k] for k in ['valid','score','summary']}))
    return 0 if valid else 2

def execute(cmd,cwd,timeout,stdin=None,untrusted=True):
    def restrict():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        if untrusted:
            resource.setrlimit(resource.RLIMIT_CPU,(limits['cpu_seconds'],limits['cpu_seconds']))
            resource.setrlimit(resource.RLIMIT_AS,(limits['memory_bytes'],limits['memory_bytes']))
            resource.setrlimit(resource.RLIMIT_FSIZE,(limits['file_bytes'],limits['file_bytes']))
            os.setgroups([]);os.setgid(limits['candidate_uid']);os.setuid(limits['candidate_uid'])
            if ctypes.CDLL(None).prctl(38,1,0,0,0):os._exit(126)
    env={'PATH':'/usr/local/bin:/usr/bin:/bin','LC_ALL':'C','HOME':str(cwd),'TMPDIR':str(cwd),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    with tempfile.TemporaryFile(dir=logs) as output:
        p=subprocess.Popen(cmd,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=output,stderr=subprocess.STDOUT,preexec_fn=restrict)
        try:
            p.communicate(stdin.encode() if stdin is not None else None,timeout=timeout)
            rc=p.returncode
        except subprocess.TimeoutExpired:
            rc=-signal.SIGKILL
        finally:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait()
        output.seek(0);data=output.read(limits['output_bytes']+1)
        if len(data)>limits['output_bytes']:return -1,'candidate output limit exceeded'
        return rc,data.decode('utf-8','replace')

def snapshot(source,dest):
    total=count=0
    for top in ['src','include']:
        src=source/top
        if src.is_symlink() or not src.is_dir():raise CandidateFailure('missing or symlink source directory')
        for dp,dns,fns in os.walk(src,followlinks=False):
            for dn in dns:
                if (pathlib.Path(dp)/dn).is_symlink():raise CandidateFailure('symlink in snapshot')
            for name in fns:
                f=pathlib.Path(dp)/name
                if f.is_symlink() or not f.is_file():raise CandidateFailure('non-regular source')
                count+=1;total+=f.stat().st_size
                if total>limits['snapshot_bytes'] or count>limits['source_files']:raise CandidateFailure('source snapshot limit')
                rel=f.relative_to(source);out=dest/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,out);out.chmod(0o644)
    return {'snapshot_bytes':total,'snapshot_files':count}

def main():
    global spec,limits
    spec=json.loads((private/'score-spec.json').read_text());limits=spec['limits']
    if os.geteuid()!=0:raise RuntimeError('verifier requires root to isolate compile and run')
    for tool in ['gcc','ar','python3']:
        if not shutil.which(tool):raise RuntimeError('missing trusted tool '+tool)
    # Integrity errors and missing reference are infrastructure faults, never 0.
    for rel,digest in json.loads((private/'integrity.json').read_text()).items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest:raise RuntimeError('trusted asset hash mismatch: '+rel)
    loader=importlib.util.spec_from_file_location('private_oracle',private/'oracle.py');oracle=importlib.util.module_from_spec(loader);loader.loader.exec_module(oracle)
    cases=oracle.cases(spec,args.split)
    expected_ids=json.loads((private/'case-membership.json').read_text())[args.split]
    if list(cases)!=expected_ids:raise RuntimeError('case membership drift')
    sanity=([set(),{0,65535,(1<<32)-1},{1,65535}],[(0,1,2,0,1<<32)],0)
    rc,output=execute([str(private/'sanity/runner')],private,limits['case_seconds'],oracle.payload(sanity),False)
    if rc or not oracle.judge(sanity,output)[0]:raise RuntimeError('trusted unmodified baseline sanity failed')
    scratch=pathlib.Path(args.scratch).resolve();scratch.mkdir(parents=True,exist_ok=True);scratch.chmod(0o755)
    work=pathlib.Path(tempfile.mkdtemp(prefix='snapshot-',dir=scratch));work.chmod(0o755)
    build=work/'build';build.mkdir();os.chown(build,limits['candidate_uid'],limits['candidate_uid']);build.chmod(0o700)
    source=work/'source';source.mkdir();metrics={'performance_enabled':False,'performance_score':None,'split':args.split};checks=[]
    try:
        metrics.update(snapshot(pathlib.Path(args.submission).resolve(),source))
        for profile in ['native','scalar']:
            out=build/profile
            cmd=['/usr/local/bin/python3' if pathlib.Path('/usr/local/bin/python3').exists() else '/usr/bin/python3','-I',str(pub/'build.py'),str(source),str(out)]
            if profile=='scalar':cmd+=['--scalar']
            start=time.monotonic();rc,msg=execute(cmd,build,limits['compile_seconds']);metrics[profile+'_compile_seconds']=time.monotonic()-start
            (logs/(profile+'-compile.log')).write_text(msg)
            checks.append({'name':profile+'_compile','passed':rc==0})
            if rc:raise CandidateFailure(profile+' compilation failed or timed out')
            if profile=='native':
                rc,msg=execute([cmd[0],'-I',str(pub/'native.py'),str(source),str(out)],build,limits['native_seconds']);(logs/'native-regressions.log').write_text(msg)
                checks.append({'name':'native_regressions','passed':rc==0})
            for cid,case in cases.items():
                rc,msg=execute([str(out/'runner')],build,limits['case_seconds'],oracle.payload(case))
                passed,why=False,'crash, timeout or output budget'
                if rc==0:
                    try:passed,why=oracle.judge(case,msg)
                    except (ValueError,IndexError,OverflowError,struct.error) as err:why='malformed candidate output: '+type(err).__name__
                checks.append({'name':profile+'/'+cid,'group':cid.split('/')[0],'passed':passed,'detail':why})
        metrics['semantic_cases']=len(cases)*2
        return finish(True,checks,metrics)
    except CandidateFailure as err:
        checks.append({'name':'candidate_failure','passed':False,'detail':str(err)})
        # A partially compiled candidate has no semantic credit; native gate
        # deliberately fails rather than dividing by checks that happened to run.
        checks=[c for c in checks if c['name']!='native_regressions']+[{'name':'native_regressions','passed':False}]
        return finish(True,checks,metrics,str(err))
    finally:
        # All subprocess groups are already dead before removing their directory.
        shutil.rmtree(work)

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as err:
        # Includes missing/corrupt private assets and trusted runner failures.
        (logs/'score.json').write_text(json.dumps({'valid':False,'score':None,'checks':[],'metrics':{},'summary':'infrastructure/reference error: '+str(err)},indent=2))
        for name in ['reward.txt','reward.json']:(logs/name).unlink(missing_ok=True)
        print('infrastructure/reference error: '+str(err),file=sys.stderr);sys.exit(2)
