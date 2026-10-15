"""JSONL stdin: {history: [[r1,...,r49],...], weights: [w1,...,w49]}.
One JSON object per line to stdout: variance_daily, q01_daily, q05_daily.
Naive reference starter; improve the risk methodology. Missing rows prefiltered.
"""
import json,sys,math
def predict(req):
    values=[sum(x*w for x,w in zip(r,req['weights'])) for r in req['history'][-252:]]
    mean=sum(values)/len(values)
    variance=max(1e-8,sum((x-mean)**2 for x in values)/len(values))
    return dict(variance_daily=variance,q01_daily=mean-2.326347874*math.sqrt(variance),q05_daily=mean-1.644853627*math.sqrt(variance))
if __name__=='__main__':
    for line in sys.stdin: print(json.dumps(predict(json.loads(line))))
