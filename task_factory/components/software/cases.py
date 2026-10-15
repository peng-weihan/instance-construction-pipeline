"""Specification-derived expectations, authored separately from the implementation."""
import copy

def cases():
    rows=[]
    def add(name,group,c,expect):rows.append({'name':name,'group':group,'input':c,'expect':expect})
    def send(statuses,**kw):return dict(op='send',responses=[{'status':s} for s in statuses],**kw)
    add('global_override','policy',dict(op='policy',policy={'global':{'max_attempts':7}}),{'policy.max_attempts':7})
    add('method_override','policy',dict(op='policy',request='POST /jobs?q=1 HTTP/1.1\r\n\r\n',policy={'global':{'max_attempts':7},'endpoints':{'/jobs':{'defaults':{'max_attempts':5},'POST':{'max_attempts':2}}}}),{'policy.max_attempts':2})
    for key,value in [('max_attempts',True),('deadline_seconds',-1),('retry_statuses',['503']),('jitter_fraction',2),('extra',1)]:
        add('reject_'+key,'policy',dict(op='policy',policy={'global':{key:value}}),{'exception_present':True})
    add('retry_503','retry',send([503,503,200]),{'calls.length':3,'waits':[1.,2.],'terminal':'succeeded'})
    add('max_attempts','retry',send([503]*5,policy={'global':{'max_attempts':2}}),{'calls.length':2,'terminal':'failed'})
    add('retry_after_seconds','retry',dict(op='send',responses=[{'raw':'HTTP/1.1 429 Busy\r\nRetry-After: 4\r\n\r\n'},{'status':200}]),{'waits':[4.],'calls.length':2})
    add('retry_after_date','retry',dict(op='send',wall=1700000000,responses=[{'raw':'HTTP/1.1 503 Busy\r\nRetry-After: Tue, 14 Nov 2023 22:13:25 GMT\r\n\r\n'},{'status':200}]),{'waits':[5.]})
    add('malformed_retry_after','retry',dict(op='send',responses=[{'raw':'HTTP/1.1 503 Busy\r\nRetry-After: nonsense\r\n\r\n'},{'status':200}]),{'waits':[1.]})
    add('deadline_blocks_sleep','retry',send([503,200],policy={'global':{'deadline_seconds':1}}),{'calls.length':1,'waits':[],'terminal':'timed_out'})
    for method in ['GET','HEAD','PUT','DELETE','POST','PATCH']:
        safe=method in ['GET','HEAD','PUT','DELETE']
        add('idempotency_'+method,'idempotency',send([503,200],request=method+' /items HTTP/1.1\r\n\r\n'),{'calls.length':2 if safe else 1,'terminal':'succeeded' if safe else 'failed'})
    add('idempotency_explicit','idempotency',send([503,200],request='POST /jobs HTTP/1.1\r\nIdempotency-Key: SECRET_KEY\r\n\r\n',policy={'global':{'idempotency_header':'Idempotency-Key'}}),{'calls.length':2,'terminal':'succeeded','secret_free':True})
    add('unsafe_network_reset','idempotency',dict(op='send',request='POST /items HTTP/1.1\r\n\r\n',responses=[{'network_error':True},{'status':200}]),{'calls.length':1,'terminal':'failed'})
    init={'raw':'HTTP/1.1 202 Accepted\r\nLocation: https://api.test/jobs/1\r\n\r\n'}
    add('async_completion_final_get','async',dict(op='async',request='PUT /items/1 HTTP/1.1\r\n\r\n',responses=[init,{'status':202},{'status':200},{'status':200}]),{'statuses':['200','200'],'error':False,'waited':True,'calls.length':4})
    add('shared_deadline','async',dict(op='async',request='PUT /items/1 HTTP/1.1\r\n\r\n',policy={'global':{'deadline_seconds':2}},responses=[dict(init,elapsed=1),{'status':202}]),{'error':True,'terminal':'timed_out','calls.length':2})
    add('cancellation','async',dict(op='send',cancel_at=0,responses=[{'status':200}]),{'calls.length':0,'terminal':'cancelled'})
    resources=[{'id':'parent'},{'id':'child','parents':['parent']},{'id':'leaf','parents':['child']}]
    add('reverse_dependency','leases',dict(op='lease',resources=resources,created=[['parent',0],['child',0],['leaf',0]]),{'deleted':['leaf','child','parent'],'retained':[]})
    add('shared_parent_retained','leases',dict(op='lease',resources=resources,created=[['parent',2],['child',0]],release=['parent']),{'deleted':['child'],'retained':['parent']})
    add('leased_child_blocks_parent','leases',dict(op='lease',resources=resources,created=[['parent',0],['child',1]]),{'deleted':[],'retained':['parent','child']})
    add('cycle_rejected','leases',dict(op='lease',resources=[{'id':'a','parents':['b']},{'id':'b','parents':['a']}]),{'exception_present':True})
    spec={'resources':[{'id':'parent','request':'PUT /p HTTP/1.1\r\n\r\n','delete_request':'DELETE /p HTTP/1.1\r\n\r\n'},
                       {'id':'child','parents':['parent'],'request':'PUT /p/c HTTP/1.1\r\n\r\n','delete_request':'DELETE /p/c HTTP/1.1\r\n\r\n'}]}
    add('rollback_via_restler','leases',dict(op='workflow',spec=spec,responses=[{'status':201},{'status':400},{'status':204}]),{'completed':['parent'],'failed':'child','deleted':['parent'],'calls.length':3})
    add('full_workflow_cleanup','leases',dict(op='workflow',spec=spec,responses=[{'status':201},{'status':201},{'status':204},{'status':204}]),{'completed':['parent','child'],'deleted':['child','parent'],'calls.length':4})
    add('redacted_trace','trace',send([503,200],request='GET /items HTTP/1.1\r\nAuthorization: SECRET_AUTH\r\nIdempotency-Key: SECRET_KEY\r\n\r\n'),{'secret_free':True,'trace_schema':True,'calls.length':2})
    add('trace_failure','trace',send([400]),{'trace_schema':True,'terminal':'failed'})
    record={'request':'GET /items HTTP/1.1\r\n\r\n','responses':[{'raw':'HTTP/1.1 503 Busy\r\n\r\n'},{'raw':'HTTP/1.1 200 OK\r\n\r\n'}]}
    add('replay_deterministic','replay',dict(op='replay',records=[record],policy={'global':{'jitter_fraction':.2}}),{'same':True,'trace_schema':True})
    add('ordinary_success','replay',send([200]),{'status':'200','calls.length':1,'waits':[]})
    add('legacy_policy_disabled','replay',dict(op='legacy',enabled=False,responses=[{'status':200}]),{'status':'200','calls.length':1,'waits':[]})
    add('legacy_retry_compatibility','replay',dict(op='legacy',enabled=False,responses=[{'status':429},{'status':200}]),{'status':'200','calls.length':2,'waits':[5]})
    return rows

def audit_cases():
    return [
      {'name':'audit_path_default','group':'policy','input':{'op':'policy','request':'PUT /audit HTTP/1.1\r\n\r\n','policy':{'global':{'deadline_seconds':3},'endpoints':{'/audit':{'defaults':{'deadline_seconds':4}}}}},'expect':{'policy.deadline_seconds':4}},
      {'name':'audit_capped_backoff','group':'retry','input':{'op':'send','policy':{'global':{'max_attempts':5,'base_delay_seconds':.5,'delay_cap_seconds':1}},'responses':[{'status':503}]*4+[{'status':200}]},'expect':{'waits':[.5,1,1,1],'calls.length':5}},
      {'name':'audit_patch_key','group':'idempotency','input':{'op':'send','request':'PATCH /audit HTTP/1.1\r\nX-Request-Key: key\r\n\r\n','policy':{'global':{'idempotency_header':'X-Request-Key'}},'responses':[{'status':503},{'status':200}]},'expect':{'calls.length':2,'terminal':'succeeded'}},
      {'name':'audit_late_response','group':'async','input':{'op':'send','policy':{'global':{'deadline_seconds':2}},'responses':[{'status':200,'elapsed':2}]},'expect':{'calls.length':1,'terminal':'timed_out'}},
      {'name':'audit_cleanup_budget','group':'leases','input':{'op':'lease','policy':{'global':{'cleanup_deadline_seconds':0}},'resources':[{'id':'a'},{'id':'b','parents':['a']}],'created':[['a',0],['b',0]]},'expect':{'deleted':[],'retained':['a','b']}},
      {'name':'audit_unauthorized_trace','group':'trace','input':{'op':'send','request':'GET /audit HTTP/1.1\r\nAuthorization: SECRET_AUTH\r\n\r\n','responses':[{'status':401}]},'expect':{'secret_free':True,'trace_schema':True,'terminal':'failed'}},
      {'name':'audit_replay_retry_after','group':'replay','input':{'op':'replay','records':[{'request':'GET /audit HTTP/1.1\r\n\r\n','responses':[{'raw':'HTTP/1.1 429 Busy\r\nRetry-After: 2\r\n\r\n'},{'raw':'HTTP/1.1 200 OK\r\n\r\n'}]}]},'expect':{'same':True,'trace_schema':True}}
    ]
