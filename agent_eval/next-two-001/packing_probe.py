"""Measure why the trusted original solver fails independent geometry checks."""
import json,subprocess,os
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon
from geometry import item_geometry,validate
from runtime import scoring_constants
case=Path('/judge/public/cases/stool_x10_order1.json');d=json.loads(case.read_text());constants=scoring_constants()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
binary=next(p for p in Path('/opt/runtime/packing-build').rglob('packingsolver_irregular') if p.is_file() and p.stat().st_mode&0o111)
out=Path('/out');cert=out/'certificate.json'
p=subprocess.run([str(binary),'--input',str(case),'--certificate',str(cert),'--time-limit','20','--verbosity-level','0'],capture_output=True,text=True,timeout=30)
report={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
if cert.exists():
 c=json.loads(cert.read_text());shapes=[];deltas=[]
 for entry in c['bins'][0]['items']:
  g=item_geometry(d['item_types'][entry['id']])
  if entry.get('mirror'):g=affinity.scale(g,xfact=-1,yfact=1,origin=(0,0))
  g=affinity.rotate(g,entry['angle'],origin=(0,0));g=affinity.translate(g,entry['x'],entry['y']);shapes.append(g)
  h=entry['item_shapes'][0]['shape'];claimed=Polygon([(x['xs'],x['ys']) for x in h]);deltas.append(g.symmetric_difference(claimed).area)
 overlaps=[]
 for i,a in enumerate(shapes):
  for j,b in enumerate(shapes[:i]):
   area=a.intersection(b).area
   if area>0:overlaps.append({'i':i,'j':j,'area':area,'relative_area':area/max(min(a.area,b.area),1)})
 report.update(placements=len(shapes),largest_overlaps=sorted(overlaps,key=lambda r:r['relative_area'],reverse=True)[:5],max_claimed_shape_difference=max(deltas))
 try:report['validated']=validate(d,c,constants)
 except Exception as e:report['validation_error']=str(e)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
