"""RESTler workflow entrypoint: real request/async paths and dependency registration."""
from engine.core import request_utilities,async_request_utilities
from engine.core.execution_policy import LeaseGraph,Context,CURRENT,resolve
from engine import dependencies
from restler_settings import Settings

def execute_workflow(spec,context=None):
    graph=LeaseGraph(spec['resources']);by_id={r['id']:r for r in spec['resources']}
    first=spec['resources'][0]['request'].split() if spec['resources'] else ['GET','/']
    ctx=context or Context(resolve(Settings().execution_policy,first[0],first[1]));token=CURRENT.set(ctx)
    completed=[];failed=None
    try:
        for name in graph.order:
            r=by_id[name]
            if ctx.stopped():failed=name;break
            response=request_utilities.send_request_data(r['request'])
            responses,error,_=async_request_utilities.try_async_poll(r['request'],response,ctx.policy['deadline_seconds'])
            if error or ctx.terminal in ['cancelled','timed_out'] or response.status_code not in ['200','201','202','204']:
                failed=name;break
            # Register existing RESTler dependencies without also enqueuing legacy GC.
            dependencies.set_variable_no_gc(name,r.get('value',name))
            graph.created(name,r.get('leases',1));completed.append(name)
        for name in completed:
            # Release this workflow's lease; explicitly retained external leases survive.
            graph.release(name)
        def delete(name,remaining):
            cleanup=Context(dict(ctx.policy,deadline_seconds=remaining),ctx.clock,ctx.rng)
            t=CURRENT.set(cleanup)
            try:
                response=request_utilities.send_request_data(by_id[name]['delete_request'],req_timeout_sec=remaining)
                return response.status_code in ['200','202','204','404'] and cleanup.terminal!='timed_out'
            finally:CURRENT.reset(t)
        deleted,remaining=graph.cleanup(delete,ctx)
        return {'completed':completed,'failed':failed,'deleted':deleted,'retained':remaining,'events':ctx.events}
    finally:CURRENT.reset(token)
