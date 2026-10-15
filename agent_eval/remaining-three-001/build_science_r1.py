"""Construct a coupled inverse problem from pinned USGS transport material."""
from pathlib import Path
import csv, hashlib, importlib.util, json, shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'samples/long-horizon-built-007/layered_aquifer_source_lab'
TASK=ROOT/'samples/remaining-three-built-001/science-task-r1';shutil.copytree(BASE,TASK)
HERE=Path(__file__).parent
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
scene=json.loads((BASE/'public/scene.json').read_text());scene['name']='DualDomain-TwoSource-62';scene['time_step_days']=.5
for layer in scene['layers']:layer.pop('R')
scene['storage']='Langmuir mobile storage plus kinetic exchange with immobile water'
scene['calibration_source']={'cx':7.,'cy':0.,'cz':0.,'hx':1.5,'hy':1.,'hz':.7,'t_start':0.,'duration':90.,'rate0':.15,'rate1':.3,'rate2':.08}
bounds={'velocity_scale':[.65,1.5],'diffusion_scale':[.5,1.8],'capacity':[.025,.18],'affinity':[10,120],
        'immobile_ratio':[.2,1.5],'exchange':[.004,.08],'decay':[.0005,.008]}
for i,xrange,trange in [(1,[7,13],[0,60]),(2,[14,22],[30,150])]:
    for k,v in {'cx':xrange,'cy':[-5,5],'cz':[-2,2],'hx':[1,4],'hy':[.5,2.5],'hz':[.3,1.5],
                't_start':trange,'duration':[60,220],'rate0':[.005,.22],'rate1':[.005,.22],'rate2':[.005,.22]}.items():bounds[f's{i}_{k}']=v
truth={'velocity_scale':1.18,'diffusion_scale':.82,'capacity':.083,'affinity':42.,'immobile_ratio':.67,'exchange':.019,'decay':.0022}
for i,values in [(1,[9.6,-2.1,-.8,2.8,1.1,.7,12,132,.065,.145,.04]),(2,[18.4,2.2,.9,2.2,1.6,.8,69,178,.08,.035,.11])]:
    for key,value in zip(['cx','cy','cz','hx','hy','hz','t_start','duration','rate0','rate1','rate2'],values):truth[f's{i}_{key}']=value
dump(TASK/'public/scene.json',scene);dump(TASK/'public/source_bounds.json',bounds);dump(TASK/'private/truth.json',truth)
shutil.copyfile(HERE/'science_model.py',TASK/'public/simulator.py')
shutil.copyfile(HERE/'science_model.py',TASK/'verifier/forward.py')
shutil.copyfile(HERE/'science_generator.py',TASK/'private/generate_scene.py')
spec=importlib.util.spec_from_file_location('label_generator',HERE/'science_generator.py');generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
spec=importlib.util.spec_from_file_location('public_forward',HERE/'science_model.py');forward=importlib.util.module_from_spec(spec);spec.loader.exec_module(forward)
pubdays=[40.,80.,120.,180.,260.,360.,480.];auditdays=[60.,100.,150.,220.,310.,430.,560.,660.]
days=sorted(set(pubdays+auditdays));rng=np.random.default_rng(2026101501);tables={'public':[],'feedback':[],'audit':[]};errors={}
for experiment in ['calibration','contaminant']:
    expected=generator.states(scene,truth,days,experiment);actual=forward.simulate(scene,truth,days,experiment)
    error=max(float(np.max(np.abs(expected[d]-actual[d]))) for d in days);assert error<1e-10;errors[experiment]=error
    for ix in range(3,24,2):
        for iy in [4,6,8,10,12]:
            for iz in [2,4,6]:
                split=['public','feedback','audit'][(ix//2+iy//2+iz//2)%3]
                for day in (auditdays if split=='audit' else pubdays):
                    value=float(expected[day][ix,iy,iz])
                    # A fixed monitoring lattice, with measured non-detects retained
                    # sparsely. This is observation design, not fabricated labels.
                    if value<.0003 and (ix+iy+iz+int(day))%7:continue
                    measured=value*float(np.exp(rng.normal(0,.05))) if split=='public' else value
                    censored=split=='public' and measured<.0003
                    tables[split].append([experiment,f'{split}_{ix}_{iy}_{iz}',ix,iy,iz,day,'' if censored else measured,int(censored),.0003])
    print(experiment,'independent error',error,flush=True)
for split,rows in tables.items():
    assert all(sum(r[0]==e for r in rows)>20 for e in ['calibration','contaminant'])
    path=TASK/('public' if split=='public' else 'private')/(split+'_observations.csv')
    with path.open('w') as f:
        w=csv.writer(f);w.writerow(['experiment','well','ix','iy','iz','day','concentration','below_detection','detection_limit']);w.writerows(rows)
dump(TASK/'private/generation_record.json',{'seed':2026101501,'synthetic':True,'model':'own conservative dual-domain stencil; not a MODFLOW execution',
 'observation_counts':{k:len(v) for k,v in tables.items()},'independent_sparse_agreement':errors,'numerically_validated':True})
dump(TASK/'public/submission/answer.json',{k:sum(v)/2 for k,v in bounds.items()})

grader='''import csv,json
import numpy as np
from runtime import PUBLIC,PRIVATE,SubmissionError,check,result,finite,scoring_constants
from forward import simulate
def grade(submission,suite):
    c=scoring_constants()
    try:p=json.loads((submission/'answer.json').read_text())
    except Exception:raise SubmissionError('answer.json must be an object')
    bounds=json.loads((PUBLIC/'source_bounds.json').read_text())
    if not isinstance(p,dict) or set(p)!=set(bounds) or any(not finite(p[k]) or not bounds[k][0]<=p[k]<=bounds[k][1] for k in bounds):raise SubmissionError('all 29 parameters must be finite and in bounds')
    scene=json.loads((PUBLIC/'scene.json').read_text());g=scene['grid']
    for source in [1,2]:
        for i,key in enumerate('xyz'):
            if p[f's{source}_c{key}']-p[f's{source}_h{key}']<g['origin_m'][i] or p[f's{source}_c{key}']+p[f's{source}_h{key}']>g['origin_m'][i]+g['shape_xyz'][i]*g['spacing_m'][i]:raise SubmissionError('source outside domain')
    rows=list(csv.DictReader(((PUBLIC if suite=='public' else PRIVATE)/(suite+'_observations.csv')).open()))
    scores=[];checks=[check('physical_parameters',True)];metrics={}
    for experiment in ['calibration','contaminant']:
        selected=[r for r in rows if r['experiment']==experiment]
        pred=simulate(scene,p,sorted({float(r['day']) for r in selected}),experiment)
        a=np.array([pred[float(r['day'])][int(r['ix']),int(r['iy']),int(r['iz'])] for r in selected])
        y=np.array([float(r['concentration']) if r['concentration'] else float(r['detection_limit']) for r in selected])
        cens=np.array([r['below_detection']=='1' for r in selected]);a[cens]=np.maximum(a[cens],y[cens])
        if not np.isfinite(a).all() or (a < -c['negative_prediction_tolerance']).any():raise SubmissionError('nonfinite or negative prediction')
        a=np.maximum(a,0);relative=float(np.sqrt(np.mean((a-y)**2))/max(np.sqrt(np.mean(y*y)),c['relative_rmse_floor']))
        logarithmic=float(np.sqrt(np.mean((np.log1p(a/c['log_scale'])-np.log1p(y/c['log_scale']))**2)))
        scores.append(1/(1+c['relative_mse_weight']*relative**2+c['log_mse_weight']*logarithmic**2))
        metrics[experiment]={'relative_rmse':relative,'log_rmse':logarithmic,'observations':len(selected),'score':scores[-1]}
        checks.extend([check(experiment+'/finite_prediction',True),check(experiment+'/relative_rmse_below_one',relative<1),check(experiment+'/log_rmse_below_one',logarithmic<1)])
    return result(sum(scores)/len(scores),checks,{'experiments':metrics,'aggregation':'equal mean of original prediction-quality formula'})
'''
(TASK/'verifier/grader.py').write_text(grader)

physics='''# 公开物理与离散契约

时间 day、空间 m、浓度 g/m³。移动域储存 W=C+Q*b*C/(1+b*C)，非移动域储存 β*C_im。方程为 dW/dt=D∇²C-v(z)*∂xC-λC-κ(C-C_im)+q/φ；β*dC_im/dt=κ(C-C_im)-β*λ*C_im。Q 是每移动水体积的吸附容量；b 是 Langmuir 亲和系数。其余符号由 scene.json 和 source_bounds.json 给出。

每个源为均匀长方体，空间分配用真实体积与网格单元的重叠比例。释放区间分为三个等长片段，各片段总质量率分别为 rate0/1/2。注入使用片段与时间步的精确重叠比例。边界与原协议相同：上游零浓度；下游与横向零梯度。使用一阶迎风、中心扩散和公开 0.5 日时间步。显式更新 W 与 β*C_im 后，解析求解 Langmuir 储存关系正根取得新的 C，保持交换项的质量守恒。

calibration_source 是已知注入实验；contaminant 是共享同一水文/吸附参数的两个未知污染源。观测位于固定监测格点，非检出记录为区间 [0,0.0003)，不能当作精确零。数据来自本项目的合成双域模拟，未运行 MODFLOW。public/simulator.py 提供完整可调用的公开前向模型，不要求重写它。
'''
(TASK/'public/physics.md').write_text(physics)
instruction='''# 联合反演双域输运与两个时变污染源

根据一个已知注入校准实验和一组污染观测，反演共享的七个输运/吸附参数，以及两个未知长方体源的几何、时段和三段释放率，共 29 个参数。工作预算六小时。完整前向模型 simulator.py、方程、参数界限和已知校准注入全部公开；难点在联合推断、混合源分离和未来外推。

提交 submission/answer.json，其键严格对应 source_bounds.json。可以从校准实验估计介质参数、从早期污染观测定位源，再分块优化释放率、源尺寸和动力学，最后联合拟合。诊断与推断源码可以同放 submission/，只有 answer.json 决定分数。

公开与固定反馈覆盖不同井位、相同采样时间；独立审计还有更晚采样时间。每个实验沿用原预测质量公式 1/(1+0.5*relative_rmse²+0.5*log_rmse²)，总分为两个实验的等权均值；原有尺度、权重与容差不变。反馈给出两实验各自的原始误差与分数。提交参数必须满足界限，两个源均须完整位于域内。

素材参照固定 USGS MODFLOW 6 的非线性吸附与移动/非移动域输运案例。实际场景、未知参数和合成观测均为新构造，具体模型与原实例不同；并非 USGS 的真实野外观测或已执行 MODFLOW 的结果。
'''
(TASK/'instruction.md').write_text(instruction);(TASK/'public/instruction.md').write_text(instruction)
for name in ['scoring_metadata.json','score_design.json']:
    p=TASK/'public'/name;d=json.loads(p.read_text());d['experiment_aggregation']='equal arithmetic mean';d['parameter_count']=29;dump(p,d)
source_dir=TASK/'public/source';source_dir.mkdir(exist_ok=True)
source_files=[]
for rel in ['scripts/ex-gwt-mt3dms-p02.py','doc/sections/ex-gwt-mt3dms-p02.tex']:
    f=ROOT/'materials/repos/modflow6-examples'/rel;shutil.copyfile(f,source_dir/f.name);source_files.append({'path':rel,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
provenance=json.loads((TASK/'source_provenance.json').read_text());provenance['sources'].append({'repository':'https://github.com/MODFLOW-ORG/modflow6-examples.git','commit':'b6d5d42839349a447579a577f968fe8ac4c1c671','files':source_files,'acquired':True});dump(TASK/'source_provenance.json',provenance)
shutil.copyfile(HERE/'science_model.py',TASK/'solution/forward.py')
shutil.copyfile(HERE/'science_reference.py',TASK/'solution/solve.py')
for side in ['agent','verifier']:
    ctx=TASK/'environment'/side;shutil.rmtree(ctx/'public');shutil.copytree(TASK/'public',ctx/'public')
    if side=='verifier':
        shutil.rmtree(ctx/'private');shutil.copytree(TASK/'private',ctx/'private')
        shutil.rmtree(ctx/'verifier');shutil.copytree(TASK/'verifier',ctx/'verifier')
dump(TASK/'REVISION.json',{'source_task':str(BASE.relative_to(ROOT)),'physical_changes':['conservative nonlinear Langmuir storage','mobile/immobile exchange','known injection calibration','two superposed sources with segmented release'],
 'public_forward_supplied':True,'parameter_count':29,'original_formula_constants_unchanged':True,'numerical_agreement':errors,'six_hour_difficulty':'not_yet_measured'})
print(TASK)
