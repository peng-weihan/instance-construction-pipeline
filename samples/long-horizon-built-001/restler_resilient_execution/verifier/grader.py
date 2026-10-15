import json,shutil
from pathlib import Path
from runtime import PUBLIC,ROOT,read_json,snapshot,JsonWorker,workdir,SubmissionError,check,result,finite
from cases import cases
WEIGHTS={'policy':.10,'retry':.15,'idempotency':.15,'async':.15,'leases':.20,'trace':.10,'replay':.15}
def matches(actual,expected):
    for path,want in expected.items():
        if path=='exception_present':
            if ('exception' in actual)!=want:return False
        elif path=='secret_free':
            if any(s in json.dumps(actual.get('events',[])) for s in ['SECRET_AUTH','SECRET_KEY']):return False
        elif path=='trace_schema':
            events=actual.get('events',[])
            if not events:return False
            keys={'event_index','request_id','resource_id','event','attempt','elapsed_ms','decision','reason'}
            if any(set(e)!=keys for e in events):return False
            if [e['event_index'] for e in events]!=list(range(len(events))):return False
        else:
            v=actual
            try:
                for k in path.split('.'):v=len(v) if k=='length' else v[k]
            except (KeyError,TypeError):return False
            if v!=want:return False
    return True
def grade(submission,suite):
    checks=[];group={k:[] for k in WEIGHTS}
    with workdir() as tmp:
        work=Path(tmp);shutil.copytree(PUBLIC/'repo',work/'repo')
        # Input is precisely the restler directory. Reconstruct all other repo paths.
        shutil.rmtree(work/'repo/restler');snapshot(submission,work/'repo/restler')
        shutil.copyfile(ROOT/'verifier/probe.py',work/'probe.py')
        for row in cases():
            # The trusted controller owns fault responses, time, and transport records.
            # Candidate code cannot fabricate the observations used for these checks.
            payload=dict(row['input']);responses=iter(payload.pop('responses',[]));calls=[];waits=[];clock=0.
            worker=JsonWorker(work,['python','probe.py']);ok=False
            try:
                message=worker.exchange(payload,timeout=5)
                for step in range(200):
                    if 'final' in message:
                        actual=message['final']
                        if payload['op'] not in ['replay','lease','policy']:
                            actual['calls']=calls;actual['waits']=waits
                        ok=matches(actual,row['expect']);break
                    request=message['rpc']
                    if request['kind']=='sleep':
                        sec=request['seconds']
                        if not finite(sec) or sec<0:raise SubmissionError('invalid sleep')
                        waits.append(sec);clock+=sec;reply={'clock':clock}
                    elif request['kind']=='transport':
                        method,path=request['raw'].split()[:2]
                        calls.append({'method':method,'path':path,'timeout':request['timeout'],'reconnect':request['reconnect']})
                        response=next(responses);clock+=response.get('elapsed',0);reply={'clock':clock,'response':response}
                    else:raise SubmissionError('unknown probe RPC')
                    message=worker.exchange(reply,timeout=5)
            except (SubmissionError,ValueError,KeyError,TypeError,StopIteration):ok=False
            finally:worker.close()
            checks.append(check(row['name'],ok,'ok' if ok else 'behavior does not meet the published contract'))
            group[row['group']].append(ok)
    fractions={k:sum(v)/len(v) for k,v in group.items()}
    return result(sum(WEIGHTS[k]*fractions[k] for k in WEIGHTS),checks,{'group_pass_fraction':fractions,'check_count':len(checks)})
