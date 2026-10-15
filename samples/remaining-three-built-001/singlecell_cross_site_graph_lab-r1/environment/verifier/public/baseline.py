"""Strong public CPU baseline; no hidden labels or private paths."""
import argparse,json,time
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz,vstack
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
p=argparse.ArgumentParser();p.add_argument('public');p.add_argument('output');p.add_argument('--components',type=int,default=64);a=p.parse_args()
root=Path(a.public);out=Path(a.output);out.mkdir(parents=True,exist_ok=True);began=time.monotonic()
train=load_npz(root/'data/train_features.npz');target=load_npz(root/'data/target_features.npz');labels=np.load(root/'data/train_labels.npy')
dev=np.load(root/'data/dev_indices.npy');dev_labels=np.load(root/'data/dev_labels.npy')
with threadpool_limits(limits=2):
 svd=TruncatedSVD(a.components,n_iter=5,random_state=713);z=svd.fit_transform(vstack([train,target]));scaler=StandardScaler();z=scaler.fit_transform(z)
 labelled=np.flatnonzero(labels>=0);fit_x=np.vstack([z[labelled],z[train.shape[0]+dev]]);fit_y=np.r_[labels[labelled],dev_labels]
 model=LogisticRegression(C=1,max_iter=300,class_weight='balanced',solver='lbfgs',random_state=713);model.fit(fit_x,fit_y)
 prediction=model.predict(z[train.shape[0]:]).astype(np.int64);np.save(out/'predictions.npy',prediction)
(out/'training_record.json').write_text(json.dumps({'public_data_only':True,'uses_public_dev_for_training':True,'fixed_seed':713,'components':a.components,'seconds':time.monotonic()-began},indent=2)+'\n')
