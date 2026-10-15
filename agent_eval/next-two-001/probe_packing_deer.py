import json,subprocess,os
from pathlib import Path
from geometry import validate
from runtime import scoring_constants
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
case=Path('/judge/private/feedback_cases/deer_order1.json');data=json.loads(case.read_text());c=scoring_constants()
binary=next(p for p in Path('/opt/runtime/packing-build').rglob('packingsolver_irregular') if p.is_file() and p.stat().st_mode&0o111)
rows=[]
for spacing in [0.0,0.0001,0.001]:
 out=Path('/out')/('cert-'+str(spacing)+'.json')
 p=subprocess.run([str(binary),'--input',str(case),'--certificate',str(out),'--time-limit','20','--verbosity-level','0','--item-item-minimum-spacing',str(spacing)],capture_output=True,text=True,timeout=30)
 row={'spacing':spacing,'exit_code':p.returncode,'stderr':p.stderr[-800:]}
 if out.exists():
  try:row['geometry']=validate(data,json.loads(out.read_text()),c)
  except Exception as e:row['geometry_error']=str(e)
 rows.append(row);print(json.dumps(row),flush=True)
(Path('/out')/'report.json').write_text(json.dumps(rows,indent=2)+'\n')
