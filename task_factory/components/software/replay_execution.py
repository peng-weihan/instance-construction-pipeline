"""Replay a sanitized fault transcript; no live network calls."""
import argparse,json,random
from engine.core.execution_policy import Context,resolve,send
from engine.transport_layer.response import HttpResponse
class ReplayClock:
    def __init__(self,wall=0):self.t=0.;self.w=wall
    def monotonic(self):return self.t
    def wall(self):return self.w+self.t
    def sleep(self,t):self.t+=t
def replay(records,policy):
    events=[]
    for record in records:
        raw=record['request'];method,path=raw.split()[:2];clock=ReplayClock(record.get('wall',0))
        ctx=Context(resolve(policy,method,path),clock,random.Random(record.get('seed',0)));responses=iter(record['responses'])
        def transport(data,remaining,retry):
            r=next(responses);clock.sleep(r.get('elapsed',0));return r.get('success',True),HttpResponse(r['raw'])
        send(raw,transport,policy,ctx);events.extend(ctx.events)
    return events
def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--policy',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    records=[json.loads(s) for s in open(a.input) if s.strip()]
    events=replay(records,json.load(open(a.policy)))
    with open(a.output,'w') as f:
        for e in events:f.write(json.dumps(e,sort_keys=True)+'\n')
if __name__=='__main__':main()
