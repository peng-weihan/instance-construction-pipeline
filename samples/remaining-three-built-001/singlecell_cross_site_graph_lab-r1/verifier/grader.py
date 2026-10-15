import json
import numpy as np
from runtime import PUBLIC,PRIVATE,SubmissionError,check,result,scoring_constants
def grade(submission,suite):
    c=scoring_constants()
    try:p=np.load(submission/'predictions.npy',allow_pickle=False)
    except Exception:raise SubmissionError('predictions.npy missing or unreadable')
    if not isinstance(p,np.ndarray):raise SubmissionError('predictions.npy must be an array, not an archive')
    if p.shape!=(c['prediction_count'],) or p.dtype.kind not in 'iu' or (p<0).any() or (p>=c['class_count']).any():raise SubmissionError('prediction shape or integer class IDs invalid')
    indices=np.load(PRIVATE/(suite+'_indices.npy'));truth=np.load(PRIVATE/'target_labels.npy');batches=np.load(PRIVATE/'target_batches.npy');records=[];scores=[];checks=[check('prediction_contract',True)]
    for batch in sorted(set(batches[indices])):
        ix=indices[batches[indices]==batch];matrix=np.bincount(truth[ix]*c['class_count']+p[ix],minlength=c['class_count']**2).reshape(c['class_count'],c['class_count'])
        tp=np.diag(matrix);gold=matrix.sum(axis=1);pred=matrix.sum(axis=0);den=gold+pred
        f1=np.divide(2*tp,den,out=np.zeros(c['class_count'],dtype=float),where=den>0)
        recall=np.divide(tp,gold,out=np.zeros(c['class_count'],dtype=float),where=gold>0)
        score=float(f1[gold>0].mean());scores.append(score)
        records.append({'batch':str(batch),'cells':len(ix),'macro_f1':score,'f1_by_class':f1.tolist(),'recall_by_class':recall.tolist(),'confusion':matrix.tolist()})
        checks.extend(check(str(batch)+'/recall/'+str(i),gold[i]==0 or recall[i]>0,'no support' if gold[i]==0 else str(float(recall[i]))) for i in range(c['class_count']))
    return result(float(np.mean(scores)),checks,{'batches':records,'aggregation':'equal batch mean of declared-class macro-F1'})
