"""Explicit trusted-author component tests on macOS; never a verifier sandbox fallback.

No model-generated or external submissions are executed. Docker, Lean kernel and
Wesnoth engine validation are separate evidence layers.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import selectors
import shutil
import subprocess
import sys
import time
import traceback
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {'science': 'layered_aquifer_source_lab', 'software': 'restler_resilient_execution',
         'finance': 'cross_asset_adaptive_allocator', 'packing': 'industrial_nesting_improvement',
         'game': 'wesnoth_frontier_campaign_ai'}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def science(task, output):
    import numpy as np
    import grader
    import forward
    from runtime import SubmissionError
    generator = load('private_generator', task / 'private/generate_scene.py')
    scene = json.loads((task / 'public/scene.json').read_text())
    truth = json.loads((task / 'private/truth.json').read_text())
    days = [.25, 30., 90., 180.]
    expected = generator.states(scene, truth, days)
    actual = forward.simulate(scene, truth, days)
    error = max(float(np.max(np.abs(expected[d] - actual[d]))) for d in days)
    checks = [{'name': 'independent_forward_agreement', 'pass': error < 1e-10, 'max_abs_error': error}]
    records = []
    variants = [('privileged_truth_control', truth), ('rate_perturbed_control', {**truth, 'rate': truth['rate'] * 1.2})]
    for name, params in variants:
        target = output / name; target.mkdir()
        (target / 'answer.json').write_text(json.dumps(params))
        for suite in ['public', 'feedback', 'audit']:
            before = time.monotonic(); report = grader.grade(target, suite)
            records.append({'control': name, 'suite': suite, 'seconds': time.monotonic()-before, 'feedback': report})
    true_scores = [r['feedback']['score'] for r in records if r['control'] == 'privileged_truth_control' and r['suite'] != 'public']
    perturbed = [r['feedback']['score'] for r in records if r['control'] == 'rate_perturbed_control' and r['suite'] != 'public']
    checks += [{'name': 'truth_matches_hidden_labels', 'pass': all(s > 1-1e-10 for s in true_scores)},
               {'name': 'source_perturbation_reduces_score', 'pass': all(a>b for a,b in zip(true_scores, perturbed))}]
    invalid = output / 'invalid'; invalid.mkdir(); (invalid / 'answer.json').write_text('{}')
    try:
        grader.grade(invalid, 'feedback'); rejected = False
    except SubmissionError:
        rejected = True
    checks.append({'name': 'missing_parameters_rejected', 'pass': rejected})
    return {'checks': checks, 'records': records, 'truth_control_is_not_solver_performance': True}


class TrustedReferenceProcess:
    def __init__(self, work, log):
        self.log = log.open('w')
        self.process = subprocess.Popen([sys.executable, '-B', 'probe.py'], cwd=work,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log, bufsize=0)
        self.pending = b''
    def exchange(self, value):
        self.process.stdin.write((json.dumps(value)+'\n').encode()); self.process.stdin.flush()
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic()+15
            while b'\n' not in self.pending:
                wait = deadline-time.monotonic()
                if wait <= 0 or not selector.select(wait): raise TimeoutError('reference probe timed out')
                data = os.read(self.process.stdout.fileno(), 65536)
                if not data: raise RuntimeError('reference probe ended before response')
                self.pending += data
                if len(self.pending)>1_000_000: raise ValueError('oversized probe output')
        line, self.pending = self.pending.split(b'\n',1)
        return json.loads(line)
    def close(self):
        if self.process.poll() is None: self.process.kill()
        self.process.wait(); self.log.close()


def software(task, output):
    import grader
    work = output/'work'; work.mkdir()
    shutil.copytree(task/'public/repo', work/'repo')
    shutil.copytree(task/'solution/reference', work/'repo/restler', dirs_exist_ok=True)
    shutil.copyfile(task/'verifier/probe.py', work/'probe.py')
    suites = json.loads((task/'private/behavior_cases.json').read_text())
    results = []
    for suite, rows in suites.items():
        for index, row in enumerate(rows):
            process = TrustedReferenceProcess(work, output/f'{suite}-{index}.stderr')
            payload = dict(row['input']); responses = iter(payload.pop('responses', []))
            calls, waits, clock = [], [], 0.
            actual = {}; error = None
            try:
                message = process.exchange(payload)
                for _ in range(200):
                    if 'final' in message:
                        actual = message['final']
                        if payload['op'] not in ['replay','lease','policy']:
                            actual['calls'], actual['waits'] = calls, waits
                        break
                    request = message['rpc']
                    if request['kind'] == 'sleep':
                        seconds = request['seconds']; waits.append(seconds); clock += seconds
                        reply = {'clock':clock}
                    else:
                        method, path = request['raw'].split()[:2]
                        calls.append({'method':method,'path':path,'timeout':request['timeout'],'reconnect':request['reconnect']})
                        response=next(responses);clock+=response.get('elapsed',0)
                        reply={'clock':clock,'response':response}
                    message=process.exchange(reply)
                else: raise RuntimeError('probe RPC limit')
                passed = grader.matches(actual, row['expect'])
            except Exception as exc:
                passed=False;error=repr(exc)
            finally: process.close()
            results.append({'suite':suite,'name':row['name'],'group':row['group'],'pass':passed,
                            'expected':row['expect'],'actual':actual,'error':error})
    return {'checks':results, 'sandbox_tested':False, 'method':'same published probe and predicates, explicit trusted reference host process'}


def finance(task, output):
    import grader
    from ledger import simulate
    from runtime import SubmissionError
    policy = load('author_reference_policy', task/'solution/policy.py')
    mandate=json.loads((task/'public/mandate.json').read_text());records=[];checks=[]
    for suite in ['public','feedback','audit']:
        prices,dates,start,assets=grader.data(suite)
        for name, reference in [('fixed_baseline',False),('author_reference',True)]:
            before=time.monotonic()
            if reference:
                user_state=policy.initialize({'assets':assets,'mandate':mandate})
                def decide(history,state):
                    nonlocal user_state
                    answer=policy.decide(history,{**state,'user_state':user_state})
                    if 'user_state' in answer:user_state=answer.pop('user_state')
                    return answer
            else:decide=grader.static_policy(assets,mandate)
            try:
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter('always')
                    metrics=simulate(prices,dates,start,assets,mandate,decide)
                records.append({'suite':suite,'policy':name,'metrics':metrics,'seconds':time.monotonic()-before,
                                'warnings':sorted(set(str(w.message) for w in captured))})
                checks.append({'name':suite+'/'+name,'pass':True})
            except Exception as exc:
                checks.append({'name':suite+'/'+name,'pass':False,'error':repr(exc)})
        try:
            simulate(prices,dates,start,assets,mandate,lambda history,state: {})
            rejected=False
        except SubmissionError:rejected=True
        checks.append({'name':suite+'/invalid_policy_rejected','pass':rejected})
    return {'checks':checks,'records':records,'policy_worker_sandbox_tested':False}


def packing(task, output):
    from geometry import validate
    constants=json.loads((task/'public/scoring_metadata.json').read_text())['constants']
    item={'type':'polygon','vertices':[{'x':0,'y':0},{'x':1,'y':0},{'x':1,'y':1},{'x':0,'y':1}],'copies':2}
    instance={'bin_types':[{'width':10,'height':2}],'item_types':[item]}
    def cert(x):return {'bins':[{'id':0,'items':[{'id':0,'x':0,'y':0},{'id':0,'x':x,'y':0}]}]}
    checks=[]
    for name, value, valid in [('touching_is_valid',cert(1),True),('overlap_rejected',cert(.5),False),('boundary_rejected',cert(11),False),('missing_piece_rejected',{'bins':[{'id':0,'items':[]}]},False)]:
        try:
            result=validate(instance,value,constants);accepted=True
        except ValueError:result=None;accepted=False
        checks.append({'name':name,'pass':accepted==valid,'geometry':result})
    return {'checks':checks,'solver_built':False,'scope':'independent geometry component on designed controls'}


def game(task, output):
    from lupa.lua54 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    checks=[]
    for path in [task/'public/adapter.lua',task/'public/submission/policy.lua',task/'solution/policy.lua']:
        parsed=lua.eval('function(source) local f,e=load(source); return f~=nil,e end')(path.read_text())
        checks.append({'name':'lua_parse/'+str(path.relative_to(task)), 'pass':parsed[0], 'error':parsed[1]})
    policy=lua.execute((task/'solution/policy.lua').read_text())
    empty=lua.table_from({'side':1,'units':[],'actions':[],'villages':[]},recursive=True)
    checks.append({'name':'reference_defers_without_actions','pass':policy.decide(empty) is None})
    state=lua.table_from({'side':1,'units':[],'actions':[{'kind':'recruit','unit_type':'Spearman','cost':14,'x':1,'y':1}],'villages':[]},recursive=True)
    answer=policy.decide(state)
    checks.append({'name':'reference_selects_recruit','pass':answer['index']==1 and 1<=answer['priority']<=250000})
    return {'checks':checks,'wesnoth_engine_executed':False,'scope':'Lua 5.4 parsing and reference policy controls, no matches'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('category',choices=TASKS)
    parser.add_argument('--batch',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    task=Path(args.batch).resolve()/TASKS[args.category];output=Path(args.output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(task/'verifier'));sys.dont_write_bytecode=True
    report={'category':args.category,'task':str(task.relative_to(ROOT)),'mode':'trusted_component_host_validation',
            'docker_executed':False,'model_runs':0,'six_hour_runs':0,'started_unix':time.time(),
            'task_manifest_sha256':hashlib.sha256((task/'files.sha256.json').read_bytes()).hexdigest()}
    try:
        report.update(globals()[args.category](task,output))
        report['status']='passed' if all(x['pass'] for x in report['checks']) else 'failed_checks'
    except Exception:
        report['status']='error';report['traceback']=traceback.format_exc()
    report['finished_unix']=time.time()
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'category':args.category,'status':report['status'],'checks':len(report.get('checks',[])),
                      'failed':[x for x in report.get('checks',[]) if not x['pass']], 'traceback':report.get('traceback')},indent=2))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
