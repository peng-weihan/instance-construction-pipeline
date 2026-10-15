"""Single authoritative score entry. Compile AND execute as a separate UID."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import struct
from wire import Wire
import cases

HERE=Path(__file__).resolve().parent
SPEC=json.loads((HERE/'score-spec.json').read_text())
UID=SPEC['limits']['candidate_uid']
GID=UID
PYTHON=sys.executable

class CandidateFailure(Exception): pass
class InfrastructureFailure(Exception): pass


def restrict():
    os.setsid()
    os.setgroups([])
    os.setgid(GID)
    os.setuid(UID)
    lim=SPEC['limits']
    resource.setrlimit(resource.RLIMIT_CPU,(lim['process_cpu_seconds'],lim['process_cpu_seconds']))
    resource.setrlimit(resource.RLIMIT_AS,(lim['memory_bytes'],lim['memory_bytes']))
    resource.setrlimit(resource.RLIMIT_FSIZE,(lim['file_bytes'],lim['file_bytes']))
    resource.setrlimit(resource.RLIMIT_NOFILE,(lim['open_files'],lim['open_files']))
    resource.setrlimit(resource.RLIMIT_NPROC,(lim['processes'],lim['processes']))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def kill(proc):
    if proc is None: return
    try: os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError: pass
    proc.wait(timeout=3)


def run_as_candidate(argv,cwd,timeout):
    proc=subprocess.Popen(argv,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL,env={'PATH':'/usr/local/bin:/usr/bin:/bin','TMPDIR':str(cwd),
                          'PYTHONDONTWRITEBYTECODE':'1'},preexec_fn=restrict)
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return -999
    finally:
        kill(proc)


def snapshot(src,dst):
    if not src.is_dir() or not (src/'server.py').is_file():
        raise CandidateFailure('missing server.py')
    count=0
    total=0
    # No symlinks, devices, hidden build hooks or private paths cross the boundary.
    for path in src.rglob('*'):
        if path.is_symlink(): raise CandidateFailure('symlinks are not allowed in snapshot')
        if path.is_dir(): continue
        if not path.is_file(): raise CandidateFailure('nonregular snapshot file')
        if path.suffix != '.py': continue
        count+=1
        total+=path.stat().st_size
        if total>SPEC['limits']['source_bytes'] or count>SPEC['limits']['source_files']:
            raise CandidateFailure('snapshot size limit')
        out=dst/path.relative_to(src)
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,out)
    for path in [dst,*dst.rglob('*')]:
        os.chown(path,UID,GID)
        path.chmod(0o700 if path.is_dir() else 0o600)

class Harness:
    def __init__(self,source,root):
        self.root=Path(tempfile.mkdtemp(prefix='case-',dir=root))
        self.root.chmod(0o755)
        self.source=source
        self.data=self.root/'data'
        self.data.mkdir(mode=0o700)
        os.chown(self.data,UID,GID)
        # Socket path's parent must be writable by candidate, not the root case dir.
        self.runtime=self.root/'runtime'
        self.runtime.mkdir(mode=0o700)
        os.chown(self.runtime,UID,GID)
        self.path=self.runtime/'s'
        self.journal=self.data/'journal.ekv'
        self.proc=None
        self.diagnostic=(self.root/'stderr.log').open('wb')
        self.clients=[]
        try:
            self.start()
        except Exception:
            self.cleanup()
            raise

    def start(self,failpoint='none',expect_failure=False):
        if self.path.exists(): self.path.unlink()
        argv=[PYTHON,'-S','-s','-B',str(self.source/'server.py'),'--socket','s',
              '--data',str(self.data),'--failpoint',failpoint]
        self.proc=subprocess.Popen(argv,cwd=self.runtime,stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,stderr=self.diagnostic,
                    env={'PATH':'/usr/local/bin:/usr/bin:/bin','TMPDIR':str(self.runtime),
                         'PYTHONDONTWRITEBYTECODE':'1'},preexec_fn=restrict)
        if expect_failure:
            try: result=self.proc.wait(timeout=SPEC['limits']['startup_seconds'])
            except subprocess.TimeoutExpired: raise CandidateFailure('corrupt journal accepted')
            if result==0 or self.path.exists(): raise CandidateFailure('corrupt journal accepted')
            kill(self.proc)
            self.proc=None
            return
        deadline=time.monotonic()+SPEC['limits']['startup_seconds']
        while time.monotonic()<deadline:
            if self.proc.poll() is not None:
                raise CandidateFailure('service exited during startup: '+str(self.proc.returncode))
            if self.path.exists():
                try:
                    probe=Wire(self.path)
                    probe.close()
                    return
                except OSError: pass
            time.sleep(0.005)
        raise CandidateFailure('service startup timeout')

    def client(self):
        client=Wire(self.path)
        self.clients.append(client)
        return client

    def stop(self):
        for client in self.clients:
            try: client.close()
            except OSError: pass
        self.clients=[]
        kill(self.proc)
        self.proc=None

    def restart(self,failpoint='none'):
        self.stop()
        self.start(failpoint=failpoint)

    def expect_crash(self):
        try: result=self.proc.wait(timeout=SPEC['limits']['startup_seconds'])
        except subprocess.TimeoutExpired: raise CandidateFailure('failpoint did not terminate service')
        if result!=SPEC['crash_exit_code']: raise CandidateFailure('wrong crash status')
        self.stop()

    def cleanup(self):
        self.stop()
        self.diagnostic.close()
        shutil.rmtree(self.root)


def verify_assets():
    if os.geteuid()!=0: raise InfrastructureFailure('grader needs root for UID separation')
    expected={g['name']:g['checks'] for g in SPEC['groups']}
    if cases.GROUPS != expected: raise InfrastructureFailure('frozen group mismatch')
    for name,digest in SPEC['authoritative_assets'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest:
            raise InfrastructureFailure('authoritative asset checksum mismatch')


def grade(src,root):
    checks=[]
    build_ok=False
    tree=Path(tempfile.mkdtemp(prefix='snapshot-',dir=root))
    tree.chmod(0o755)
    source=tree/'source'
    source.mkdir()
    failure=None
    snapshot_digest=None
    try:
        try:
            snapshot(src,source)
            digest=hashlib.sha256()
            for path in sorted(source.rglob('*.py')):
                digest.update(str(path.relative_to(source)).encode()+b'\0'+path.read_bytes()+b'\0')
            snapshot_digest=digest.hexdigest()
            status=run_as_candidate([PYTHON,'-I','-S','-B','-m','compileall','-q',str(source)],source,
                                    SPEC['limits']['compile_seconds'])
            if status!=0: raise CandidateFailure('candidate compilation failed')
            # Compilation needs a writable build tree. Runtime sees root-owned
            # read-only sources, preventing cross-scenario self-modification.
            for path in [source,*source.rglob('*')]:
                os.chown(path,0,0)
                path.chmod(0o555 if path.is_dir() else 0o444)
            build_ok=True
        except CandidateFailure as exc:
            failure=str(exc)
        for group in SPEC['groups']:
            for name in group['checks']:
                passed=False
                detail=failure
                h=None
                if build_ok:
                    try:
                        h=Harness(source,root)
                        getattr(cases,name)(h)
                        passed=True
                        detail='passed'
                    except (CandidateFailure,AssertionError,EOFError,OSError,ValueError,KeyError,TypeError,struct.error,RecursionError) as exc:
                        detail=type(exc).__name__+(': '+str(exc) if isinstance(exc,CandidateFailure) else '')
                    finally:
                        if h is not None: h.cleanup()
                        # If constructor failed, its process must still be cleaned.
                        # Per-case watchdog processes are not reused across snapshots.
                checks.append({'name':name,'group':group['name'],'passed':passed,'detail':detail})
        score=0.0
        group_results={}
        for group in SPEC['groups']:
            items=[c for c in checks if c['group']==group['name']]
            n=sum(c['passed'] for c in items)
            group_results[group['name']]={'passed':n,'total':len(items),'fraction':n/len(items)}
            score+=group['weight']*n/len(items)
        return {'valid':True,'score':min(1.0,max(0.0,score)),
                'pass_rate':sum(c['passed'] for c in checks)/len(checks),
                'summary':'semantic checks completed','checks':checks,
                'metrics':{'compiled':build_ok,'groups':group_results,
                           'snapshot_sha256':snapshot_digest,
                           'raw_passed':sum(c['passed'] for c in checks),'raw_total':len(checks)}}
    finally:
        shutil.rmtree(tree)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--submission',type=Path,default=Path('/home/workspace/edgekv/submission'))
    p.add_argument('--output',type=Path,default=Path('/logs/verifier'))
    p.add_argument('--sandbox-root',type=Path,default=Path('/candidate-runs'))
    p.add_argument('--fault-infrastructure',action='store_true',help='author fault-classification probe')
    args=p.parse_args()
    HERE.chmod(0o700)
    args.output=args.output.resolve()
    args.sandbox_root=args.sandbox_root.resolve()
    args.output.mkdir(parents=True,exist_ok=True,mode=0o700)
    args.output.chmod(0o700)
    for name in ('reward.txt','reward.json'):
        (args.output/name).unlink(missing_ok=True)
    try:
        verify_assets()
        if args.fault_infrastructure: raise InfrastructureFailure('injected author infrastructure fault')
        args.sandbox_root.mkdir(parents=True,exist_ok=True,mode=0o755)
        # Known private file and actual reward destination must be inaccessible to
        # the SAME identity used for compilation and service execution.
        probe='import os,sys; paths=sys.argv[1:]; denied=[]\nfor p in paths:\n try:\n  f=open(p,"rb" if p!=paths[-1] else "wb");f.close();denied.append(False)\n except PermissionError: denied.append(True)\nassert all(denied)'
        boundary_status=run_as_candidate([PYTHON,'-I','-S','-c',probe,str(HERE/'cases.py'),str(args.output/'reward.txt')],
                            args.sandbox_root,SPEC['limits']['compile_seconds'])
        if boundary_status!=0:
            raise InfrastructureFailure('private/reward permission boundary failed: status '+str(boundary_status))
        result=grade(args.submission.resolve(),args.sandbox_root)
    except Exception as exc:
        result={'valid':False,'score':None,'checks':[],
                'summary':'infrastructure failure: '+type(exc).__name__+': '+str(exc)}
        (args.output/'score.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        return 2
    (args.output/'score.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'reward.txt').write_text(format(result['score'],'.17g')+'\n')
    print(json.dumps({'valid':result['valid'],'score':result['score'],'metrics':result['metrics']}))
    return 0

if __name__=='__main__': sys.exit(main())
