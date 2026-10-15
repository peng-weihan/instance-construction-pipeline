#!/usr/bin/env python3
"""One frozen, group-weighted behavioral scorer; never imports candidate code."""
import argparse,collections,hashlib,json,os,pathlib,resource,signal,subprocess,sys,tempfile
TASK='wasm-profile'
def limit_candidate():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    # macOS rejects RLIMIT_AS lowering; host controls record this missing layer.
    if sys.platform=='linux':resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    if sys.platform=='linux' and os.geteuid()==0:
        os.setgroups([]);os.setgid(65534);os.setuid(65534)
def execute(entry,case):
    argv=[] if TASK=='wasm-profile' else case['argv']
    stdin=json.dumps(case['request'])+'\n' if TASK=='wasm-profile' else case['stdin']
    with tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
        p=subprocess.Popen([sys.executable,'-I',str(entry),*argv],cwd=entry.parent,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env={'PATH':'/usr/local/bin:/usr/bin:/bin','LANG':'C.UTF-8','HOME':'/tmp'},preexec_fn=limit_candidate)
        timeout=False
        try:p.communicate(stdin.encode(),timeout=3)
        except subprocess.TimeoutExpired:
            timeout=True;os.killpg(p.pid,signal.SIGKILL);p.communicate()
        finally:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        stdout.seek(0);stderr.seek(0)
        return {'stdout':stdout.read(1024*1024).decode('utf8',errors='replace'),'stderr':stderr.read(1024*1024).decode('utf8',errors='replace'),'exit':p.returncode,'timeout':timeout}
def equal(case,actual):
    if actual['timeout']:return False
    expected=case['expected']
    if TASK=='wasm-profile':
        try:return actual['exit']==0 and json.dumps(json.loads(actual['stdout']),sort_keys=True)==json.dumps(expected,sort_keys=True)
        except (ValueError,TypeError):return False
    if actual['exit']!=expected['exit'] or bool(actual['stderr'])!=expected['stderr_nonempty']:return False
    if '-r' in case['argv']:return actual['stdout']==expected['stdout']
    try:
        left=[json.loads(x) for x in actual['stdout'].splitlines()];right=[json.loads(x) for x in expected['stdout'].splitlines()]
        # JSON bool and numeric types must remain distinct, object order is irrelevant.
        def canonical(v):
            if isinstance(v,dict):return ('object',tuple((k,canonical(v[k])) for k in sorted(v)))
            if isinstance(v,list):return ('array',tuple(canonical(x) for x in v))
            return ('boolean',v) if isinstance(v,bool) else ('number',v) if isinstance(v,(float,int)) else (type(v).__name__,v)
        return canonical(left)==canonical(right)
    except ValueError:return False
def main():
    p=argparse.ArgumentParser();p.add_argument('--submission',type=pathlib.Path,default=pathlib.Path('/home/workspace/'+TASK+'/submission'));p.add_argument('--cases',type=pathlib.Path,default=pathlib.Path('/private/cases.json'));p.add_argument('--logs',type=pathlib.Path,default=pathlib.Path('/logs/verifier'));a=p.parse_args()
    a.logs.mkdir(parents=True,exist_ok=True)
    for old in ['reward.txt','reward.json']:(a.logs/old).unlink(missing_ok=True)
    try:
        raw=a.cases.read_bytes();digest=a.cases.with_suffix('.sha256').read_text().strip()
        if hashlib.sha256(raw).hexdigest()!=digest:raise RuntimeError('private fixture hash mismatch')
        cases=json.loads(raw);groups=collections.Counter(c['group'] for c in cases)
        if len(groups)!=8 or not cases:raise RuntimeError('invalid frozen groups')
        entry=(a.submission/'runner.py').resolve();checks=[];passed=collections.Counter()
        for c in cases:
            actual=execute(entry,c) if entry.is_file() else {'stdout':'','stderr':'runner.py missing','exit':127,'timeout':False}
            ok=equal(c,actual);passed[c['group']]+=int(ok)
            checks.append({'name':c['id'],'group':c['group'],'passed':ok,'actual':actual})
        score=sum(passed[g]/groups[g] for g in groups)/8
        report={'valid':True,'score':score,'pass_rate':sum(passed.values())/len(cases),'summary':f'{sum(passed.values())}/{len(cases)} behavior cases; equal weight across 8 groups','metrics':{'group_passed':dict(passed),'group_total':dict(groups),'candidate_uid_isolation':sys.platform=='linux' and os.geteuid()==0},'checks':checks}
        (a.logs/'score.json').write_text(json.dumps(report,indent=2)+'\n');(a.logs/'reward.txt').write_text(str(score)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
    except Exception as e:
        (a.logs/'score.json').write_text(json.dumps({'valid':False,'score':None,'summary':type(e).__name__+': '+str(e)})+'\n');raise
if __name__=='__main__':main()
