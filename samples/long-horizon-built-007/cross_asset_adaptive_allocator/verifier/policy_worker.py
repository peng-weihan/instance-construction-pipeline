"""JSON-lines policy adapter. Future returns and trusted scoring never enter here."""
import contextlib,json,sys
sys.path.insert(0,'submission')
with contextlib.redirect_stdout(sys.stderr):import policy
for line in sys.stdin:
    try:
        request=json.loads(line)
        with contextlib.redirect_stdout(sys.stderr):
            if request['op']=='initialize':
                user_state=policy.initialize(request['metadata']);answer={'initialized':True}
            else:
                state=dict(request['state']);state['user_state']=user_state
                answer=policy.decide(request['history'],state)
                if 'user_state' in answer:user_state=answer.pop('user_state')
        print(json.dumps(answer,allow_nan=False),flush=True)
    except Exception as e:
        print(json.dumps({'policy_error':type(e).__name__,'message':str(e)[:300]}),flush=True)
