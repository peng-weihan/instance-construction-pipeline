import argparse,json
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score
p=argparse.ArgumentParser();p.add_argument('predictions');a=p.parse_args()
root=Path(__file__).resolve().parent;pred=np.load(a.predictions,allow_pickle=False)
idx=np.load(root/'data/dev_indices.npy');y=np.load(root/'data/dev_labels.npy')
assert isinstance(pred,np.ndarray) and pred.shape==(33883,) and pred.dtype.kind in 'iu'
print(json.dumps({'public_dev_macro_f1':f1_score(y,pred[idx],labels=np.unique(y),average='macro',zero_division=0),'dev_labels_may_be_used_for_training':True,'warning':'dev score is in-sample if these labels were used for training'}))
