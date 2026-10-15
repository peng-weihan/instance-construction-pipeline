from pathlib import Path
import struct,subprocess,random,json
R=Path(__file__).resolve().parents[1]
def data(src,a,b,new):
 pack=lambda *x:struct.pack('<'+'I'*len(x),*x)
 blob=lambda x:pack(len(x.encode()))+x.encode()
 point=lambda x:(x.count('\n'),len(x.rsplit('\n',1)[-1].encode()))
 after=src[:a]+new+src[b:]
 return pack(0,0)+blob(src)+pack(1,1,len(src[:a].encode()),len(src[:b].encode()),len((src[:a]+new).encode()),*point(src[:a]),*point(src[:b]),*point(src[:a]+new))+blob(after)+pack(0)
def parsed(out,tag):return out.split('@'+tag+'\n')[1].split('@end')[0]
sources=['''if x:
    if y:
        a = 1
        b = 2
    c = 3
d = 4
''','''def f():
    a = """one
two
three"""
    b = "four"
    return b
x = 4
''','''x = f"abc {a} def {b} ghi"
y = "z"
z = 3
''','''x = [
    1,
    2,
    3
]
y = 4
''']
rng=random.Random(14023);found=[]
for i in range(1600):
 src=sources[i%len(sources)];a=rng.randrange(len(src));b=min(len(src),a+rng.randrange(0,12));new=rng.choice(['','    ','\n','"','"""',"'",'r','f','    if q:\n','(',')',':','\\','\n    ']);inp=data(src,a,b,new)
 p=subprocess.run([str(R/'evidence/scanner-missing-probe')],input=inp,capture_output=True,timeout=2)
 if p.returncode:continue
 out=p.stdout.decode()
 if parsed(out,'parsed')==parsed(out,'fresh'):continue
 ref=subprocess.run([str(R/'evidence/reference-probe')],input=inp,capture_output=True,timeout=2)
 if ref.returncode or parsed(ref.stdout.decode(),'parsed')!=parsed(ref.stdout.decode(),'fresh'):continue
 found.append({'index':i,'source':src,'start':a,'end':b,'replacement':new})
 (R/f'evidence/scanner-found-{len(found)}.bin').write_bytes(inp)
 if len(found)>=3:break
(R/'evidence/scanner-search.json').write_text(json.dumps({'seed':14023,'attempts':i+1,'found':found},indent=2)+'\n');print('found',len(found),'attempts',i+1)
