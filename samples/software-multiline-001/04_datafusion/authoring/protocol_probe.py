#!/Users/raymone/Desktop/edgebench/.venv/bin/python
"""Author-only test driver for grader protocol; NOT a DataFusion solution/reference."""
import pathlib,sys,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tests'))
from workloads import expected
s=json.loads(sys.stdin.readline());print('READY',flush=True);assert sys.stdin.readline().strip()=='GO'
mode=s.pop('_probe_mode','correct')
if mode=='wrong-null':s['nulls_first']=not s['nulls_first']
rows=expected(s)
if mode=='short':rows=rows[:-1]
print(json.dumps({'rows':rows}))
