#!/usr/bin/env python3
"""One authoritative scorer for native and periodic entries.

Root owns this module, private fixtures, base tree, and reward directory.
Both candidate compilation and execution drop to uid 10001. No reference
source or expected output is passed to candidate processes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from oracle import arguments, expected

class InfrastructureError(Exception):
    pass
class SubmissionError(Exception):
    pass

def read_json(path):
    return json.loads(path.read_text())

def execute(cmd, cwd, env, limits, uid, timeout, logdir):
    logdir.mkdir(parents=True, exist_ok=True,mode=0o700)
    os.chmod(logdir,0o700)
    def restrict():
        os.setsid()
        os.umask(0o077)
        resource.setrlimit(resource.RLIMIT_AS, (limits['max_virtual_bytes'],)*2)
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout+1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits['max_file_bytes'],)*2)
        resource.setrlimit(resource.RLIMIT_NPROC, (limits['max_processes'],)*2)
        resource.setrlimit(resource.RLIMIT_CORE, (0,0))
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
    start=time.monotonic_ns()
    with (logdir/'stdout').open('wb') as out, (logdir/'stderr').open('wb') as err:
        os.fchmod(out.fileno(),0o600);os.fchmod(err.fileno(),0o600)
        proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=out,stderr=err,preexec_fn=restrict)
        timed_out=False;overflow=False
        deadline=time.monotonic()+timeout
        try:
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    timed_out=True;break
                try:
                    proc.wait(timeout=min(limits['output_poll_sec'],remaining))
                    break
                except subprocess.TimeoutExpired:
                    if sum((logdir/f).stat().st_size for f in ['stdout','stderr'])>limits['max_output_bytes']:
                        overflow=True;break
        finally:
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
    size=sum((logdir/f).stat().st_size for f in ['stdout','stderr'])
    overflow=overflow or size>limits['max_output_bytes']
    return dict(returncode=proc.returncode,timed_out=timed_out,overflow=overflow,wall_ns=time.monotonic_ns()-start,
                stdout=(logdir/'stdout').read_bytes()[:limits['max_output_bytes']].decode('utf-8',errors='replace'),
                stderr=(logdir/'stderr').read_bytes()[:limits['max_output_bytes']].decode('utf-8',errors='replace'))

def owned_tree(path,uid):
    for base,dirs,files in os.walk(path):
        os.chown(base,uid,uid);os.chmod(base,0o700)
        for file in files:
            p=Path(base)/file
            if p.is_symlink(): raise InfrastructureError('unexpected base symlink')
            os.chown(p,uid,uid)
            os.chmod(p,0o700 if p.stat().st_mode & 0o111 else 0o600)

def readonly_source(path):
    for base,dirs,files in os.walk(path):
        os.chown(base,0,0);os.chmod(base,0o555)
        for name in files:
            p=Path(base)/name
            if p.is_symlink():raise InfrastructureError('unexpected source symlink')
            executable=bool(p.stat().st_mode & 0o111)
            os.chown(p,0,0);os.chmod(p,0o555 if executable else 0o444)

def safe_source(submission,relative):
    # Reject known-name symlink reads and escapes before opening any candidate file.
    p=submission
    for component in relative.parts:
        p=p/component
        if p.is_symlink():raise SubmissionError(f'symlink in source path: {relative}')
    if not p.is_file():raise SubmissionError(f'missing source: {relative}')
    return p

def copy_candidate(base,submission,dst,limits):
    if submission.is_symlink(): raise SubmissionError('submission must be a directory')
    total=0
    for root in limits['allowed_roots']:
        for original in sorted((base/root).rglob('*'+limits['file_suffix'])):
            rel=original.relative_to(base)
            candidate=safe_source(submission,rel)
            total+=candidate.stat().st_size
            if total>limits['max_source_bytes']:raise SubmissionError('source budget exceeded')
            data=candidate.read_bytes()
            # Original native regression sections remain authoritative. Public
            # edits to their copies are never used by the judge.
            marker=b'#[cfg(test)]\nmod tests'
            if marker in original.read_bytes():
                if marker not in data:raise SubmissionError(f'preserve test module boundary in {rel}')
                data=data.split(marker,1)[0]+marker+original.read_bytes().split(marker,1)[1]
            (dst/rel).write_bytes(data)
        # New production Rust modules under the declared roots are supported.
        candidate_root=submission/root
        for p in sorted(candidate_root.rglob('*'+limits['file_suffix'])):
            rel=p.relative_to(submission)
            if (base/rel).exists():continue
            p=safe_source(submission,rel)
            total+=p.stat().st_size
            if total>limits['max_source_bytes']:raise SubmissionError('source budget exceeded')
            (dst/rel).parent.mkdir(parents=True,exist_ok=True)
            (dst/rel).write_bytes(p.read_bytes())

def compile_command(source,runtime,tests=False):
    cmd=[str(runtime/'rust/bin/cargo'),'test' if tests else 'build','--manifest-path',str(source/'Cargo.toml'),'--locked','--offline','--release','-p','datafusion-physical-plan']
    return cmd+(['--lib'] if tests else ['--example','edgebench_sort'])

def strict_json(text):
    def invalid_constant(value):
        raise ValueError('nonfinite JSON constant')
    return json.loads(text,parse_constant=invalid_constant)

def parse_run(result,case):
    if result['returncode']!=0 or result['timed_out'] or result['overflow']:
        return False,{},'candidate execution failed'
    try:
        ids=strict_json(result['stdout'])
        metrics=[strict_json(s[7:]) for s in result['stderr'].splitlines() if s.startswith('ENGINE ')]
        if len(metrics)!=1:return False,{},'missing or ambiguous engine metrics'
        if not isinstance(ids,list) or any(type(i) is not int for i in ids):
            return False,{},'row ids must be integers'
        m=metrics[0]
        if not isinstance(m,dict) or set(m)!={'elapsed_ns','spill_count','spilled_bytes'}:
            return False,{},'invalid engine metric schema'
        if not isinstance(m['elapsed_ns'],list) or len(m['elapsed_ns'])!=case['repetitions'] or any(type(n) is not int or n<0 for n in m['elapsed_ns']):
            return False,{},'invalid elapsed metrics'
        if any(type(m[k]) is not int or m[k]<0 for k in ['spill_count','spilled_bytes']):
            return False,{},'invalid spill metrics'
        ok=ids==expected(case)
        if case['group']=='spill':ok=ok and metrics[0]['spill_count']>0
        return ok,metrics[0],'ok' if ok else 'order, row count, or spill mismatch'
    except (ValueError,TypeError,KeyError):
        return False,{},'invalid candidate output'

def native_passed(stdout, native_spec):
    observed=re.findall(r'^test (\S+) \.\.\. (ok|FAILED|ignored)$',stdout,re.M)
    return (len(observed)==native_spec['test_count']
            and {n for n,result in observed}==set(native_spec['tests'])
            and all(result=='ok' for n,result in observed)
            and 'test result: ok.' in stdout)

def grade(args,spec):
    limits=spec['candidate'];uid=limits['uid']
    if os.geteuid()!=0:raise InfrastructureError('trusted launcher must run as root to enforce uid isolation')
    for p in [args.runtime/'rust/bin/cargo',args.runtime/'rust/bin/rustc',Path('/usr/bin/cc'),args.base/'Cargo.lock',args.runtime/'vendor',args.runtime/'health/edgebench_sort']:
        if not p.exists():raise InfrastructureError(f'missing promised build/runtime dependency: {p}')
    lock=read_json(args.runtime/'runtime-lock.json')
    # Promised public dependencies must be readable during unprivileged builds.
    # A private or corrupt vendor file is an infrastructure failure.
    public_dirs=set()
    for relative in lock['relative']:
        p=args.runtime/relative
        if not p.is_file() or not (p.stat().st_mode & 0o004):
            raise InfrastructureError('promised runtime file not publicly readable: '+relative)
        for directory in p.parents:
            if directory==args.runtime.parent:break
            public_dirs.add(directory)
    for directory in public_dirs:
        if directory.stat().st_mode & 0o005 != 0o005:
            raise InfrastructureError('promised runtime directory not accessible')
    for relative,digest in lock['relative'].items():
        p=args.runtime/relative
        if not p.is_file() or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=digest:
            raise InfrastructureError('promised runtime input missing or corrupt: '+relative)
    for absolute,digest in lock['absolute'].items():
        p=Path(absolute)
        if not p.is_file() or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=digest:
            raise InfrastructureError('promised system tool missing or corrupt')
    private=read_json(args.private/'assets.json')
    for relative,digest in private.items():
        if hashlib.sha256((args.private/relative).read_bytes()).hexdigest()!=digest:
            raise InfrastructureError('private asset hash mismatch')
    cases=read_json(args.private/'cases.json')
    frozen={n:g for g,v in spec['groups'].items() for n in v['cases']}
    if len(cases)!=len(frozen) or any(frozen.get(c['name'])!=c['group'] for c in cases):
        raise InfrastructureError('case membership mismatch')
    with tempfile.TemporaryDirectory(prefix='sort-grade-',dir=args.temporary_root) as temporary:
        work=Path(temporary);os.chmod(work,0o755)
        source=work/'source';shutil.copytree(args.base,source)
        cargo=work/'cargo';cargo.mkdir()
        (cargo/'config.toml').write_text('[source.crates-io]\nreplace-with="vendored"\n[source.vendored]\ndirectory="'+str(args.runtime/'vendor')+'"\n')
        target=work/'target'
        if (args.runtime/'cache').exists():shutil.copytree(args.runtime/'cache',target)
        else:target.mkdir()
        scratch=work/'scratch';scratch.mkdir()
        home=work/'home';home.mkdir()
        env=dict(PATH=str(args.runtime/'rust/bin')+':/usr/bin:/bin',HOME=str(home),CARGO_HOME=str(cargo),CARGO_TARGET_DIR=str(target),CARGO_BUILD_JOBS=str(limits['build_jobs']),CARGO_NET_OFFLINE='true',TMPDIR=str(scratch),RUST_BACKTRACE='0',CARGO_PROFILE_RELEASE_DEBUG='0',LANG='C.UTF-8')
        for p in [cargo,target,scratch,home]:owned_tree(p,uid)
        health_source=work/'toolchain-health.rs'
        health_source.write_text('fn main() {}\n')
        health_binary=scratch/'toolchain-health'
        compiler_health=execute([str(args.runtime/'rust/bin/rustc'),'--crate-name','toolchain_health',str(health_source),'-o',str(health_binary)],work,env,limits,uid,limits['case_timeout_sec'],work/'compiler-health')
        if compiler_health['returncode']!=0 or compiler_health['timed_out'] or compiler_health['overflow']:
            raise InfrastructureError('trusted compiler/linker health check failed')
        run_health=execute([str(health_binary)],work,env,limits,uid,limits['case_timeout_sec'],work/'linker-health')
        if run_health['returncode']!=0:
            raise InfrastructureError('trusted compiled runtime health check failed')
        # Trusted baseline health test. Any failure here is infrastructure, not a candidate zero.
        health=cases[0]
        r=execute([str(args.runtime/'health/edgebench_sort'),*arguments(health)],work,env,limits,uid,limits['case_timeout_sec'],work/'health')
        if not parse_run(r,health)[0]:raise InfrastructureError('trusted engine health/oracle mismatch')
        try:copy_candidate(args.base,args.submission,source,limits)
        except SubmissionError as e:
            return dict(valid=True,score=0.0,pass_rate=0.0,checks=[dict(name='source',passed=False,detail=str(e))],metrics={})
        readonly_source(source)
        build=execute(compile_command(source,args.runtime),source,env,limits,uid,limits['build_timeout_sec'],work/'build')
        if build['returncode']!=0 or build['timed_out'] or build['overflow']:
            return dict(valid=True,score=0.0,pass_rate=0.0,checks=[dict(name='compile',passed=False,detail=build['stderr'][-8000:])],metrics={'build_wall_ns':build['wall_ns']})
        # Preserve the compiled public driver before executing any candidate code.
        # Native regressions run before the candidate probe can touch its build cache.
        programs=work/'programs';programs.mkdir(mode=0o755)
        binary=programs/'edgebench_sort'
        shutil.copyfile(target/'release/examples/edgebench_sort',binary)
        binary.chmod(0o555);programs.chmod(0o555)
        native_cmd=compile_command(source,args.runtime,tests=True)+[spec['native']['filter'],'--','--test-threads=1']
        native=execute(native_cmd,source,env,limits,uid,limits['native_timeout_sec'],work/'native')
        native_ok=native['returncode']==0 and not native['timed_out'] and not native['overflow'] and native_passed(native['stdout'],spec['native'])
        checks=[];raw={};groups={g:0 for g in spec['groups']}
        for c in cases:
            try:
                r=execute([str(binary),*arguments(c)],source,env,limits,uid,limits['case_timeout_sec'],work/('run-'+c['name']))
                ok,engine,detail=parse_run(r,c)
            except OSError as error:
                r=dict(wall_ns=None,returncode=None)
                ok,engine,detail=False,{},'candidate launch failed: '+str(error)
            groups[c['group']]+=int(ok)
            checks.append(dict(name=c['name'],group=c['group'],passed=ok,detail=detail))
            raw[c['name']]=dict(wall_ns=r['wall_ns'],engine_reported=engine,returncode=r['returncode'])
        checks.append(dict(name='native-regressions',passed=native_ok,detail=native['stdout'][-4000:] if native_ok else native['stderr'][-4000:]))
        score=sum(v['weight']*groups[g]/v['case_count'] for g,v in spec['groups'].items())+spec['native']['weight']*int(native_ok)
        return dict(valid=True,score=score,pass_rate=sum(c['passed'] for c in checks)/len(checks),checks=checks,metrics=dict(cases=raw,groups_passed=groups,native_wall_ns=native['wall_ns'],performance_enabled=False,performance_score=None),summary='Draft correctness score only; performance scoring disabled pending calibration')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',type=Path,default=Path('/opt'))
    parser.add_argument('--temporary-root',type=Path,default=None)
    parser.add_argument('--submission',type=Path,default=Path('/home/workspace/datafusion/submission'))
    parser.add_argument('--base',type=Path,default=Path('/opt/base'))
    parser.add_argument('--private',type=Path,default=Path('/opt/judge/private'))
    parser.add_argument('--output',type=Path,default=Path('/logs/verifier'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True);os.chmod(args.output,0o700)
    for name in ['reward.txt','reward.json','score.json']:(args.output/name).unlink(missing_ok=True)
    try:
        spec=read_json(args.private/'score-spec.json')
        report=grade(args,spec)
    except Exception as e:
        report=dict(valid=False,score=None,checks=[],metrics={},summary=f'infrastructure/reference error: {type(e).__name__}: {e}')
        (args.output/'score.json').write_text(json.dumps(report,indent=2)+'\n')
        print(report['summary'],file=sys.stderr)
        return 2
    (args.output/'score.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (args.output/'reward.txt').write_text(f"{report['score']:.17g}\n")
    return 0
if __name__=='__main__':sys.exit(main())
