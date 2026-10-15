#!/usr/bin/env python3
"""Trusted controller: never imports or compiles candidate code in this process."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(uid, limits):
    def setup():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CPU, (limits['cpu_seconds'], limits['cpu_seconds']))
        resource.setrlimit(resource.RLIMIT_AS, (limits['memory_bytes'], limits['memory_bytes']))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits['file_bytes'], limits['file_bytes']))
        resource.setrlimit(resource.RLIMIT_NOFILE, (limits['open_files'], limits['open_files']))
        resource.setrlimit(resource.RLIMIT_NPROC, (limits['processes'], limits['processes']))
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    return setup


def launch(command, cwd, uid, limits):
    return subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, bufsize=0,
                            env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(cwd),
                                 'PYTHONDONTWRITEBYTECODE':'1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1',
                                 'TMPDIR':str(cwd)},
                            preexec_fn=identity(uid, limits))


def kill_group(process):
    try: os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError: pass
    process.wait()


def snapshot(source, destination, spec):
    root=source/'httpx'
    if not root.is_dir() or root.is_symlink(): return False, 'Missing regular httpx directory'
    total=0
    for path in root.rglob('*'):
        if path.is_symlink(): return False, 'Symlinks are not submission artifacts'
        if path.is_dir(): continue
        if not path.is_file(): return False, 'Special submission file'
        if path.suffix != '.py' and path.name != 'py.typed': continue
        total += path.stat().st_size
        if total > spec['limits']['submission_bytes']: return False, 'Submission exceeds size limit'
        out=destination/path.relative_to(source)
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,out)
        out.chmod(0o644)
    return (destination/'httpx/__init__.py').is_file(), 'Snapshot copied'


def drain(process, timeout, limit):
    selector=selectors.DefaultSelector()
    selector.register(process.stdout,selectors.EVENT_READ)
    deadline=time.monotonic()+timeout
    total=0
    try:
        while time.monotonic()<deadline:
            ready=selector.select(max(0,deadline-time.monotonic()))
            if not ready: raise subprocess.TimeoutExpired(process.args,timeout)
            chunk=os.read(process.stdout.fileno(),65536)
            if not chunk:
                process.wait(timeout=max(0.001,deadline-time.monotonic()))
                return
            total+=len(chunk)
            if total>limit: raise subprocess.TimeoutExpired(process.args,timeout)
        raise subprocess.TimeoutExpired(process.args,timeout)
    finally: selector.close()


def compile_candidate(candidate, work, spec, python):
    work.chmod(0o777)
    # compileall runs as a build UID, with only a public, writable cache.
    process=launch([python,'-I','-X',f'pycache_prefix={work}/cache','-m','compileall','-q',str(candidate/'httpx')],
                   work,spec['identities']['compile_uid'],spec['limits'])
    try:
        drain(process,spec['limits']['compile_seconds'],spec['limits']['output_bytes'])
        return process.returncode==0
    except subprocess.TimeoutExpired: return False
    finally: kill_group(process)


def probe(case, candidate, worker, work, spec, python):
    observations={'entries':[], 'dispatches':[], 'closes':[], 'reads':[], 'yields':[], 'results':None}
    steps=case['steps']; current=-1
    read_indices=[0]*len(steps)
    observations['closes']=[0]*len(steps); observations['reads']=[0]*len(steps)
    process=launch([python,'-I',str(worker),str(candidate)],work,spec['identities']['run_uid'],spec['limits'])
    selector=selectors.DefaultSelector(); selector.register(process.stdout,selectors.EVENT_READ)
    data=b''; size=0
    deadline=time.monotonic()+spec['limits']['case_seconds']
    def answer(value): process.stdin.write((json.dumps(value)+'\n').encode()); process.stdin.flush()
    try:
        answer(case['config'])
        while time.monotonic()<deadline:
            ready=selector.select(max(0,deadline-time.monotonic()))
            if not ready: return observations,'Candidate timeout'
            chunk=os.read(process.stdout.fileno(),65536)
            if not chunk: return observations,'Candidate exited without result'
            size+=len(chunk)
            if size>spec['limits']['output_bytes']: return observations,'Candidate output limit'
            data+=chunk
            while b'\n' in data:
                line,data=data.split(b'\n',1)
                try: msg=json.loads(line)
                except (ValueError,TypeError): return observations,'Malformed candidate protocol'
                op=msg.get('op') if isinstance(msg,dict) else None
                reply={}
                if op=='result':
                    results=msg.get('results')
                    if not isinstance(results,list) or not results or any(not isinstance(r,dict) for r in results):
                        return observations,'Malformed candidate result list'
                    for result in results:
                        trace=result.get('trace')
                        if trace is None: continue
                        if not isinstance(trace,dict) or type(trace.get('attempts')) is not int or not 0<=trace['attempts']<=len(steps) or not isinstance(trace.get('events'),list):
                            return observations,'Malformed candidate trace'
                        for event in trace['events']:
                            if not isinstance(event,dict) or any(not isinstance(event.get(k),str) for k in ['kind','method','origin']) or type(event.get('attempt')) is not int:
                                return observations,'Malformed candidate event'
                    observations['results']=results
                    return observations,None
                if op=='enter':
                    if not isinstance(msg.get('method'),str) or not isinstance(msg.get('url'),str): return observations,'Malformed transport entry'
                    try:
                        parsed=urlsplit(msg['url'])
                        if not parsed.hostname or parsed.port is not None and not 0<=parsed.port<=65535: return observations,'Malformed transport URL'
                    except ValueError: return observations,'Malformed transport URL'
                    current+=1; observations['entries'].append(msg)
                    if current>=len(steps): return observations,'Unexpected extra physical dispatch'
                    reply={'error':steps[current].get('enter_error'),'partial':steps[current].get('partial',False)}
                elif op=='dispatch':
                    if not isinstance(msg.get('method'),str) or not isinstance(msg.get('url'),str) or not isinstance(msg.get('headers'),dict) or not isinstance(msg.get('body'),str): return observations,'Malformed transport dispatch'
                    observations['dispatches'].append(msg)
                    if current<0 or current>=len(steps): return observations,'Dispatch without entry'
                    step=steps[current]
                    reply={k:v for k,v in step.items() if k in ('status','headers','error')}
                    reply['id']=current
                elif op in ('read','close'):
                    ident=msg.get('id')
                    if type(ident) is not int or not 0<=ident<len(steps): return observations,'Invalid response identity'
                    step=steps[ident]
                    if op=='close':
                        observations['closes'][ident]+=1
                        reply={'cancel':step.get('cancel_close',False)}
                    else:
                        observations['reads'][ident]+=1
                        if step.get('read_error'): reply={'error':step['read_error']}
                        elif step.get('cancel_read'): reply={'cancel':True}
                        else:
                            chunks=step.get('chunks',[]); index=read_indices[ident]; read_indices[ident]+=1
                            reply={'chunk':chunks[index]} if index<len(chunks) else {'end':True}
                elif op=='body_yield': observations['yields'].append(msg)
                else: return observations,'Unknown candidate protocol operation'
                answer(reply)
        return observations,'Candidate timeout'
    except (BrokenPipeError,OSError,ValueError) as exc:
        return observations,'Candidate protocol failure: '+type(exc).__name__
    finally:
        selector.close(); kill_group(process)


def assess(case, obs, protocol_error):
    failures=[]
    if protocol_error: return [protocol_error]
    expected=case['expect']; results=obs['results']
    if not isinstance(results,list) or not results: return ['Missing result list']
    first=results[0]
    def check(name, actual, wanted):
        if actual!=wanted: failures.append(name)
    if 'validation' in expected:
        actual=[r.get('exception','ok') for r in results]
        check('constructor validation',actual,expected['validation'])
        if actual and actual[-1]=='ok': check('method normalization',results[-1].get('methods'),['PUT'])
        return failures
    for key in ['status','exception','history','next_url']:
        if key in expected: check(key,first.get(key),expected[key])
    if 'statuses' in expected: check('per-send results',[r.get('status') for r in results],expected['statuses'])
    check('physical attempts',len(obs['entries']),expected['attempts'])
    for key, actual in [('bodies',[d['body'] for d in obs['dispatches']]),
                        ('methods',[d['method'] for d in obs['dispatches']]),
                        ('paths',[urlsplit(d['url']).path for d in obs['dispatches']]),
                        ('authorization',[d['headers'].get('authorization') for d in obs['dispatches']]),
                        ('proxy_authorization',[d['headers'].get('proxy-authorization') for d in obs['dispatches']]),
                        ('closes',obs['closes']),('reads',obs['reads']),('yields',len(obs['yields']))]:
        if key in expected: check(key,actual,expected[key])
    if 'returned_closed' in expected: check('stream return ownership',first.get('closed'),expected['returned_closed'])
    traces=[r.get('trace') for r in results]
    if expected.get('no_trace'):
        check('disabled policy trace',traces,[None]*len(results))
        return failures
    # Event correctness is its own semantic dimension: a useful retry/body
    # implementation can earn those groups before implementing tracing.
    if case['group']!='events': return failures
    if any(not isinstance(t,dict) for t in traces): return failures+['Missing structured trace']
    check('trace attempts',[t.get('attempts') for t in traces],expected.get('trace_attempts',[expected['attempts']]))
    for result,trace in zip(results,traces):
        events=trace.get('events',[])
        if not events: failures.append('Empty trace'); continue
        check('terminal kind',events[-1].get('kind'),'error' if 'exception' in result else 'return')
        dispatches=[e for e in events if e.get('kind')=='dispatch']
        check('dispatch numbering',[e.get('attempt') for e in dispatches],list(range(1,trace['attempts']+1)))
        for event in events:
            if set(event)!={'kind','attempt','method','origin','status_code','error_type'}: failures.append('Event fields')
        if 'exception' in result: check('terminal error type',events[-1].get('error_type'),result['exception'])
        else: check('terminal status',events[-1].get('status_code'),result.get('status'))
    # Independent origin construction from externally observed transport URLs.
    def safe_origin(url):
        parsed=urlsplit(url)
        host=parsed.hostname
        if ':' in host: host='['+host+']'
        port={'http':80,'https':443}.get(parsed.scheme) if parsed.port is None else parsed.port
        return parsed.scheme+'://'+host+((':'+str(port)) if port else '')
    flat_events=[event for trace in traces for event in trace.get('events',[])]
    if not case['config'].get('concurrent'):
        actual_dispatch=[(e.get('method'),e.get('origin')) for e in flat_events if e.get('kind')=='dispatch']
        observed_dispatch=[(e['method'],safe_origin(e['url'])) for e in obs['entries']]
        check('externally observed dispatch events',actual_dispatch,observed_dispatch)
        response_statuses=[step['status'] for step in case['steps'][:len(obs['entries'])] if 'status' in step]
        check('externally observed response events',[e.get('status_code') for e in flat_events if e.get('kind')=='response'],response_statuses)
        errors=[step.get('enter_error',step.get('error')) for step in case['steps'][:len(obs['entries'])] if step.get('enter_error') or step.get('error')]
        check('externally observed transport errors',[e.get('error_type') for e in flat_events if e.get('kind')=='transport_error'],errors)
    events=traces[0].get('events',[])
    if 'kinds' in expected: check('event order',[e['kind'] for e in events],expected['kinds'])
    if 'origins' in expected: check('origins',[e['origin'] for e in events],expected['origins'])
    if expected.get('redacted'):
        serialized=json.dumps(traces)
        for secret in ['password','secret-path','secret-query','private-key','secret-cookie','private transport marker','private stream marker']:
            if secret in serialized: failures.append('Trace leaked sensitive content')
    return failures


def native_check(candidate, assets, work, spec, python):
    # All native assets are upstream public tests, not hidden extension answers.
    runner=assets/'native_runner.py'
    report=work/'native.xml'
    work.chmod(0o777)
    command=[python,'-I',str(runner),str(candidate),str(assets/'native'),str(report)]
    process=launch(command,work,spec['identities']['run_uid'],spec['limits'])
    try:
        drain(process,spec['limits']['native_seconds'],spec['limits']['output_bytes'])
        if not report.is_file(): return 0.0,{'error':'Native regression process did not produce a report'}
        tree=ET.parse(report)
        cases=tree.findall('.//testcase')
        observed={c.attrib['classname']+'.'+c.attrib['name']:c for c in cases}
        frozen=spec['native_members']
        passes=sum(name in observed and not any(observed[name].find(x) is not None for x in ('failure','error','skipped')) for name in frozen)
        fraction=passes/len(frozen)
        if process.returncode!=0 and passes==len(frozen):
            return 0.0,{'passed':passes,'total':len(frozen),'exit_code':process.returncode,'error':'Native session failed outside frozen cases'}
        return fraction,{'passed':passes,'total':len(frozen),'exit_code':process.returncode}
    except (subprocess.TimeoutExpired,ET.ParseError): return 0.0,{'error':'Native regression timeout or invalid report'}
    finally: kill_group(process)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--submission',default='/home/workspace/httpx/submission')
    parser.add_argument('--assets',default='/opt/judge')
    parser.add_argument('--public',default='/opt/probe')
    parser.add_argument('--output',default='/logs/verifier')
    parser.add_argument('--scratch',default='/tmp')
    parser.add_argument('--python',default='/opt/venv/bin/python')
    args=parser.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True);out.chmod(0o700)
    for name in ['reward.txt','reward.json']:
        (out/name).unlink(missing_ok=True)
    try:
        assets=Path(args.assets);public=Path(args.public)
        spec=json.loads((assets/'score-spec.json').read_text())
        cases=json.loads((assets/'private/cases.json').read_text())
        if [c['id'] for c in cases]!=spec['case_order']: raise RuntimeError('Frozen case membership mismatch')
        for path,digest in spec['trusted_hashes'].items():
            if hash_file(assets/path)!=digest: raise RuntimeError('Trusted asset integrity failure: '+path)
            if path.startswith('native/') and hash_file(public/path)!=digest: raise RuntimeError('Executed native asset integrity failure: '+path)
        if not Path(args.python).is_file() or not (public/'worker.py').is_file(): raise RuntimeError('Missing trusted interpreter or probe adapter')
        for path,digest in spec['public_hashes'].items():
            if hash_file(public/path)!=digest: raise RuntimeError('Trusted probe integrity failure: '+path)
        if hash_file(Path(__file__))!=spec['entrypoint_hashes']['grader.py']: raise RuntimeError('Grader integrity failure')
        for dep in spec['dependencies']:
            if importlib.util.find_spec(dep) is None: raise RuntimeError('Missing trusted dependency: '+dep)
        checks=[];groups={k:[] for k in spec['groups']}
        with tempfile.TemporaryDirectory(prefix='httpx-grade-',dir=args.scratch) as tmp:
            root=Path(tmp); root.chmod(0o755)
            candidate=root/'candidate';candidate.mkdir(mode=0o755)
            work=root/'run';work.mkdir(mode=0o777);work.chmod(0o777)
            ok,diagnostic=snapshot(Path(args.submission),candidate,spec)
            if ok: ok=compile_candidate(candidate,work,spec,args.python)
            for case in cases:
                if ok:
                    obs,err=probe(case,candidate,public/'worker.py',work,spec,args.python)
                    reasons=assess(case,obs,err)
                else: obs={};reasons=['Candidate missing or failed compilation: '+diagnostic]
                passed=not reasons
                checks.append({'name':case['id'],'group':case['group'],'passed':passed,'failures':reasons})
                groups[case['group']].append(int(passed))
            native_fraction,native_result=native_check(candidate,public,work,spec,args.python) if ok else (0.0,{'error':'Candidate failed compilation'})
            checks.append({'name':'native_regressions','group':'native_regressions','passed':native_fraction==1,'details':native_result})
            fractions={name:sum(v)/len(v) for name,v in groups.items() if v}
            fractions['native_regressions']=native_fraction
            score=sum(spec['groups'][name]['weight']*fractions[name] for name in spec['groups'])
            result={'valid':True,'score':score,'pass_rate':sum(c['passed'] for c in checks)/len(checks),
                    'checks':checks,'metrics':{'group_fractions':fractions,'native':native_result},
                    'summary':'Deterministic semantic groups and frozen upstream regressions'}
        (out/'score.json').write_text(json.dumps(result,indent=2)+'\n')
        (out/'reward.txt').write_text(str(score)+'\n')
        print(json.dumps({'valid':True,'score':score,'groups':fractions}))
    except Exception as exc:
        (out/'score.json').write_text(json.dumps({'valid':False,'score':None,'error':str(exc)},indent=2)+'\n')
        print('Verifier infrastructure error: '+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=='__main__': sys.exit(main())
