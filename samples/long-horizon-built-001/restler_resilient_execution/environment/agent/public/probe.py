"""Public probe adapter; contains no expected results. Runs in isolated worker."""
import json,random,sys,types
sys.path.insert(0,'repo/restler')
def rpc(message):
    print(json.dumps({'rpc':message}),flush=True)
    return json.loads(sys.stdin.readline())

def probe(c):
    from restler_settings import RestlerSettings
    RestlerSettings.TEST_DeleteInstance();settings=RestlerSettings({'execution_policy':c.get('policy',{})})
    from engine.core import request_utilities as ru,async_request_utilities as au
    from engine.core.execution_policy import Context,resolve,LeaseGraph
    from engine.transport_layer.response import HttpResponse
    class Clock:
        def __init__(self):self.t=0.;self.waits=[]
        def monotonic(self):return self.t
        def wall(self):return c.get('wall',1700000000)+self.t
        def sleep(self,t):
            answer=rpc({'kind':'sleep','seconds':t});self.waits.append(t);self.t=answer['clock']
    clock=Clock();calls=[]
    class Sock:
        def sendRecv(self,raw,timeout,reconnect=False):
            calls.append({'method':raw.split()[0],'path':raw.split()[1],'timeout':timeout,'reconnect':reconnect})
            answer=rpc({'kind':'transport','raw':raw,'timeout':timeout,'reconnect':reconnect});r=answer['response'];clock.t=answer['clock']
            if r.get('network_error'):raise OSError('injected connection reset')
            return r.get('success',True),HttpResponse(r.get('raw',f'HTTP/1.1 {r.get("status",200)} Test\r\n\r\n'))
    ru.threadLocal.main_sock=Sock();ru.time=types.SimpleNamespace(sleep=clock.sleep)
    au.time=types.SimpleNamespace(time=clock.monotonic,sleep=clock.sleep)
    op=c['op'];policy=c.get('policy',{});raw=c.get('request','GET /items HTTP/1.1\r\n\r\n')
    method,path=raw.split()[:2]
    if op=='policy':return {'policy':resolve(settings.execution_policy,method,path)}
    ctx=Context(resolve(policy,method,path),clock,random.Random(c.get('seed',0)),lambda:clock.t>=c.get('cancel_at',float('inf')))
    if op=='lease':
        g=LeaseGraph(c['resources'])
        for n,refs in c.get('created',[]):g.created(n,refs)
        for n in c.get('release',[]):g.release(n)
        deleted,retained=g.cleanup(lambda n,t:True,ctx)
        return {'deleted':deleted,'retained':retained}
    if op=='workflow':
        from engine.core.resilient_workflow import execute_workflow
        out=execute_workflow(c['spec'],ctx);out['calls']=calls;return out
    if op=='replay':
        from engine.tools.replay_execution import replay
        a=replay(c['records'],policy);b=replay(c['records'],policy)
        return {'same':a==b,'events':a}
    from engine.core.execution_policy import CURRENT
    token=CURRENT.set(ctx)
    try:
        r=ru.send_request_data(raw)
        if op=='async':
            out,error,waited=au.try_async_poll(raw,r,c.get('max_wait',30))
            return {'statuses':[x.status_code for x in out],'error':error,'waited':waited,'terminal':ctx.terminal,'calls':calls,'waits':clock.waits,'events':ctx.events}
        return {'status':r.status_code,'terminal':ctx.terminal,'calls':calls,'waits':clock.waits,'events':ctx.events}
    finally:CURRENT.reset(token)
try:
    print(json.dumps({'final':probe(json.loads(sys.stdin.readline()))},allow_nan=False),flush=True)
except Exception as e:
    print(json.dumps({'final':{'exception':type(e).__name__,'message':str(e)}}),flush=True)
