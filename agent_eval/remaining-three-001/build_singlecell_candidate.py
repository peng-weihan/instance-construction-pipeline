"""Construct a real-data, cross-site cell label prediction candidate."""
from pathlib import Path
import csv,hashlib,json,shutil
import h5py,numpy as np
from scipy.sparse import csc_matrix,save_npz
ROOT=Path(__file__).resolve().parents[2]
TASK=ROOT/'samples/remaining-three-built-001/singlecell_cross_site_graph_lab-r1'
for path in ['public/data','public/submission','private','solution','verifier','environment/agent','environment/verifier']:(TASK/path).mkdir(parents=True,exist_ok=False)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
source=ROOT/'materials/datasets/neurips2021-cite/gex.h5ad'
with h5py.File(source,'r') as f:
 x=f['X'];X=csc_matrix((x['data'][:],x['indices'][:],x['indptr'][:]),shape=tuple(x.attrs['shape'])).tocsr()
 cats=f['obs/__categories'];batch_names=cats['batch'].asstr()[:];batches=batch_names[f['obs/batch'][:]]
 type_names=cats['cell_type'].asstr()[:];original_y=f['obs/cell_type'][:]
 genes=f['var/_index'].asstr()[:]
training_batches=['s1d1','s1d2','s2d1','s2d4','s2d5']
train_mask=np.isin(batches,training_batches);counts=np.bincount(original_y[train_mask],minlength=len(type_names))
# Define supported categories from training data only; hidden labels do not
# choose the vocabulary, features or reference hyperparameters.
kept=np.flatnonzero(counts>=100);lookup=np.full(len(type_names),-1,dtype=np.int64);lookup[kept]=np.arange(len(kept))
y=lookup[original_y];keep=y>=0;X=X[keep];y=y[keep];batches=batches[keep]
train=np.flatnonzero(np.isin(batches,training_batches));target=np.flatnonzero(~np.isin(batches,training_batches))
mean=np.asarray(X[train].mean(axis=0)).ravel();variance=np.asarray(X[train].power(2).mean(axis=0)).ravel()-mean**2
gene_ids=np.argsort(variance,kind='stable')[-4000:];X=X[:,gene_ids].astype(np.float32)
rng=np.random.default_rng(2026101504);labels=np.full(len(train),-1,dtype=np.int64)
for c in range(len(kept)):
 positions=np.flatnonzero(y[train]==c);chosen=rng.choice(positions,size=min(len(positions),max(20,int(.08*len(positions)))),replace=False);labels[chosen]=c
save_npz(TASK/'public/data/train_features.npz',X[train]);save_npz(TASK/'public/data/target_features.npz',X[target])
np.save(TASK/'public/data/train_labels.npy',labels);np.save(TASK/'private/target_labels.npy',y[target])
dev=np.flatnonzero(batches[target]=='s1d3');feedback=np.flatnonzero(batches[target]=='s3d1');audit=np.flatnonzero(np.isin(batches[target],['s3d6','s3d7']))
assert len(dev)+len(feedback)+len(audit)==len(target)
np.save(TASK/'public/data/dev_indices.npy',dev);np.save(TASK/'public/data/dev_labels.npy',y[target][dev])
for name,indices in [('dev',dev),('feedback',feedback),('audit',audit)]:np.save(TASK/'private'/(name+'_indices.npy'),indices)
np.save(TASK/'private/target_batches.npy',batches[target].astype('U8'))
np.save(TASK/'public/data/train_batches.npy',batches[train].astype('U8'));np.save(TASK/'public/data/target_batches.npy',batches[target].astype('U8'))
(TASK/'public/data/genes.txt').write_text('\n'.join(genes[gene_ids])+'\n')
dump(TASK/'public/classes.json',{str(i):type_names[k] for i,k in enumerate(kept)})
spec={'train_cells':len(train),'target_cells':len(target),'genes':len(gene_ids),'classes':len(kept),
      'public_labels':int((labels>=0).sum()),'dev_cells':len(dev),'feedback_cells':len(feedback),'audit_cells':len(audit),
      'train_batches':training_batches,'dev_batches':['s1d3'],'feedback_batches':['s3d1'],'audit_batches':['s3d6','s3d7'],
      'class_selection':'at least 100 full-source training-batch cells; no target-label-dependent selection',
      'gene_selection':'4000 highest-variance genes on training cells only',
      'public_target_annotations':'batch only; ADT-derived annotations and pseudotime excluded'}
dump(TASK/'public/data_contract.json',spec);print(spec,flush=True)
source_manifest=json.loads((ROOT/'research/remaining-three-2026-10-15/single-cell-source-manifest.json').read_text())
dump(TASK/'source_provenance.json',{'category':'Scientific Problems & ML','anchor':'graph_node_classification',
 'relationship':'same node-label learning family; real cross-site biological cell data instead of the original graph',
 'sources':source_manifest,'labels':'original curated source cell types, not simulated labels',
 'status':'constructed_host_unverified','six_hour_difficulty':'unmeasured'})
shutil.copyfile(ROOT/'research/remaining-three-2026-10-15/single-cell-data-LICENSE.txt',TASK/'public/DATA_LICENSE.txt')
instruction='''# 跨中心单细胞图学习与分类

在离线 CPU 环境中，为来自另一实验中心和新供者的细胞预测类别。数据为真实单细胞 RNA 表达，不是脚本合成标签。可以构造细胞近邻图、细胞—基因图，或采用强线性/树/神经网络方法；不会因为没有使用 GNN 而扣分。允许 sklearn、PyTorch 和公开方法源码，不允许读取隐藏类别。

public/data 有训练细胞的4000维稀疏表达、约8%类别标签（-1为未标注）、全部待预测细胞表达和实验批次。public/classes.json 是类别字典。公开开发批次的标签也已提供，可用于模型选择和训练；固定反馈与审计类别不公开。数据没有提供可泄漏类别的 cell_type、ADT伪时间或原始注释表。

训练批次来自两个中心；公开开发在已见中心的新供者上，固定反馈在新中心的已见供者上，审计在新中心的两个新供者上。模型要同时处理标签稀少、类别不平衡、批次偏移和新供者泛化。给定目标表达可以参与无监督表示学习和建图。只要不使用隐藏标签，转导学习合法。

提交 submission/predictions.npy，长度与target_features.npz行数一致，整数类别ID严格对应classes.json。分数仅由这份固定数组决定，训练中的进程状态不影响评分。每个目标批次在有真实样本的类别上按宏平均F1评分，再对该suite的批次等权平均，范围0到1、越高越好；失败类别、召回率和混淆摘要随反馈返回。某类只要有一个真实样本就计分，不按频率删掉难类；没有真实样本的类不设不可获得的奖励项。工作预算六小时，可每十分钟冻结一次预测继续改进。

建议先跑公开的SVD+逻辑回归基线，再研究批次校正、稀疏标签传播、伪标签质量、罕见类召回与多模型组合。数据源为NeurIPS 2021 Open Problems BMMC公开数据，修改了训练监督与跨中心划分，未复制EdgeBench原题数据；许可和采集版本随题交付。本小样尚未验证六小时增长曲线。
'''
for p in [TASK/'instruction.md',TASK/'public/instruction.md']:p.write_text(instruction)
dump(TASK/'public/scoring_metadata.json',{'reward_type':'bounded_continuous','direction':'higher_is_better','range':[0,1],
 'formula':'mean_over_fixed_suite_batches(mean_over_classes_with_true_support(2*TP/(2*TP+FP+FN)))',
 'constants':{'class_count':len(kept),'zero_division':0,'prediction_count':len(target)},
 'baseline':'public/baseline.py, public-data-only SVD and logistic regression','upper':{'value':1,'meaning':'perfect labels; not demonstrated by learned model'},
 'aggregation':'best valid snapshot on fixed feedback batch','baseline_score':None,'nop_score':None,'three_model_run_mean':None})
runtime=(ROOT/'samples/remaining-three-built-001/finance-task-r3/verifier/runtime.py').read_text();(TASK/'verifier/runtime.py').write_text(runtime)
grader='''import json
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
'''
(TASK/'verifier/grader.py').write_text(grader)
baseline='''"""Strong public CPU baseline; no hidden labels or private paths."""
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
(out/'training_record.json').write_text(json.dumps({'public_data_only':True,'uses_public_dev_for_training':True,'fixed_seed':713,'components':a.components,'seconds':time.monotonic()-began},indent=2)+'\\n')
'''
(TASK/'public/baseline.py').write_text(baseline);(TASK/'solution/solve.py').write_text(baseline)
np.save(TASK/'public/submission/predictions.npy',np.full(len(target),int(np.bincount(labels[labels>=0]).argmax()),dtype=np.int64))
base=ROOT/'samples/remaining-three-built-001/finance-task-r3/environment'
for side in ['agent','verifier']:
 ctx=TASK/'environment'/side;shutil.copytree(TASK/'public',ctx/'public')
 shutil.copyfile(base/side/'capture_build.py',ctx/'capture_build.py');docker=(base/side/'Dockerfile').read_text()
 docker=docker.replace('cmake==3.31.6','cmake==3.31.6 scikit-learn==1.7.0 h5py==3.14.0')
 if side=='agent':docker=docker.replace('RUN mkdir /workspace && cp -a /opt/public/. /workspace/','RUN mkdir -p /home/workspace/cellgraph && cp -a /opt/public/. /home/workspace/cellgraph/').replace('WORKDIR /workspace','WORKDIR /home/workspace/cellgraph')
 else:
  shutil.copytree(TASK/'private',ctx/'private');shutil.copytree(TASK/'verifier',ctx/'verifier')
  docker=docker.replace('/judge/verifier/entry.py','/judge/verifier/judge_entry.py')
 (ctx/'Dockerfile').write_text(docker)
shutil.copyfile(Path(__file__).parent/'judge_entry.py',TASK/'verifier/judge_entry.py');shutil.copyfile(TASK/'verifier/judge_entry.py',TASK/'environment/verifier/verifier/judge_entry.py')
dump(TASK/'AUTHORING_REPORT.json',{'state':'constructed_unverified','synthetic_measurements':False,'model_runs':0,'docker_verified':False,'native_harbor_verified':False,
 'open_gaps':['strong baseline runtime and cheap shortcut screening','Harbor schema/environment mapping','six-hour difficulty and growth','offline Torch toolchain availability and optional graph baseline'],
 'construction':'real source data -> training-only feature and class selection -> fixed cross-site splits -> frozen prediction verifier'})
print(TASK)
