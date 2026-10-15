"""Trusted controller helpers. Candidate code is only executed by bubblewrap.

The judge image and the agent image have separate build contexts. Inside the judge,
only /work and public system/runtime files are visible to an untrusted worker.
No fallback to unsandboxed execution is permitted.
"""
import json, math, os, resource, selectors, shutil, signal, subprocess, tempfile, time
from pathlib import Path

class SubmissionError(Exception): pass
class InfrastructureError(Exception): pass

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private'
PUBLIC = ROOT / 'public'

def read_json(p):
    return json.loads(Path(p).read_text())

def scoring_constants():
    """Use the shipped machine-readable contract as the grading authority."""
    return read_json(PUBLIC / 'scoring_metadata.json')['constants']

def check(name, passed, diagnostic=''):
    return {'name': name, 'pass': bool(passed), 'summary': str(diagnostic)[:600]}

def result(score, checks, metrics=None, valid=True):
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise InfrastructureError('nonfinite or unbounded score')
    return {'status':'scored', 'score':score, 'valid':bool(valid),
            'checks':checks, 'raw_metrics':metrics or {},
            'summary':f'{sum(x["pass"] for x in checks)}/{len(checks)} named checks passed'}

def invalid(message):
    return result(0, [check('submission_contract',False,message)], valid=False)

def finite(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def snapshot(src, dst, max_bytes=100_000_000):
    """Copy only regular files; prevent symlink/path escape and unbounded snapshots."""
    src, dst = Path(src),Path(dst); total=0
    if not src.is_dir(): raise SubmissionError('submission must be a directory')
    for f in sorted(src.rglob('*')):
        if f.is_symlink(): raise SubmissionError('symlinks are forbidden in submission')
        if f.is_dir(): continue
        if not f.is_file(): raise SubmissionError('only regular files are permitted')
        total+=f.stat().st_size
        if total>max_bytes: raise SubmissionError('snapshot exceeds byte limit')
        out=dst/f.relative_to(src);out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(f,out)

def limits(cpu=1200,memory_gb=64):
    def apply():
        os.setsid()
        if hasattr(os,'sched_getaffinity'):
            os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu+1))
        resource.setrlimit(resource.RLIMIT_AS,(memory_gb*1024**3,)*2)
        resource.setrlimit(resource.RLIMIT_FSIZE,(100_000_000,)*2)
        resource.setrlimit(resource.RLIMIT_NOFILE,(512,512))
    return apply

def command(work, argv, readonly=()):
    if os.name!='posix' or not shutil.which('bwrap'):
        raise InfrastructureError('Linux bubblewrap is required; host fallback is disabled')
    cmd=['bwrap','--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL']
    for p in ['/usr','/bin','/lib','/lib64','/sbin','/opt/runtime']:
        if Path(p).exists(): cmd+=['--ro-bind',p,p]
    # Never bind /judge, host /proc, /home, /root, or arbitrary /opt.
    cmd+=['--dir','/etc']
    for p in ['/etc/ld.so.cache','/etc/ld.so.conf','/etc/localtime']:
        if Path(p).is_file():cmd+=['--ro-bind',p,p]
    cmd+=['--bind',str(Path(work).resolve()),'/work','--tmpfs','/tmp',
          '--proc','/proc','--dev','/dev','--chdir','/work','--clearenv',
          '--setenv','PATH','/opt/runtime/venv/bin:/opt/runtime/elan/bin:/usr/local/bin:/usr/bin:/bin',
          '--setenv','HOME','/work/home','--setenv','ELAN_HOME','/opt/runtime/elan',
          '--setenv','LEAN_NUM_THREADS','1','--setenv','OMP_NUM_THREADS','1','--setenv','OPENBLAS_NUM_THREADS','1',
          '--setenv','PYTHONHASHSEED','0','--setenv','LANG','C.UTF-8',
          '--setenv','SDL_VIDEODRIVER','dummy','--setenv','SDL_AUDIODRIVER','dummy']
    for relative in readonly:
        target='/work/'+str(relative)
        cmd+=['--ro-bind',str(Path(work).resolve()/relative),target]
    cmd+=['--']
    return cmd+list(map(str,argv))

def run(work, argv, *, stdin=None, timeout=300):
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        p=subprocess.Popen(command(work,argv),stdin=subprocess.PIPE,stdout=out,stderr=err,preexec_fn=limits())
        try:p.communicate(stdin.encode() if stdin is not None else None,timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.wait();raise SubmissionError('worker time budget exceeded')
        out.seek(0);err.seek(0);s=out.read(5_000_001);e=err.read(100_000).decode(errors='replace')
        if p.returncode and ('bwrap:' in e):raise InfrastructureError('sandbox startup failed: '+e[:500])
        if len(s)>5_000_000:raise SubmissionError('worker output exceeds limit')
        return p.returncode,s.decode(errors='replace'),e

class JsonWorker:
    def __init__(self, work, argv, readonly=()):
        self.err=tempfile.TemporaryFile()
        self.p=subprocess.Popen(command(work,argv,readonly),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                stderr=self.err,bufsize=0,preexec_fn=limits())
        self.buffer=b''
    def exchange(self, obj, timeout=10):
        try:self.p.stdin.write((json.dumps(obj,allow_nan=False)+'\n').encode());self.p.stdin.flush()
        except (BrokenPipeError,OSError):raise SubmissionError('worker terminated')
        deadline=time.monotonic()+timeout
        with selectors.DefaultSelector() as sel:
            sel.register(self.p.stdout,selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                wait=max(0,deadline-time.monotonic())
                if not wait or not sel.select(wait):raise SubmissionError('policy response deadline exceeded')
                chunk=os.read(self.p.stdout.fileno(),65536)
                if not chunk:
                    self.err.seek(0);e=self.err.read(1000).decode(errors='replace')
                    if 'bwrap:' in e:raise InfrastructureError(e)
                    raise SubmissionError('worker ended without a JSON response')
                self.buffer+=chunk
                if len(self.buffer)>1_000_000:raise SubmissionError('policy response too large')
        line,self.buffer=self.buffer.split(b'\n',1)
        try:return json.loads(line)
        except Exception:raise SubmissionError('policy response must be one JSON line')
    def close(self):
        if self.p.poll() is None:
            os.killpg(self.p.pid,signal.SIGKILL);self.p.wait()
        self.err.close()

def workdir():
    return tempfile.TemporaryDirectory(prefix='task-worker-')
