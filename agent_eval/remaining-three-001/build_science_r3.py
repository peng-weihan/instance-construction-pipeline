"""Four interacting finite-release sources; calibration is input, not reward."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
# Retain independently measured r1/r2. Build a fresh scene from their construction
# recipe, with source count generalized in both separate numerical implementations.
for source,target in [('science_model_r2.py','science_model_r3.py'),('science_generator_r2.py','science_generator_r3.py')]:
 text=(HERE/source).read_text().replace('for i in [1,2]',"for i in range(1,scene.get('source_count',2)+1)")
 (HERE/target).write_text(text)
recipe=(HERE/'build_science_r2.py').read_text().replace("SRC.with_name('science-task-r2')","SRC.with_name('science-task-r3')")
recipe=recipe.replace('science_model_r2.py','science_model_r3.py').replace('science_generator_r2.py','science_generator_r3.py')
recipe=recipe.replace('2026101502','2026101503').replace("scene.update(name=", "scene.update(source_count=4,name=")
insert='''
for i,values,xrange,trange in [(3,[22.4,-3.1,1.2,2.6,1.4,.8,36,163,.07,.16,.04],[18,25],[10,100]),
                              (4,[27.2,3.0,-1.1,2.2,1.1,.7,113,208,.04,.09,.13],[23,30],[50,180])]:
 for key,value in zip(['cx','cy','cz','hx','hy','hz','t_start','duration','rate0','rate1','rate2'],values):truth[f's{i}_{key}']=value
 for key,value in {'cx':xrange,'cy':[-5,5],'cz':[-2,2],'hx':[1,4],'hy':[.5,2.5],'hz':[.3,1.5],
                   't_start':trange,'duration':[60,240],'rate0':[.005,.22],'rate1':[.005,.22],'rate2':[.005,.22]}.items():bounds[f's{i}_{key}']=value
'''
recipe=recipe.replace("rng=np.random.default_rng(2026101503)",insert+"\nrng=np.random.default_rng(2026101503)")
recipe=recipe.replace("for source in [1,2]", "for source in range(1,scene['source_count']+1)")
# The grader source is copied from r1 inside the recipe. Transform that source
# after construction below; known calibration injections are auxiliary inputs.
exec(compile(recipe,str(HERE/'build_science_r2.py'),'exec'),{'__file__':str(HERE/'build_science_r2.py'),'__name__':'__main__'})
import json,shutil
task=ROOT/'samples/remaining-three-built-001/science-task-r3'
grader=(task/'verifier/grader.py').read_text().replace('all 113 parameters','all 135 parameters').replace('for source in [1,2]',"for source in range(1,scene['source_count']+1)")
grader=grader.replace("for experiment in ['calibration','contaminant']:", "for experiment in ['contaminant']:")
grader=grader.replace("'equal mean of original prediction-quality formula'","'original prediction-quality formula on operational contaminant predictions; calibration is auxiliary data'")
(task/'verifier/grader.py').write_text(grader)
for name in ['scoring_metadata.json','score_design.json']:
 p=task/'public'/name;d=json.loads(p.read_text());d.update(parameter_count=135,
  experiment_aggregation='score operational contaminant predictions only; calibration observations are public inference inputs',
  auxiliary_data='hydraulic and known-injection calibration inputs do not add easy score terms')
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
note='''\n## r3 的评测对象\n\n此版反演四个有不同空间位置与释放时段的污染源，共135参数。四源共享非线性储存与空间水力场，浓度不是四份独立子题。source_count 与各源界限明确公开。已知注入校准实验和水力观测只作为推断素材；评分回到原始污染源任务的浓度预测公式，直接评价未知污染的空间/时间外推。不给已知校准注入单独加分。原0.5/0.5误差权重、尺度、上下界均未修改。\n'''
for p in [task/'instruction.md',task/'public/instruction.md']:
 text=p.read_text().replace('两个未知','四个未知').replace('两个污染','四个污染').replace('两个时变','四个时变').replace('113','135')
 text=text.replace('每个实验沿用原预测质量公式','未知污染预测沿用原质量公式').replace('总分为两个实验的等权均值','总分只评价未知污染预测')
 text=text.replace('反馈给出两实验各自的原始误差与分数','反馈给出未知污染预测的原始误差与分数').replace('两个源均须','四个源均须')
 p.write_text(text+note)
for side in ['agent','verifier']:
 ctx=task/'environment'/side;shutil.rmtree(ctx/'public');shutil.copytree(task/'public',ctx/'public')
 if side=='verifier':shutil.rmtree(ctx/'verifier');shutil.copytree(task/'verifier',ctx/'verifier')
p=task/'REVISION.json';d=json.loads(p.read_text());d.update(previous_revision='science-task-r2',
 why='two-source public-data reference reached .922 in 110 seconds',source_count=4,parameter_count=135,
 scoring_change='remove the r1/r2 auxiliary calibration reward; retain original unknown-source prediction formula')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
