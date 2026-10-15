"""Reference execution policies for RESTler. Injectable clock/transport; no test fixtures."""
import contextvars,copy,email.utils,json,math,random,time
from urllib.parse import urlsplit

DEFAULT={'max_attempts':4,'deadline_seconds':30.,'cleanup_deadline_seconds':10.,
         'base_delay_seconds':1.,'delay_cap_seconds':8.,'jitter_fraction':0.,
         'retry_statuses':[429,503],'idempotency_header':None}
CURRENT=contextvars.ContextVar('restler_execution_context',default=None)
class PolicyError(ValueError):pass
class Clock:
    def monotonic(self):return time.monotonic()
    def wall(self):return time.time()
    def sleep(self,t):time.sleep(t)

def validate_policy(config):
    if not isinstance(config,dict):raise PolicyError('execution_policy: expected object')
    if set(config)-{'schema_version','global','endpoints'}:raise PolicyError('execution_policy: unknown key')
    if type(config.get('schema_version',1))!=int or config.get('schema_version',1)!=1:raise PolicyError('schema_version: expected integer 1')
    def fields(d,path):
        if not isinstance(d,dict):raise PolicyError(path+': expected object')
        for k,v in d.items():
            where=path+'.'+k
            if k not in DEFAULT:raise PolicyError(where+': unknown key')
            if k=='idempotency_header':
                if v is not None and (not isinstance(v,str) or not v or '\r' in v or '\n' in v):raise PolicyError(where)
            elif k=='retry_statuses':
                if not isinstance(v,list) or any(type(s)!=int or not 100<=s<=599 for s in v):raise PolicyError(where)
            elif k=='max_attempts':
                if type(v)!=int or v<1:raise PolicyError(where)
            elif isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or (k=='jitter_fraction' and v>1):raise PolicyError(where)
    fields(config.get('global',{}),'global')
    endpoints=config.get('endpoints',{})
    if not isinstance(endpoints,dict):raise PolicyError('endpoints')
    for path,methods in endpoints.items():
        if not isinstance(path,str) or not path.startswith('/') or not isinstance(methods,dict):raise PolicyError('endpoints.'+str(path))
        for method,fields_ in methods.items():
            if method not in ['defaults','GET','HEAD','PUT','DELETE','POST','PATCH','OPTIONS']:raise PolicyError('endpoints.'+path+'.'+method)
            fields(fields_,'endpoints.'+path+'.'+method)
    return copy.deepcopy(config)

def resolve(config,method,path):
    validate_policy(config);p=copy.deepcopy(DEFAULT);p.update(config.get('global',{}))
    endpoint=config.get('endpoints',{}).get(urlsplit(path).path,{})
    p.update(endpoint.get('defaults',{}));p.update(endpoint.get(method.upper(),{}));return p

class Context:
    def __init__(self,policy,clock=None,rng=None,cancelled=None):
        self.policy=policy;self.clock=clock or Clock();self.rng=rng or random.Random(0)
        self.start=self.clock.monotonic();self.deadline=self.start+policy['deadline_seconds']
        self.cancelled=cancelled or (lambda:False);self.events=[];self.terminal=None
    def emit(self,event,attempt=0,decision='',reason='',request_id='',resource_id=''):
        self.events.append(dict(event_index=len(self.events),request_id=request_id,resource_id=resource_id,
            event=event,attempt=attempt,elapsed_ms=round(1000*(self.clock.monotonic()-self.start),6),decision=decision,reason=reason))
    def stopped(self):
        if self.cancelled():self.terminal='cancelled'
        elif self.clock.monotonic()>=self.deadline:self.terminal='timed_out'
        else:return False
        self.emit('terminal',decision=self.terminal);return True

def request_parts(data):
    lines=data.split('\r\n');first=lines[0].split();headers={}
    for s in lines[1:]:
        if not s:break
        if ':' in s:k,v=s.split(':',1);headers[k.lower()]=v.strip()
    return first[0],first[1],headers

def send(data,transport,config,context=None):
    from engine.transport_layer.response import HttpResponse
    method,path,headers=request_parts(data);policy=resolve(config,method,path)
    ctx=context or Context(policy);request_id=f'r{sum(e["event"]=="request" for e in ctx.events)}'
    ctx.emit('request',request_id=request_id)
    key=policy['idempotency_header'];safe=method in ['GET','HEAD','PUT','DELETE'] or bool(key and headers.get(key.lower()))
    response=HttpResponse();response._execution_context=ctx
    for attempt in range(1,policy['max_attempts']+1):
        if ctx.stopped():break
        ctx.emit('attempt',attempt,request_id=request_id)
        try:success,response=transport(data,max(0.,ctx.deadline-ctx.clock.monotonic()),attempt>1)
        except (OSError,TimeoutError):success=False;response=HttpResponse()
        response._execution_context=ctx
        if ctx.stopped():break
        status=int(response.status_code) if response.status_code and response.status_code.isdigit() else 0
        retry=(not success or status in policy['retry_statuses']) and safe
        if not retry or attempt==policy['max_attempts']:
            ctx.terminal='succeeded' if success and 200<=status<300 else 'failed'
            ctx.emit('terminal',attempt,ctx.terminal,request_id=request_id);return response
        delay=min(policy['delay_cap_seconds'],policy['base_delay_seconds']*2**(attempt-1))
        retry_after={k.lower():v for k,v in response.headers_dict.items()}.get('retry-after','')
        try:
            value=float(retry_after)
            if not math.isfinite(value) or value<0:raise ValueError()
        except (ValueError,TypeError):
            try:value=max(0.,email.utils.parsedate_to_datetime(retry_after).timestamp()-ctx.clock.wall())
            except (ValueError,TypeError,OverflowError):value=0.
        delay=max(delay,value)*ctx.rng.uniform(1-policy['jitter_fraction'],1+policy['jitter_fraction'])
        if ctx.clock.monotonic()+delay>=ctx.deadline:
            ctx.terminal='timed_out';ctx.emit('terminal',attempt,'timed_out','retry_would_exceed_deadline',request_id);break
        ctx.emit('wait',attempt,'retry',format(delay,'.12g'),request_id);ctx.clock.sleep(delay)
    response._execution_context=ctx;return response

def send_from_restler(data,timeout=None,reconnect=None,http_sock=None):
    from restler_settings import Settings
    from engine.transport_layer.messaging import HttpSock
    from engine.core import request_utilities as ru
    settings=Settings();sock=http_sock
    if sock is None:
        try:sock=ru.threadLocal.main_sock
        except AttributeError:sock=HttpSock(settings.connection_settings);ru.threadLocal.main_sock=sock
    def transport(raw,remaining,retry):
        limit=min(remaining,timeout if timeout is not None else settings.max_request_execution_time)
        return sock.sendRecv(raw,limit,reconnect=bool(retry or reconnect or settings.reconnect_on_every_request))
    return send(data,transport,settings.execution_policy,CURRENT.get())

def poll_from_restler(request_data,response,max_wait,poll_delete_status=False):
    from engine.core import request_utilities as ru,async_request_utilities as au
    ctx=getattr(response,'_execution_context',None)
    if ctx is None:return [response],False,False
    data,in_response=au.get_polling_request(response)
    if not data or max_wait<=0:return [response],False,False
    ctx.deadline=min(ctx.deadline,ctx.clock.monotonic()+max_wait)
    token=CURRENT.set(ctx)
    try:
        while not ctx.stopped():
            polled=ru.send_request_data(data)
            if ctx.terminal in ['timed_out','cancelled']:break
            code=int(polled.status_code or 0)
            if code>=300:return [response],True,True
            if in_response:done=code in [200,201]
            else:
                try:state=json.loads(polled.json_body).get('status','').lower()
                except Exception:return [response],True,True
                if state in ['failed','canceled','cancelled']:return [response],True,True
                done=state=='succeeded'
            if done:
                out=[polled]
                if not poll_delete_status and not ctx.stopped():
                    final=au.try_parse_GET_request(request_data)
                    if final is not None and not ctx.stopped():out.insert(0,final)
                return out,ctx.terminal in ['timed_out','cancelled'],True
            if ctx.clock.monotonic()+1>=ctx.deadline:ctx.terminal='timed_out';break
            ctx.clock.sleep(1)
        return [response],True,True
    finally:CURRENT.reset(token)

class LeaseGraph:
    def __init__(self,spec):
        self.nodes={n['id']:{'parents':list(n.get('parents',[])),'refs':0,'created':False} for n in spec}
        if len(self.nodes)!=len(spec):raise PolicyError('duplicate resource id')
        seen=set();visiting=set();order=[]
        def visit(name):
            if name not in self.nodes:raise PolicyError('unknown parent '+name)
            if name in visiting:raise PolicyError('resource cycle')
            if name in seen:return
            visiting.add(name)
            for parent in self.nodes[name]['parents']:visit(parent)
            visiting.remove(name);seen.add(name);order.append(name)
        for n in self.nodes:visit(n)
        self.order=order
    def created(self,name,refs=1):
        n=self.nodes[name];n['created']=True;n['refs']+=refs
    def acquire(self,name):
        if not self.nodes[name]['created']:raise PolicyError('resource not created')
        self.nodes[name]['refs']+=1
    def release(self,name):
        if self.nodes[name]['refs']<=0:raise PolicyError('lease underflow')
        self.nodes[name]['refs']-=1
    def cleanup(self,delete,ctx):
        deadline=ctx.clock.monotonic()+ctx.policy['cleanup_deadline_seconds'];deleted=[]
        for name in reversed(self.order):
            n=self.nodes[name]
            children=[x for x in self.nodes.values() if name in x['parents'] and x['created']]
            if not n['created'] or n['refs'] or children:continue
            if ctx.clock.monotonic()>=deadline:break
            if delete(name,deadline-ctx.clock.monotonic()):
                n['created']=False;deleted.append(name);ctx.emit('cleanup',decision='deleted',resource_id=name)
        remaining=[n for n in self.order if self.nodes[n]['created']]
        if remaining:ctx.emit('cleanup',decision='cleanup_incomplete',reason='resources_retained')
        return deleted,remaining
