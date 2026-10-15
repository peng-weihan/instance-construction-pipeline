from pathlib import Path
import json,subprocess,tomllib
R=Path(__file__).resolve().parents[1];cases=[]
def add(group,name,**r): cases.append({'id':name,'group':group,'request':r})
for n,s in [
 ('ascii-escapes',r's="\b\e\f\n\r\t\\\""'+'\n'),
 ('unicode-widths',r's="\x41\u03B1\U0001F600"'+'\n'),
 ('unicode-keys',r'"\u03B1"."\U0001F600"="yes"'+'\n'),
 ('literal-no-escapes',"s='C:\\Users\\ray'\n"),
 ('utf8-mixed',r's="中\u6587\U0001F642"'+'\n')]:add('decode',n,op='roundtrip',text=s)
for n,s in [
 ('fold-indent','s="""\nalpha\\\n    beta\\\n\n\t gamma"""\n'),
 ('fold-crlf','s="""\r\nalpha\\\r\n  \r\n\tbeta"""\r\n'),
 ('fold-whitespace','s="""a\\ \t\n \t b"""\n'),
 ('literal-multiline',"s='''\nnew\nlines and \\slashes'''\n"),
 ('triple-quotes','s="""two "" quotes and \\" done"""\n')]:add('multiline',n,op='roundtrip',text=s)
for n,s in [
 ('package-comments','# package configuration\n[package] # header\nname  =  \'demo\' # keep me\nversion="0.1"\n'),
 ('array-format','values = [\n  "a", # item\n  \'b\',\n]\n'),
 ('dotted-inline','"root key".nested={ x=1, y = \'two\' } # tail\n'),
 ('array-tables','[[bin]]\nname=\'one\'\n[[bin]] # two\nname="two"\n'),
 ('integer-spelling','hex = 0xDEAD_BEEF\nplus = +42\nfloat = 1_000.25\n')]:add('format',n,op='roundtrip',text=s)
for n,s,ch in [
 ('edit-root','a = \'unchanged\' # comment\nb = 2\n',[{'path':['b'],'value':"line\n\"quote\"\\tail"}]),
 ('edit-nested','# banner\n[package]\nname=\'old\'\nversion = \'1.0\' # keep\n',[{'path':['package','name'],'value':'new\nname'}]),
 ('edit-array','items = ["old", \'keep\', "last"] # tail\n',[{'path':['items',0],'value':'new\tvalue'}]),
 ('edit-inline','point={ x=1, label=\'old\' }\n',[{'path':['point','label'],'value':"it's new"}]),
 ('edit-new-key','name=\'demo\'\n',[{'path':['strange key.中'],'value':'value\\path\u0001'}])]:add('edit',n,op='edit',text=s,changes=ch)
for n,v in [
 ('serialize-controls',{'s':'\b\t\n\f\r\u001b\u0000\u007f'}),
 ('serialize-quotes',{'s':'""" and \'\'\' and \\'}),
 ('serialize-key-policy',{'bare-key':1,'':'empty','a.b':'dot','中 文':'中文'}),
 ('serialize-leading-newlines',{'s':'\n\nhello\n'}),
 ('serialize-structure',{'package':{'name':'demo','features':['a','b\nc'],'metadata':{'needs quote':'x\\y'}}})]:add('serialize',n,op='serialize',value=v)
for n,s in [
 ('invalid-escape',r's="\q"'+'\n'),
 ('short-unicode',r's="\u12"'+'\n'),
 ('surrogate',r's="\uD800"'+'\n'),
 ('out-of-range',r's="\U00110000"'+'\n'),
 ('nonhex',r's="\uABCG"'+'\n'),
 ('stray-cr','s="""one\\\rtwo"""\n'),
 ('bad-continuation','s="""a\\  X"""\n')]:add('diagnostic',n,op='diagnostic',text=s)
for n,s in [('nested-string-array','[package]\nname="demo"\n[package.metadata]\nx=["a\\nb", "\\U0001F600"]\n'),('quoted-table','["a.b"."\\u03b1"]\ns="\\t" # trailing\n'),('crlf-format','title = \'demo\'\r\n\r\n[section]\r\nitem = "x"\r\n')]:add('integration',n,op='roundtrip',text=s)
bin=R/'authoring/harness/target/debug/edgebench-toml-probe'
p=subprocess.run([str(bin)],input=''.join(json.dumps(c['request'])+'\n' for c in cases),text=True,capture_output=True)
(R/'authoring/evidence/reference-freeze.stderr').write_text(p.stderr)
if p.returncode:raise SystemExit(p.stderr)
outs=p.stdout.splitlines();assert len(outs)==len(cases)
for c,line in zip(cases,outs):
 c['expected']=json.loads(line)
 # Independently check TOML 1.0 semantics on applicable successful input.
 if 'text' in c['request'] and c['request']['op']!='diagnostic' and c['expected'].get('ok'):
  try:
   v=tomllib.loads(c['request']['text'])
   assert c['expected']['original']==v,(c['id'],v,c['expected'])
   c['independent_check']='Python 3.12 tomllib semantic equality'
  except tomllib.TOMLDecodeError:c['independent_check']='TOML 1.1 source reference only'
(R/'verifier/private/cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
(R/'environment/dev-cases.json').write_text(json.dumps(cases[:2]+cases[10:11]+cases[15:16]+cases[20:21]+cases[25:26],ensure_ascii=False,indent=2)+'\n')
(R/'authoring/evidence/reference-freeze.stdout.jsonl').write_text(p.stdout)
print(json.dumps({'cases':len(cases),'groups':sorted({c['group'] for c in cases}),'reference_errors':[c['id'] for c in cases if not c['expected'].get('ok') and c['group']!='diagnostic']}))
