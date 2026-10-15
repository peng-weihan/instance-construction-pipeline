from pathlib import Path
import re,json,struct,subprocess
R=Path(__file__).resolve().parents[1];D=R/'task/verifier/private';D.mkdir(exist_ok=True,parents=True)
cases=[]
def scenario(id,src,batches,enc=0,scanner=False,included=False,public=False):
 codec=['utf-8','utf-16-le','utf-16-be'][enc]
 def bs(s):return s.encode(codec)
 def pt(s):return (s.count('\n'),len(bs(s.rsplit('\n',1)[-1])))
 def pack(*ns):return struct.pack('<'+'I'*len(ns),*ns)
 def blob(s):b=bs(s);return pack(len(b))+b
 def ranges(s):
  if not included:return pack(0)
  a=s.index('<code>\n')+len('<code>\n');b=s.index('\n</code>');return pack(1,*pt(s[:a]),*pt(s[:b]),len(bs(s[:a])),len(bs(s[:b])))
 data=pack(enc)+ranges(src)+blob(src)+pack(len(batches));cur=src
 for edits in batches:
  data+=pack(len(edits))
  for old,new,*occ in edits:
   if old=='$START':a=b=0
   elif old=='$END':a=b=len(cur)
   else:
    a=cur.index(old) if not occ else [m.start() for m in re.finditer(re.escape(old),cur)][occ[0]];b=a+len(old)
   after=cur[:a]+new+cur[b:]
   data+=pack(len(bs(cur[:a])),len(bs(cur[:b])),len(bs(cur[:a]+new)),*pt(cur[:a]),*pt(cur[:b]),*pt(cur[:a]+new))+blob(after);cur=after
  data+=ranges(cur)
 groups=['initial','edit','lifecycle','parser','ranges']
 if enc or any(ord(c)>127 for c in src+cur):groups+=['unicode']
 if scanner:groups+=['scanner']
 c={'id':id,'encoding':enc,'scanner':scanner,'included':included,'groups':groups,'split':'public' if public else 'feedback','input':id+'.bin','expected':id+'.out','description':id.replace('_',' ')}
 (D/c['input']).write_bytes(data);cases.append(c)
 if public:
  p=R/'task/environment/public';p.mkdir(exist_ok=True);(p/c['input']).write_bytes(data)
scenario('rename_same_shape','alpha = 12\nbeta = alpha + 2\n',[[('alpha','gamma')]],public=True)
scenario('replace_type','a = 12\nb = 4\n',[[('12','"q"')]],public=True)
scenario('prefix_multiline','a = 1\nb = a + 2\n',[[('$START','# heading\nx = 8\n')],[('a + 2','[a, 2]')]],public=True)
scenario('delete_cross_children','x = [1, 2, 3]\ny = x\nz = 4\n',[[('2, 3]\ny = x','8]')]])
scenario('batch_before_parse','x = 1\ny = 2\nz = 3\n',[[('1','[10, 20]'),('y = 2','if x:\n    y = x'),('z = 3','z = "end"')],[('20','30')]])
scenario('insert_empty','',[[('$START','def f():\n    return 3\n')],[('return 3','return [3]')]],scanner=True)
scenario('delete_all','x = [1, 2]\n',[[('x = [1, 2]\n','')],[('$END','pass\n')]])
scenario('append_eof','a = 1',[[('$END','\nb = (a + 2)')],[('$END','\n')]])
scenario('noop_then_change','a = 1\nb = 2\n',[[('$START','')],[('2','{}')]])
scenario('boundary_insert','x = [1,2]\ny = 3\n',[[('1,2','1, 0,2')],[(']\ny',']\n# hi\ny')]])
scenario('error_bracket','x = [1, 2\ny = 3\n',[[('2\ny','2]\ny')],[('[1, 2]','(1 + )')],[('(1 + )','(1 + 4)')]],scanner=True)
scenario('error_suite','def f():\n    x =\n    return x\n',[[('x =\n','x = 4\n')],[('return x','return (x +')],[('(x +','(x + 2)')]],scanner=True)
scenario('error_delete_colon','if True:\n    pass\nx = 2\n',[[('True:','True')],[('True','True:')]],scanner=True)
scenario('multiedit_recovery','x = f(1, 2)\ny = 3\n',[[('f(1, 2)','f(1, '),('y = 3','y = {')],[('f(1, ','f(1, 4)'),('y = {','y = {}')]])
for enc in [0,1,2]:
 scenario('unicode_'+str(enc),'变量 = "café🙂"\nα = [变量, 2]\n',[[('café🙂','雪\n山')],[('雪\n山','雪🌍')],[('α = [变量, 2]','α = {"键": 变量}')]],enc=enc)
 scenario('unicode_prefix_'+str(enc),'x = "é"\ny = 3\n',[[('$START','# λ🌍\n')],[('3','"漢字"')]],enc=enc)
scenario('crlf','x = 1\r\ny = 2\r\n',[[('1','[1,\r\n 2]')],[('2]\r\ny','2,3]\r\ny')]])
scenario('indent_shift','if x:\n    a = 1\n    b = 2\nc = 3\n',[[('    b = 2','b = 2')],[('b = 2','    b = 2')],[('a = 1','if y:\n        a = 1')]],scanner=True)
scenario('nested_indent','def f():\n    if x:\n        return 1\n    return 2\ny = f()\n',[[('        return 1','    return 1')],[('    return 1','        return [1]')]],scanner=True)
scenario('triple_string','x = """abc\ndef\nghi"""\ny = 2\n',[[('def','def\nMORE')],[('abc','a"bc')],[('y = 2','y = [2]')]],scanner=True)
scenario('f_string','x = f"hello {name}"\ny = 1\n',[[('name','user.id')],[('hello ','hi {2} ')],[('f"','rf"')]],scanner=True)
scenario('tabs','if x:\n\ta = 1\n\tb = 2\nc = 3\n',[[('\tb','b')],[('b = 2','\tb = [2]')]],scanner=True)
scenario('comment_indent','if x:\n    # comment\n    a = 1\n\nb = 2\n',[[('# comment','# new\n    # more')],[('a = 1','a = (\n        1 + 2\n    )')]],scanner=True)
scenario('included_prefix','HOST\n<code>\nx = 1\ny = 2\n</code>\nEND',[[('HOST','HEADER\nSECOND')],[('1','[1]')]],included=True)
scenario('included_inside','HOST\n<code>\na = 12\nb = 2\n</code>\nEND',[[('a = 12','a = "hi"\nc = 3')],[('b = 2','if a:\n    b = 2')]],included=True,scanner=True)
scenario('included_unicode','宿主\n<code>\n名字 = 2\nx = 名字\n</code>\n结束',[[('宿主','宿主🙂\n行')],[('2','[2,3]')]],included=True,enc=1)
# State-safety counterexamples found by deterministic author audit, not upstream tests.
for index,found in enumerate(json.loads((R/'evidence/scanner-search.json').read_text())['found']):
 src=found['source'];old=src[found['start']:found['end']]
 scenario('scanner_state_'+str(index),src,[[ (old,found['replacement']) ]],scanner=True)
# Native unchanged grammar regression expectations: first 3 plain cases in each file.
for f in sorted((R/'material-src/tree-sitter-python/test/corpus').glob('*.txt')):
 if f.stem=='errors':continue
 text=f.read_text();chunks=re.split(r'^={20,}\r?\n',text,flags=re.M);taken=0
 for j in range(1,len(chunks)-1,2):
  title=chunks[j].strip();body=chunks[j+1];parts=re.split(r'^-{20,}\r?\n',body,flags=re.M,maxsplit=1)
  if len(parts)!=2 or ':' in title or '(MISSING' in parts[1] or '(ERROR' in parts[1]:continue
  src=parts[0].strip('\n')+'\n';expected=' '.join(parts[1].split())
  expected=re.sub(r'\b[a-z_]+: ', '', expected)
  expected=re.sub(r'\s+\)',')',expected)
  ident='native_'+f.stem+'_'+str(taken);scenario(ident,src,[],public=False);c=cases[-1];c['groups']=['initial'];c['native_expected']=expected;c['native_origin']=f'test/corpus/{f.name}: {title}'
  taken+=1
  if taken==3:break
(D/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
print('cases',len(cases))
