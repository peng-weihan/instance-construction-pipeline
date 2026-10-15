"""Authoritative score controller. Candidate build and execution always drop UID."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

class CandidateFailure(Exception):
    pass


def read_regular(path, limit):
    if not path.exists():
        return b''
    if any(p.is_symlink() for p in [path,*path.parents]):
        raise CandidateFailure('symlink output')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise CandidateFailure('non-regular output')
        b=f.read(limit+1)
    if len(b)>limit:
        raise CandidateFailure('oversized output')
    return b


def snapshot(source,target,limits):
    total=0;count=0;digest=hashlib.sha256()
    if not source.is_dir() or source.is_symlink():
        raise CandidateFailure('missing source directory')
    for base,dirs,files in os.walk(source,followlinks=False):
        dirs[:]=[d for d in dirs if d not in {'.git','.venv','__pycache__','build','dist','.pytest_cache'} and not d.endswith('.egg-info')]
        if any((Path(base)/d).is_symlink() for d in dirs):
            raise CandidateFailure('source directory symlink')
        dirs.sort()
        rel=Path(base).relative_to(source);(target/rel).mkdir(parents=True,exist_ok=True)
        for name in sorted(files):
            p=Path(base)/name
            if p.is_symlink() or not p.is_file():
                raise CandidateFailure('source must contain regular files')
            total+=p.stat().st_size;count+=1
            if total>limits['source_bytes'] or count>limits['max_files']:
                raise CandidateFailure('source snapshot limit')
            data=p.read_bytes()
            (target/rel/name).write_bytes(data)
            digest.update(str(rel/name).encode()+b'\0'+hashlib.sha256(data).digest())
    return total,digest.hexdigest()


def own_tree(path,uid):
    for base,dirs,files in os.walk(path):
        os.chown(base,uid,uid);os.chmod(base,0o755)
        for f in files:
            os.chown(Path(base)/f,uid,uid);os.chmod(Path(base)/f,0o644)


def execute(cmd,cwd,pythonpath,timeout,limits,python):
    uid=limits['candidate_uid']
    def lower():
        os.setgroups([]);os.setgid(uid);os.setuid(uid)
        resource.setrlimit(resource.RLIMIT_CPU,(limits['cpu_sec'],limits['cpu_sec']))
        resource.setrlimit(resource.RLIMIT_AS,(limits['memory_bytes'],limits['memory_bytes']))
        resource.setrlimit(resource.RLIMIT_FSIZE,(limits['output_bytes'],limits['output_bytes']))
        resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
        os.umask(0o022)
    env={'PATH':str(Path(python).parent)+':/usr/bin:/bin','HOME':str(cwd),'TMPDIR':str(cwd),
         'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0',
         'PIP_NO_INDEX':'1','PIP_CACHE_DIR':str(cwd/'pip-cache'), 'PYTHONPATH':str(pythonpath),
         'SETUPTOOLS_SCM_PRETEND_VERSION':'9.2.0.dev0','LC_ALL':'C.UTF-8'}
    with tempfile.TemporaryFile() as output:
        proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdin=subprocess.DEVNULL,
                              stdout=output,stderr=subprocess.STDOUT,preexec_fn=lower,start_new_session=True)
        try:
            try:code=proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:code=124
        finally:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait()
        output.seek(0);text=output.read(limits['output_bytes']).decode('utf8','replace')
    return code,text


def parse_rows(path,limit):
    try:return [json.loads(x) for x in read_regular(path,limit).decode().splitlines()]
    except (ValueError,UnicodeError):raise CandidateFailure('invalid JSONL output')


def grade(args):
    if os.geteuid()!=0:
        raise RuntimeError('grader must be root to drop compile/run UID')
    private=args.private.resolve();spec=json.loads((private/'score-spec.json').read_text())
    # Frozen authoritative assets must be intact; these failures are not candidate scores.
    for rel,digest in json.loads((private/'integrity.json').read_text()).items():
        if hashlib.sha256((private/rel).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('private asset integrity failed: '+rel)
    module_spec=importlib.util.spec_from_file_location('trusted_cases',private/'cases.py')
    cases=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(cases)
    import iniconfig, packaging, pluggy, pygments, setuptools, setuptools_scm, attrs, hypothesis
    import pip
    limits=spec['limits'];names=[x for group in spec['groups'].values() for x in group]
    checks={name:False for name in names};details={};native_ok=False;raw={}
    args.scratch_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fixture-judge-',dir=args.scratch_root) as temp:
        work=Path(temp);work.chmod(0o755)
        try:
            raw['snapshot_bytes'],raw['snapshot_sha256']=snapshot(args.submission,work/'src',limits)
            own_tree(work/'src',limits['candidate_uid'])
            for directory in ('wheel','build-run','site'):
                (work/directory).mkdir()
                os.chown(work/directory,limits['candidate_uid'],limits['candidate_uid'])
            code,log=execute([args.python,'-m','pip','wheel','--no-deps','--no-build-isolation','--wheel-dir',str(work/'wheel'),str(work/'src')],work/'build-run','',limits['build_wall_sec'],limits,args.python)
            details['build']={'exit':code,'log':log[-limits['build_log_chars']:]}
            if code:raise CandidateFailure('candidate wheel build failed')
            wheels=list((work/'wheel').glob('pytest-*.whl'))
            if len(wheels)!=1:raise CandidateFailure('expected one pytest wheel')
            code,log=execute([args.python,'-m','pip','install','--no-deps','--no-compile','--target',str(work/'site'),str(wheels[0])],work/'build-run','',limits['build_wall_sec'],limits,args.python)
            details['install']={'exit':code,'log':log[-limits['install_log_chars']:]}
            if code:raise CandidateFailure('candidate wheel install failed')
            # Native tests are immutable upstream bytes, run as the same UID.
            native_input=work/'native-input';shutil.copytree(private/'native',native_input)
            # Private image assets are mode 600/700; expose only the public
            # native test copy, read-only, under a root-owned parent.
            for base,dirs,files in os.walk(native_input):
                os.chmod(base,0o755)
                for filename in files:
                    os.chmod(Path(base)/filename,0o444)
            native=work/'native-run';native.mkdir();os.chown(native,limits['candidate_uid'],limits['candidate_uid'])
            code,log=execute([args.python,'-m','pytest','-q','-p','pytester','-o','addopts=','--junitxml=native.xml','-k',spec['native_gate']['selection'],str(native_input/'test_native.py')],native,work/'site',limits['native_wall_sec'],limits,args.python)
            try:
                tree=ET.fromstring(read_regular(native/'native.xml',limits['output_bytes']))
                tests=tree.findall('.//testcase')
                native_ok=code==0 and len(tests)==spec['native_gate']['expected_tests'] and not tree.findall('.//failure') and not tree.findall('.//error') and not tree.findall('.//skipped')
            except (ET.ParseError,CandidateFailure):native_ok=False
            details['native']={'exit':code,'passed':native_ok,'log':log[-limits['build_log_chars']:]}
            runs={}
            for case in spec['case_ids']:
                runs[case]={}
                for mode in ('off','on','repeat'):
                    run=work/(case+'-'+mode);run.mkdir();
                    (run/'test_case.py').write_text(cases.CASES[case]);(run/'conftest.py').write_text(cases.OBSERVER)
                    own_tree(run,limits['candidate_uid'])
                    command=[args.python,'-m','pytest','-q','--color=no','-o','addopts=','test_case.py']
                    if mode!='off':command+=['--fixture-trace=trace.jsonl']
                    code,log=execute(command,run,work/'site',limits['run_wall_sec'],limits,args.python)
                    result={'exit':code,'log':log[-limits['case_log_chars']:]}
                    try:
                        result.update(trace=parse_rows(run/'trace.jsonl',limits['output_bytes']),body=parse_rows(run/'body.jsonl',limits['output_bytes']),hook=parse_rows(run/'hook.jsonl',limits['output_bytes']),plugin=read_regular(run/'plugin.jsonl',limits['output_bytes']).decode(),mutable=(run/'mutable').exists())
                    except CandidateFailure as exc:
                        result.update(trace=[],body=[],hook=[],plugin='',mutable=True,parse_error=str(exc))
                    runs[case][mode]=result
            for name in checks:
                try:checks[name]=bool(cases.check(name,runs,spec))
                except (KeyError,TypeError,IndexError,ValueError,AttributeError) as exc:
                    # Candidate traces may be incomplete or malformed.
                    details[name]=type(exc).__name__
            details['runs']=runs
        except CandidateFailure as exc:
            details['candidate_failure']=str(exc)
    group_scores={g:sum(checks[n] for n in ns)/len(ns) for g,ns in spec['groups'].items()}
    score=sum(spec['group_weights'][g]*v for g,v in group_scores.items()) if native_ok else 0.0
    raw.update(passed_checks=sum(checks.values()),total_checks=len(checks),groups=group_scores,native_regressions_passed=native_ok)
    return {'valid':True,'scoring_version':spec['version'],'score_spec_sha256':hashlib.sha256((private/'score-spec.json').read_bytes()).hexdigest(),'score':score,'pass_rate':sum(checks.values())/len(checks),'checks':[{'name':n,'passed':v} for n,v in checks.items()], 'metrics':raw,'summary':'native gate + frozen semantic group means','details':details}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--submission',type=Path,default=Path('/home/workspace/pytest-fixture-trace/submission'))
    parser.add_argument('--private',type=Path,default=Path('/opt/fixture-private'))
    parser.add_argument('--output',type=Path,default=Path('/logs/verifier'))
    parser.add_argument('--scratch-root',type=Path,default=Path('/tmp/fixture-candidates'))
    parser.add_argument('--python',default=sys.executable)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for reward in ('reward.txt','reward.json'):
        (args.output/reward).unlink(missing_ok=True)
    try:report=grade(args)
    except Exception as exc:
        report={'valid':False,'score':None,'checks':[],'metrics':{},'summary':f'infrastructure error: {type(exc).__name__}: {exc}'}
        (args.output/'score.json').write_text(json.dumps(report,indent=2)+'\n')
        raise
    (args.output/'score.json').write_text(json.dumps(report,indent=2)+'\n')
    (args.output/'reward.txt').write_text(str(report['score'])+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},sort_keys=True))

if __name__=='__main__':main()
