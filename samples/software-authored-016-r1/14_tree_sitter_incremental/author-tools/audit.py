from pathlib import Path
import struct,subprocess,json
R=Path(__file__).resolve().parents[1];D=R/'task/verifier/private/author-audit';D.mkdir(exist_ok=True);E=R/'evidence'
pack=lambda *x:struct.pack('<'+'I'*len(x),*x)
def make(src,old,new,encoding=0):
 codec=['utf-8','utf-16-le','utf-16-be'][encoding];bs=lambda x:x.encode(codec)
 blob=lambda x:pack(len(bs(x)))+bs(x);point=lambda x:(x.count('\n'),len(bs(x.rsplit('\n',1)[-1])))
 a=src.index(old);b=a+len(old);text=src[:a]+new+src[b:]
 return pack(encoding,0)+blob(src)+pack(1,1,len(bs(src[:a])),len(bs(src[:b])),len(bs(src[:a]+new)),*point(src[:a]),*point(src[:b]),*point(src[:a]+new))+blob(text)+pack(0),text,codec
cases=[('same_kind','answer = 7\n','7','8',0,'(module (expression_statement (assignment (identifier) (integer))))'),('unicode_points','名 = 7\n','7','"🌲"',1,'(module (expression_statement (assignment (identifier) (integer))))'),('suite','if x:\n    pass\n','pass','return [7]',0,'(module (if_statement (identifier) (block (pass_statement))))')]
results=[]
for name,src,old,new,enc,expected in cases:
 data,text,codec=make(src,old,new,enc);(D/(name+'.bin')).write_bytes(data)
 p=subprocess.run([str(E/'reference-probe')],input=data,capture_output=True,timeout=5);assert p.returncode==0
 out=p.stdout.decode();section=lambda tag:out.split('@'+tag+'\n')[1].split('@end')[0].rstrip('\n')
 checks={'manual_initial_named_tree':section('sexp')==expected,'incremental_equals_separate_fresh':section('parsed')==section('fresh')}
 # Independent byte/point audit: do not use the reference tree to compute coordinates.
 payload=text.encode(codec);unit=2 if enc else 1
 def point_at(byte):
  pre=payload[:byte].decode(codec);return pre.count('\n'),len(pre.rsplit('\n',1)[-1].encode(codec))
 valid=True
 for line in section('parsed').splitlines():
  if line.startswith('field '):continue
  fields=line.split();a,b=map(int,fields[7:9]);ar,ac,br,bc=map(int,fields[9:13])
  if not (0<=a<=b<=len(payload)) or a%unit or b%unit or point_at(a)!=(ar,ac) or point_at(b)!=(br,bc):valid=False
 checks['independent_all_node_positions']=valid
 if name=='same_kind':checks['same_kind_changed_range_empty']=not section('changed')
 else:checks['structural_change_reported']=bool(section('changed'))
 results.append({'id':name,'checks':checks,'passed':all(checks.values())})
(D/'contract.json').write_text(json.dumps({'scored':False,'selection_use':'author quality audit only; never selects candidate submissions','cases':[{'id':x[0],'manual_initial_named_tree':x[5]} for x in cases]},indent=2)+'\n')
(E/'author-audit.json').write_text(json.dumps({'cases':results,'all_passed':all(x['passed'] for x in results)},indent=2)+'\n');print(results);assert all(x['passed'] for x in results)
