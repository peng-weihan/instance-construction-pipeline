"""Authoritative grader: source snapshot -> unprivileged generation -> SDK execution.

Only this root orchestrator computes scores. All candidate Python runs as uid/gid 21001.
Root-owned HTTP observer holds request and wire-close evidence outside that process.
"""
from __future__ import annotations
import argparse
import email.parser
import email.policy
import hashlib
import http.server
import json
import os
from pathlib import Path
import resource
import selectors
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback

DEFAULT_SUBMISSION = '/home/workspace/openapi-streaming/submission'
DEFAULT_PRIVATE = '/opt/edgebench/private'


class InfrastructureError(RuntimeError):pass


def write_json(path, data):
    Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


class Runner:
    def __init__(self, spec, python):
        self.limits=spec['limits'];self.python=str(Path(python).absolute())
        self.uid=self.limits['candidate_uid'];self.gid=self.limits['candidate_gid']
        if os.geteuid()!=0:raise InfrastructureError('grader requires root to isolate uid')
    def child(self):
        os.setgroups([]);os.setgid(self.gid);os.setuid(self.uid)
        resource.setrlimit(resource.RLIMIT_CPU,(self.limits['cpu_sec'],self.limits['cpu_sec']))
        resource.setrlimit(resource.RLIMIT_AS,(self.limits['memory_bytes'],self.limits['memory_bytes']))
        resource.setrlimit(resource.RLIMIT_FSIZE,(self.limits['file_bytes'],self.limits['file_bytes']))
        resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
        os.umask(0o077)
    def run(self, args, cwd, timeout, marker=None):
        env={'PATH':str(Path(self.python).parent)+':/usr/local/bin:/usr/bin:/bin','HOME':str(cwd),'TMPDIR':str(cwd/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0','NO_COLOR':'1'}
        p=subprocess.Popen([self.python,*args],cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,preexec_fn=self.child,start_new_session=True)
        output=bytearray();sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
        deadline=time.monotonic()+timeout;timed_out=False
        try:
            while sel.get_map():
                if time.monotonic()>=deadline:timed_out=True;break
                for key,_ in sel.select(min(.1,max(0,deadline-time.monotonic()))):
                    chunk=os.read(key.fileobj.fileno(),65536)
                    if not chunk:sel.unregister(key.fileobj);continue
                    output.extend(chunk)
                    if marker and b'FIRST\n' in output:marker()
                    if len(output)>self.limits['output_bytes']:timed_out=True;break
                if timed_out:break
            if not timed_out:p.wait(timeout=max(.01,deadline-time.monotonic()))
        except subprocess.TimeoutExpired:timed_out=True
        finally:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait();sel.close();p.stdout.close()
        return {'returncode':p.returncode,'timeout':timed_out,'output':output[:self.limits['output_bytes']].decode(errors='replace')}


class Observer:
    def __init__(self, action, spec):
        self.action=action;self.spec=spec;self.events=[];self.requests=[];self.release=threading.Event();self.done=threading.Event();self.fault=None
        outer=self
        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def log_message(self,*args):pass
            def do_GET(self):self.respond()
            def do_POST(self):self.respond()
            def respond(self):
                try:
                    data=self.rfile.read(int(self.headers.get('Content-Length',0)))
                    outer.requests.append({'method':self.command,'path':self.path,'headers':dict((k.lower(),v) for k,v in self.headers.items()),'body':data.decode(errors='replace')})
                    if self.path=='/plain':
                        body=b'{"seq":9,"label":"plain"}'
                        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);self.wfile.flush();return
                    self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.send_header('Transfer-Encoding','chunked');self.end_headers()
                    def send(chunk):
                        self.wfile.write(('%x\r\n'%len(chunk)).encode()+chunk+b'\r\n');self.wfile.flush()
                    send(b'{"seq":1,"label":"first"}\n');outer.events.append('first_sent')
                    if outer.action=='network':
                        if not outer.release.wait(outer.spec['limits']['server_gate_sec']):
                            outer.events.append('gate_timeout');self.close_connection=True;return
                        outer.events.append('first_observed')
                    if outer.action=='network_early':
                        self.connection.settimeout(outer.spec['limits']['server_gate_sec'])
                        try:
                            if self.connection.recv(1)==b'':outer.events.append('peer_closed')
                        except ConnectionResetError:outer.events.append('peer_closed')
                        except TimeoutError:outer.events.append('close_timeout')
                        self.close_connection=True;outer.done.set();return
                    send(b'{"seq":2,"label":"second"}\n');self.wfile.write(b'0\r\n\r\n');self.wfile.flush();outer.events.append('end_sent')
                except (BrokenPipeError,ConnectionResetError):outer.events.append('peer_closed')
                except Exception as exc:outer.fault=repr(exc)
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def close(self):
        self.release.set();self.server.shutdown();self.server.server_close();self.thread.join()


def snapshot(source,dest,limits):
    """Do not follow symlinks or permit a captured source tree to escape its root."""
    if not source.is_dir():return 'missing submission directory'
    count=size=0
    for path in source.rglob('*'):
        relative=path.relative_to(source)
        if any(part in {'.git','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache'} for part in relative.parts):continue
        if path.is_symlink():return f'symlink rejected: {relative}'
        if path.is_dir():continue
        if not path.is_file():return f'nonregular source file: {relative}'
        count+=1;size+=path.stat().st_size
        if count>limits['snapshot_files'] or size>limits['snapshot_bytes']:return 'snapshot exceeds limits'
        target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    return None


def prepare_dirs(work,uid,gid):
    for path in [work,*work.rglob('*')]:
        if path.is_symlink():raise InfrastructureError('unexpected link in trusted work setup')
        os.chown(path,uid,gid);os.chmod(path,0o755 if path.is_dir() else 0o644)


def assert_check(condition, detail):
    return bool(condition), detail


def main(args):
    private=Path(args.private).resolve();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True);os.chmod(out,0o700)
    for name in ('reward.txt','reward.json'):(out/name).unlink(missing_ok=True)
    try:
        spec=json.loads((private/'score-spec.json').read_text());oracle=spec['oracle'];limits=spec['limits']
        # Trusted dependency preflight, independent of candidate import paths.
        import httpx, jinja2, pydantic, pytest, mypy, anyio, ruamel.yaml, syrupy, typer
        for filename in ['stream-contract.json','config.json','score-spec.json']:
            if not (private/filename).is_file():raise InfrastructureError('missing trusted '+filename)
        integrity=json.loads((private/'integrity.json').read_text())
        for filename,expected in integrity.items():
            path=private/filename
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise InfrastructureError('trusted asset integrity failure: '+filename)
        runner=Runner(spec,args.python)
        # Reference and reward paths must be inaccessible even if their names are known.
        permission=runner.run(['-I','-c','import os,sys; sys.exit(0 if not os.access(sys.argv[1],os.R_OK) and not os.access(sys.argv[2],os.W_OK) else 1)',str(private/'reference.patch'),str(out)],out.parent,limits['probe_wall_sec'])
        if permission['returncode']!=0:raise InfrastructureError('candidate can access private oracle/reward directory')
        if args.inject_infrastructure_failure:raise InfrastructureError('explicit author infrastructure fault control')
        work=Path(tempfile.mkdtemp(prefix='grade-',dir=args.scratch));os.chmod(work,0o755)
        source=work/'submission';source.mkdir();generated=work/'generated';generated.mkdir()
        error='submission root is a symlink' if Path(args.submission).is_symlink() else snapshot(Path(args.submission).resolve(),source,limits)
        # Only non-answer schema/config inputs enter the unprivileged workspace.
        for name in ['stream-contract.json','config.json']:shutil.copyfile(private/name,work/name)
        worker=Path(__file__).with_name('worker.py');shutil.copyfile(worker,work/'worker.py')
        native=private/'native'
        if not native.is_dir():raise InfrastructureError('missing authoritative native regression files')
        shutil.copytree(native,work/'native')
        # Root owns immutable harness/native tests/schema. Candidate may write only its source,
        # generated outputs and tmp, and cannot replace siblings because work itself is root-owned.
        for child in [source, generated, work/'tmp']:
            child.mkdir(exist_ok=True)
            prepare_dirs(child,runner.uid,runner.gid)
        dependency_probe=runner.run(['-I','-c','import httpx,jinja2,pydantic,pytest,mypy,anyio,ruamel.yaml,syrupy,typer; import importlib.metadata; importlib.metadata.version("openapi-python-client")'],work,limits['probe_wall_sec'])
        if dependency_probe['returncode']!=0:raise InfrastructureError('unprivileged dependency preflight failed: '+dependency_probe['output'])
        checks={name:{'name':name,'passed':False,'detail':'generation unavailable'} for g in spec['groups'].values() for name in g['checks']}
        diagnostics={};traces={}
        if error:diagnostics['snapshot_error']=error
        elif not (source/'openapi_python_client/__init__.py').is_file():diagnostics['snapshot_error']='missing generator source package'
        else:
            code='import sys,runpy; sys.path.insert(0,sys.argv.pop(1)); runpy.run_module("openapi_python_client",run_name="__main__")'
            compile_result=runner.run(['-I','-c',code,str(source),'generate','--path',str(work/'stream-contract.json'),'--config',str(work/'config.json'),'--meta','none','--output-path',str(generated/'stream_sdk'),'--overwrite'],work,limits['compile_wall_sec'])
            diagnostics['generation']=compile_result
            if compile_result['returncode']==0 and not compile_result['timeout']:
                for mode in ['sync','async']:
                    for action in ['records','numbers','early','empty','malformed','consumer','status','media','anonymous','json_body','multipart_body','optional','network','network_early']+(['cancel'] if mode=='async' else []):
                        observed=None
                        config={'action':action,'mode':mode}
                        if action in ['anonymous','json_body','multipart_body','optional','network','network_early']:
                            observed=Observer(action,spec);config.update(real_http=True,base_url=observed.url)
                        try:
                            run=runner.run(['-I',str(work/'worker.py'),str(generated),json.dumps(config)],work,limits['probe_wall_sec'],observed.release.set if observed else None)
                            result_lines=[line[7:] for line in run['output'].splitlines() if line.startswith('RESULT ')]
                            try:trace=json.loads(result_lines[-1]) if result_lines else {'fatal':run['output'][-3000:] or 'worker failed'}
                            except (ValueError,IndexError):trace={'fatal':'invalid worker output'}
                            if observed:
                                if action=='network_early':observed.done.wait(limits['server_gate_sec'])
                                trace['wire_requests']=observed.requests;trace['wire_events']=observed.events
                                if observed.fault:raise InfrastructureError('HTTP observer failed: '+observed.fault)
                            trace['timeout']=run['timeout'];traces[action+'_'+mode]=trace
                        finally:
                            if observed:observed.close()
                def put(name,passed,detail='semantic predicate failed'):
                    checks[name]={'name':name,'passed':bool(passed),'detail':'passed' if passed else detail}
                def good(t):return not t.get('fatal') and not t.get('timeout')
                def close_once(t):return t.get('after_exit',[]).count(['close'])==1 and t.get('client_closed') is False
                for mode in ['sync','async']:
                    t=traces['records_'+mode]
                    put('records_'+mode,good(t) and t.get('values')==oracle['record_values'] and t.get('after_construct')==0 and t.get('at_enter')==[] and t.get('after_first')==[['read',0],['read',1]])
                    put('types_'+mode,good(t) and 'Iterator' in t.get('annotation','') and 'Event' in t.get('annotation','') and 'Any' not in t.get('annotation',''))
                    n=traces['numbers_'+mode];put('numbers_'+mode,good(n) and n.get('values')==oracle['numbers'])
                    n=traces['network_'+mode];put('network_'+mode,good(n) and n.get('values')==oracle['network_values'] and n.get('wire_events')==['first_sent','first_observed','end_sent'])
                    for action in ['early','empty','malformed','consumer']:
                        t=traces[action+'_'+mode];expected={'early':None,'empty':None,'malformed':oracle['malformed_error'],'consumer':oracle['consumer_error']}[action]
                        passed=good(t) and close_once(t) and t.get('error')==expected
                        if action=='empty':passed=passed and t.get('after_exit')==[['close']] and t.get('values')==[]
                        elif action=='early':passed=passed and len(t.get('values',[]))==1 and t.get('after_exit')==[['read',0],['read',1],['close']]
                        else:passed=passed and len(t.get('values',[]))==1
                        put(action+'_'+mode,passed)
                    t=traces['network_early_'+mode];put('network_early_'+mode,good(t) and t.get('wire_events')==['first_sent','peer_closed'] and len(t.get('values',[]))==1 and not t.get('client_closed'))
                    t=traces['status_'+mode];put('status_'+mode,good(t) and close_once(t) and t.get('error')==oracle['status_error'] and t.get('status_code')==oracle['status_code'] and t.get('values')==[] and 'café' in t.get('error_content',''))
                    t=traces['media_'+mode];put('media_'+mode,good(t) and close_once(t) and t.get('error')==oracle['media_error'] and t.get('values')==[] and t.get('after_exit')==[['close']])
                    for action in ['anonymous','json_body','multipart_body','optional']:
                        t=traces[action+'_'+mode];requests=t.get('wire_requests',[])
                        passed=good(t) and len(requests)==2 and t.get('values')==oracle['network_values']
                        if len(requests)==2:
                            request=requests[0];headers=request['headers']
                            passed=passed and headers.get('x-session')=='stable' and t.get('default_headers',{}).get('authorization')==oracle['token']
                            passed=passed and (headers.get('authorization')==oracle['token'] if action=='optional' else 'authorization' not in headers)
                            passed=passed and 'authorization' not in requests[1]['headers']
                            if action in ('anonymous','json_body'):
                                try:passed=passed and json.loads(request['body'])==oracle['json_body'] and headers.get('content-type')=='application/json'
                                except ValueError:passed=False
                            if action=='multipart_body':
                                message=email.parser.BytesParser(policy=email.policy.default).parsebytes(('Content-Type: '+headers.get('content-type','')+'\r\nMIME-Version: 1.0\r\n\r\n'+request['body']).encode())
                                try:
                                    parts=list(message.iter_parts());fields=[[p.get_param('name',header='content-disposition'),p.get_payload(decode=True).decode()] for p in parts]
                                    filenames=[p.get_filename() for p in parts if p.get_filename()]
                                    passed=passed and fields==oracle['multipart_fields'] and filenames==oracle['multipart_filenames']
                                except (ValueError,UnicodeError,AttributeError):passed=False
                        put(action+'_'+mode,passed)
                    t=traces['records_'+mode];put('shared_'+mode,good(t) and close_once(t) and t.get('ordinary')==oracle['ordinary'] and len(t.get('requests',[]))==2 and t['requests'][0]['headers'].get('authorization')==oracle['token'] and t.get('default_headers',{}).get('authorization')==oracle['token'])
                put('security_signatures',all(' | ' not in traces['records_'+m].get('client_annotation','') and 'AuthenticatedClient' in traces['records_'+m].get('client_annotation','') and ' | ' in traces['optional_'+m].get('client_annotation','') for m in ['sync','async']))
                put('required_media_body',all(traces['json_body_'+m].get('body_required') is True for m in ['sync','async']))
                t=traces['cancel_async'];put('cancel_async',good(t) and close_once(t) and t.get('error')=='CancelledError' and len(t.get('values',[]))==1)
                code='import sys; sys.path.insert(0,sys.argv.pop(1)); import pytest; raise SystemExit(pytest.main(sys.argv[1:]))'
                native_result=runner.run(['-I','-c',code,str(source),'-q','--import-mode=importlib',*[str(work/'native'/p) for p in spec['native_tests']]],work,limits['native_wall_sec'])
                diagnostics['native_regressions']=native_result
                put('native_regressions',native_result['returncode']==0 and not native_result['timeout'],native_result['output'][-2000:])
        raw={name:{'passed':sum(checks[c]['passed'] for c in g['checks']),'total':len(g['checks'])} for name,g in spec['groups'].items()}
        score=sum(g['weight']*raw[name]['passed']/raw[name]['total'] for name,g in spec['groups'].items())
        passed=sum(c['passed'] for c in checks.values());total=len(checks)
        report={'valid':True,'score':score,'pass_rate':passed/total,'checks':list(checks.values()),'metrics':{'groups':raw,'passed':passed,'total':total},'diagnostics':diagnostics,'spec_sha256':hashlib.sha256((private/'score-spec.json').read_bytes()).hexdigest(),'summary':f'{passed}/{total} named checks passed'}
        write_json(out/'traces.json',traces);write_json(out/'score.json',report);(out/'reward.txt').write_text(f'{score:.17g}\n')
        shutil.rmtree(work)
        print(json.dumps({'valid':True,'score':score,'passed':passed,'total':total}));return 0
    except Exception as exc:
        for name in ['reward.txt','reward.json']:(out/name).unlink(missing_ok=True)
        write_json(out/'score.json',{'valid':False,'score':None,'summary':'infrastructure/reference error','error':repr(exc),'traceback':traceback.format_exc()})
        print('invalid grader: '+repr(exc),file=sys.stderr);return 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--submission',default=DEFAULT_SUBMISSION);parser.add_argument('--private',default=DEFAULT_PRIVATE);parser.add_argument('--output',default='/logs/verifier');parser.add_argument('--scratch',default='/tmp');parser.add_argument('--python',default='/opt/venv/bin/python');parser.add_argument('--inject-infrastructure-failure',action='store_true');raise SystemExit(main(parser.parse_args()))
