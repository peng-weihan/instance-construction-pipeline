"""A named deployment revision; preserve the original data and score formula."""
from pathlib import Path
import hashlib,json,shutil,tarfile
ROOT=Path(__file__).resolve().parents[2]
old=ROOT/'samples/remaining-three-built-001/singlecell_cross_site_graph_lab-r1'
new=old.with_name('singlecell_cross_site_graph_lab-r2')
new.mkdir()
for name in ['public','private','solution','verifier']:
    shutil.copytree(old/name,new/name)
for name in ['instruction.md','source_provenance.json']:
    shutil.copyfile(old/name,new/name)
p=new/'verifier/grader.py'
s=p.read_text().replace("    try:p=np.load(submission/'predictions.npy',allow_pickle=False)","    prediction_path=submission/'predictions.npy'\n    if prediction_path.is_symlink() or not prediction_path.is_file():raise SubmissionError('predictions.npy must be a regular file, not a symlink')\n    try:p=np.load(prediction_path,allow_pickle=False)")
s=s.replace("    indices=np.load(PRIVATE/(suite+'_indices.npy'))", "    p=p.astype(np.int64,copy=False)\n    indices=np.load(PRIVATE/(suite+'_indices.npy'))")
p.write_text(s)
src=ROOT/'materials/repos/neurips2021-topmethods'
shutil.copytree(src,new/'public/method_sources',ignore=shutil.ignore_patterns('.git','__pycache__','sample_data','*.h5ad','*.npy','*.npz','*.whl','*.pkl','*.pt'))
(new/'public/evaluate_dev.py').write_text('''import argparse,json
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score
p=argparse.ArgumentParser();p.add_argument('predictions');a=p.parse_args()
root=Path(__file__).resolve().parent;pred=np.load(a.predictions,allow_pickle=False)
idx=np.load(root/'data/dev_indices.npy');y=np.load(root/'data/dev_labels.npy')
assert isinstance(pred,np.ndarray) and pred.shape==(33883,) and pred.dtype.kind in 'iu'
print(json.dumps({'public_dev_macro_f1':f1_score(y,pred[idx],labels=np.unique(y),average='macro',zero_division=0),'dev_labels_may_be_used_for_training':True,'warning':'dev score is in-sample if these labels were used for training'}))
''')
extra='''
运行环境：工作目录 /home/workspace/cellgraph；数据在 data/，不是嵌套的 public/data/。
离线提供 numpy 2.2.6、scipy 1.15.3、scikit-learn 1.7.0、PyTorch 2.7.1 CPU、h5py 3.14.0、原始竞赛方法源码 method_sources/。资源4核CPU、16GiB内存，无GPU。
先运行 `python baseline.py . submission`；公开开发检查为 `python evaluate_dev.py submission/predictions.npy`。
完整学习预算21600秒，每600秒自动评分，也可使用 sforge-submit 主动提交。只对 submission/predictions.npy 评分；不要把模型和训练缓存放进submission。
公开开发标签可用于训练，此时开发集成绩属于训练内指标。固定反馈用于交互，独立审计标签始终隐藏。
'''
(new/'instruction.md').write_text((new/'instruction.md').read_text()+extra)
(new/'public/instruction.md').write_text((new/'instruction.md').read_text())
(new/'reference-predictions').mkdir()
shutil.copyfile(ROOT/'runs/remaining-three-001/singlecell-baseline-002/predictions.npy',new/'reference-predictions/predictions.npy')
meta=json.loads((new/'public/scoring_metadata.json').read_text())
meta['baseline_score']={'host_only_not_deployment_evidence':0.3885168478386856,'deployment_check':'pending'}
(new/'public/scoring_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
hashes={p.relative_to(new).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in new.rglob('*') if p.is_file()}
(new/'source-files.sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
archive=ROOT/'runs/remaining-three-001/singlecell-source-r2.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=1) as tar:tar.add(new,arcname=new.name)
print(archive,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
