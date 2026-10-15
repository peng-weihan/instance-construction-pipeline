#!/usr/bin/env python3
"""Executable native component audit, NOT the missing Polaris acceptance judge.

Full scoring is intentionally unavailable until trusted Polaris service/reset,
independent HTTP observation and lifecycle oracle have been constructed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile


def run(cmd,cwd,timeout=90):
    env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','LD_PRELOAD')}
    env['PATH']=str(Path(sys.executable).parent)+':/usr/local/bin:/usr/bin:/bin'
    env['PYTHONDONTWRITEBYTECODE']='1'
    import resource
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
        if sys.platform.startswith('linux'):
            resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    identity={'user':65534,'group':65534,'extra_groups':[]} if os.getuid()==0 else {}
    with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
        p=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=out,stderr=err,start_new_session=True,preexec_fn=limits,**identity)
        timed=False
        try: p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed=True
            os.killpg(p.pid,signal.SIGKILL)
            p.wait()
        finally:
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
        out.seek(0);err.seek(0)
        return {'command':cmd,'cwd':str(cwd),'exit':p.returncode,'timeout':timed,'stdout':out.read(12000).decode(errors='replace'),'stderr':err.read(12000).decode(errors='replace')}


def components(candidate):
    checks=[];records=[]
    if not (candidate/'restler/restler.py').is_file():
        return [{'name':n,'passed':False,'detail':'missing native engine'} for n in ['native_smoke','native_replay','commit','resume','corruption','input_mismatch']],[]
    with tempfile.TemporaryDirectory(prefix='restler-native-') as temporary:
        root=Path(temporary);root.chmod(0o777)
        engine=root/'restler'
        shutil.copytree(candidate/'restler',engine,ignore=shutil.ignore_patterns('RestlerResults','__pycache__','.pytest_cache'))
        # Container candidate may run as nobody; this copy contains only public
        # engine and public native fixtures, never the trusted private oracle.
        for p in [engine,*engine.rglob('*')]:
            p.chmod(0o777 if p.is_dir() else 0o666)
        for name,test in [('native_smoke','test_abc_minimal_smoke_test'),('native_replay','test_trace_database_replay_file')]:
            record=run([sys.executable,'-m','pytest','unit_tests/test_basic_functionality_end_to_end.py::FunctionalityTests::'+test,'-q'],engine)
            records.append({'phase':name,**record})
            checks.append({'name':name,'passed':record['exit']==0})
        checkpoint=root/'frontier.bin'
        command=[sys.executable,'restler.py','--use_test_socket','--fuzzing_mode','bfs','--restler_grammar','unit_tests/log_baseline_test_files/abc_test_grammar.py','--custom_mutations','unit_tests/log_baseline_test_files/abc_dict.json','--host','unittest','--token_refresh_cmd','python unit_tests/authentication_test_files/unit_test_server_auth.py','--token_refresh_interval','10','--garbage_collection_interval','30','--campaign_checkpoint_file',str(checkpoint)]
        first=run(command+['--max_sequence_length','2'],engine)
        records.append({'phase':'commit',**first})
        committed=False
        if checkpoint.is_file():
            try:
                line,payload=checkpoint.read_bytes().split(b'\n',1);header=json.loads(line)
                committed=first['exit']==0 and header['generation']==2 and hashlib.sha256(payload).hexdigest()==header['sha256']
            except (KeyError,ValueError): pass
        checks.append({'name':'commit','passed':committed})
        second=run(command+['--max_sequence_length','3','--campaign_resume'],engine)
        records.append({'phase':'resume',**second})
        restored=False
        if checkpoint.is_file():
            try: restored=committed and second['exit']==0 and json.loads(checkpoint.read_bytes().split(b'\n',1)[0])['generation']==3 and 'restored generation 2' in second['stdout']
            except (KeyError,ValueError): pass
        checks.append({'name':'resume','passed':restored})
        if committed:
            original=checkpoint.read_bytes()
            checkpoint.write_bytes(original[:-8]+b'corrupt!')
            bad=run(command+['--max_sequence_length','4','--campaign_resume'],engine)
            records.append({'phase':'corruption',**bad})
            checks.append({'name':'corruption','passed':bad['exit']!=0 and 'checksum mismatch' in (bad['stdout']+bad['stderr'])})
            checkpoint.write_bytes(original)
            dictionary=engine/'unit_tests/log_baseline_test_files/abc_dict.json'
            data=json.loads(dictionary.read_text());data['restler_fuzzable_string']=['DIFFERENT_DICTIONARY_VALUE']
            dictionary.write_text(json.dumps(data))
            changed=run(command+['--max_sequence_length','4','--campaign_resume'],engine)
            records.append({'phase':'input_mismatch',**changed})
            checks.append({'name':'input_mismatch','passed':changed['exit']!=0 and 'fingerprint mismatch' in (changed['stdout']+changed['stderr'])})
        else:
            checks.extend([{'name':'corruption','passed':False,'detail':'no committed checkpoint'}, {'name':'input_mismatch','passed':False,'detail':'no committed checkpoint'}])
    return checks,records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate',type=Path,default=Path('/home/workspace/restler_campaign_recovery/submission'))
    parser.add_argument('--output',type=Path,default=Path('/logs/verifier'))
    parser.add_argument('--component-only',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for name in ['reward.txt','reward.json']: (args.output/name).unlink(missing_ok=True)
    checks,records=components(args.candidate.resolve())
    result={'valid':False,'score':None,'summary':'hold_for_evidence: native component diagnostics available, Polaris HTTP/reset/lifecycle reference and acceptance oracle missing','component_checks':checks,'component_pass_rate':sum(x['passed'] for x in checks)/6,'component_fixed_denominator':6,'records':records,'unexecuted_required_groups':['external HTTP crash/replay exactly-once semantics','Polaris principal/role/catalog dependency restoration','cleanup and resource lifecycle after cancellation']}
    (args.output/'score.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
    # Do not leave a numeric reward for an unconstructed formal experiment.
    return 0 if args.component_only else 2

if __name__=='__main__': sys.exit(main())
