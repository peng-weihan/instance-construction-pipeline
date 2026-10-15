"""Build a coupled Darcy-field, sorption and source inverse problem."""
from pathlib import Path
import csv,importlib.util,json,shutil,sys
import numpy as np
from scipy.ndimage import gaussian_filter
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
SRC=ROOT/'samples/remaining-three-built-001/science-task-r1';DST=SRC.with_name('science-task-r2')
shutil.copytree(SRC,DST)
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
scene=json.loads((SRC/'public/scene.json').read_text());scene.pop('layers')
scene.update(name='Heterogeneous-Darcy-DualDomain-62',conductivity_control_shape=[7,4,3],
 base_conductivity_m_day=.23,hydraulic_heads_m={'0':[6.,0.],'1':[3.,0.]},
 noise={'multiplicative_log_sd':.05,'detection_limit_g_m3':.0003},
 hydraulic_observation_noise={'head_sd_m':.0005,'flux_relative_sd':.005})
bounds=json.loads((SRC/'public/source_bounds.json').read_text());truth=json.loads((SRC/'private/truth.json').read_text())
rng=np.random.default_rng(2026101502)
field=gaussian_filter(rng.normal(0,.65,size=(7,4,3)),sigma=.65)
field-=field.mean();field*=.82/max(abs(field.min()),abs(field.max()))
for i,x in enumerate(field.ravel()):bounds[f'logK_{i:03d}']=[-1.,1.];truth[f'logK_{i:03d}']=float(x)
dump(DST/'public/scene.json',scene);dump(DST/'public/source_bounds.json',bounds);dump(DST/'private/truth.json',truth)
for dest,name in [('public/simulator.py','science_model_r2.py'),('verifier/forward.py','science_model_r2.py'),
                  ('solution/forward.py','science_model_r2.py'),('private/generate_scene.py','science_generator_r2.py'),
                  ('private/hydrology_generator.py','science_hydrology_generator.py')]:shutil.copyfile(HERE/name,DST/dest)
for folder in ['public','verifier','solution']:shutil.copyfile(HERE/'science_hydrology.py',DST/folder/'hydrology.py')
sys.path.insert(0,str(DST/'private'));sys.path.insert(0,str(DST/'public'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
gen=load('r2_gen',DST/'private/generate_scene.py');forward=load('r2_forward',DST/'public/simulator.py')
import hydrology,hydrology_generator
hydro_rows=[];errors={}
for axis in [0,1]:
 h,q,total=hydrology_generator.hydraulic_fields(scene,truth,axis);h2,q2,t2=hydrology.hydraulic_fields(scene,truth,axis)
 errors['hydraulic_axis_'+str(axis)]={'head':float(abs(h-h2).max()),'flux':max(float(abs(a-b).max()) for a,b in zip(q,q2)),'total':abs(total-t2)}
 assert errors['hydraulic_axis_'+str(axis)]['head']<1e-8
 for ix in [3,8,13,18,23,28]:
  for iy in [3,8,13]:
   for iz in [2,4,6]:hydro_rows.append([axis,ix,iy,iz,float(h[ix,iy,iz]+rng.normal(0,.0005)),.0005])
 # The absolute inlet flux resolves the global conductivity scale ambiguity.
 hydro_rows.append([axis,-1,-1,-1,float(total*(1+rng.normal(0,.005))),abs(total)*.005])
with (DST/'public/hydraulic_observations.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['axis','ix','iy','iz','value','sd']);w.writerows(hydro_rows)
pubdays=[40.,80.,120.,180.,260.,360.,480.];auditdays=[60.,100.,150.,220.,310.,430.,560.,660.]
days=sorted(set(pubdays+auditdays));tables={'public':[],'feedback':[],'audit':[]}
for experiment in ['calibration','contaminant']:
 expected=gen.states(scene,truth,days,experiment);actual=forward.simulate(scene,truth,days,experiment)
 err=max(float(abs(expected[d]-actual[d]).max()) for d in days);assert err<1e-8;errors[experiment]=err
 for ix in range(3,24,2):
  for iy in [4,6,8,10,12]:
   for iz in [2,4,6]:
    split=['public','feedback','audit'][(ix//2+iy//2+iz//2)%3]
    for day in (auditdays if split=='audit' else pubdays):
     v=float(expected[day][ix,iy,iz])
     if v<.0003 and (ix+iy+iz+int(day))%7:continue
     measured=v*float(np.exp(rng.normal(0,.05))) if split=='public' else v
     censored=split=='public' and measured<.0003
     tables[split].append([experiment,f'{split}_{ix}_{iy}_{iz}',ix,iy,iz,day,'' if censored else measured,int(censored),.0003])
 print(experiment,'independent agreement',err,flush=True)
for split,rows in tables.items():
 assert all(sum(r[0]==e for r in rows)>20 for e in ['calibration','contaminant'])
 with (DST/('public' if split=='public' else 'private')/(split+'_observations.csv')).open('w') as f:
  w=csv.writer(f);w.writerow(['experiment','well','ix','iy','iz','day','concentration','below_detection','detection_limit']);w.writerows(rows)
(DST/'verifier/grader.py').write_text((SRC/'verifier/grader.py').read_text().replace('all 29 parameters','all 113 parameters'))
dump(DST/'public/submission/answer.json',{k:sum(v)/2 for k,v in bounds.items()})
hydraulic_doc='''\n## 空间介质与水力实验（r2）\n\n介质 K=0.23*exp(trilinear(logK)) m/day，logK 为公开的 7×4×3 控制网格，共84个待反演系数。稳态水头满足 div(K grad h)=0；两个公开水力实验分别在 x 或 y 两侧施加 scene.json 的已知水头，其余边界无流。单元面通量采用谐均导水系数，Dirichlet 边界到单元中心距离为半个单元。水头与总入口流量观测见 hydraulic_observations.csv；ix=-1 行是总流量，单位 m³/day。观测噪声 sd 明示。\n\n输运使用 x 方向水力实验得到的三维 Darcy 面通量，再乘 velocity_scale/porosity 得到孔隙流速。一阶守恒迎风、各向扩散、Langmuir储存和移动/非移动交换共同决定浓度。公开 hydrology.py 与 simulator.py 给出完整实现。稳定时间步为0.5/ceil(0.5*max_rate/0.8)，至少一段；所有采样时刻均为0.5的整数倍。导水场、介质参数与两污染源须联合推断，总113参数。水力观测只用于反演，不与浓度误差混用单位计分。固定反馈及审计仍按原浓度公式给分。\n'''
physics=(SRC/'public/physics.md').read_text().replace('v(z)*∂xC','div(v*C)').replace('公开 0.5 日时间步','公开稳定时间步')+hydraulic_doc
(DST/'public/physics.md').write_text(physics)
instruction=(SRC/'instruction.md').read_text().replace('共享的七个输运/吸附参数','84个空间导水场系数、七个输运/吸附参数').replace('共 29 个参数','共 113 个参数').replace('难点在联合推断、混合源分离和未来外推','难点在水力场反演、空间输运、混合源分离和未来外推')
instruction+='\n先利用公开水头与总流量估计空间导水场，再结合校准示踪与污染浓度修正场、介质参数和源。导水场平滑正则化、灵敏度分析、交替优化与不确定性检验都是允许的。完整物理契约见 physics.md。\n'
for p in [DST/'instruction.md',DST/'public/instruction.md']:p.write_text(instruction)
for name in ['scoring_metadata.json','score_design.json']:
 p=DST/'public'/name;d=json.loads(p.read_text());d.update(parameter_count=113,auxiliary_data='hydraulic observations are inference inputs, not extra score terms');dump(p,d)
dump(DST/'private/generation_record.json',{'seed':2026101502,'synthetic':True,'model':'own coupled Darcy and reactive dual-domain transport; not a MODFLOW execution',
 'observation_counts':{k:len(v) for k,v in tables.items()},'independent_agreement':errors})
dump(DST/'REVISION.json',{'previous_revision':'science-task-r1','why':'1200 evaluations reached .907 feedback in 77 seconds',
 'new_physics':'unknown heterogeneous Darcy field coupled to transport and two sources','parameter_count':113,
 'public_forward_supplied':True,'original_formula_constants_unchanged':True,'independent_agreement':errors,'six_hour_difficulty':'not_measured'})
for side in ['agent','verifier']:
 ctx=DST/'environment'/side;shutil.rmtree(ctx/'public');shutil.copytree(DST/'public',ctx/'public')
 if side=='verifier':
  for part in ['private','verifier']:shutil.rmtree(ctx/part);shutil.copytree(DST/part,ctx/part)
print(DST)
