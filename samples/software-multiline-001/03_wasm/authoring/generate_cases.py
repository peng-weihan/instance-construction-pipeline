#!/usr/bin/env python3
import json, re, subprocess, pathlib, collections
from wasmtime import wat2wasm
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=ROOT/'authoring/sources/spec-d910f03bd6d6477656fc5070b5098e8f909305d3'
cases=[]
def add(group,name,wat,calls,memory=None,source='author adaptation of official instruction semantics'):
    req={'module':bytes(wat2wasm(wat)).hex(),'calls':[{'export':n,'args':a} for n,a in calls]}
    if memory: req['memory']=memory
    cases.append({'id':name,'group':group,'request':req,'source':source,'wat':wat})
text=(SPEC/'test/core/i32.wast').read_text(); end=text.index('\n(assert_')
wat='\n'.join(line for line in text[:end].splitlines() if 'extend8_s' not in line and 'extend16_s' not in line)
seen=collections.Counter()
for line in text[end:].splitlines():
    m=re.match(r'\(assert_(return|trap) \(invoke "([^"]+)"((?: \(i32.const [^)]+\))*)\)',line)
    if not m: continue
    mode,op,args=m.groups()
    if 'extend' in op: continue
    seen[op]+=1
    if seen[op]>6: continue
    nums=[int(x.replace('_',''),0) for x in re.findall(r'\(i32.const ([^)]+)\)',args)]
    nums=[((x&0xffffffff)^0x80000000)-0x80000000 for x in nums]
    group='traps' if mode=='trap' else 'integer'
    add(group,f'official_i32_{op}_{seen[op]}',wat,[(op,nums)],source='test/core/i32.wast:'+line)

control='''(module
 (func (export "choose") (param i32) (result i32)
   (if (result i32) (local.get 0) (then (i32.const 17)) (else (i32.const -9))))
 (func (export "escape") (param i32) (result i32)
   (block (result i32) (i32.const 41) (local.get 0) (br_if 0) (drop) (i32.const 23)))
 (func (export "nested") (param i32) (result i32)
   (block (result i32) (block (i32.const 12) (local.get 0) (br_if 1) (drop)) (i32.const 99)))
 (func (export "table") (param i32) (result i32) (local i32)
   (block (block (block (local.get 0) (br_table 0 1 2)) (i32.const 10) (local.set 1) (br 1)) (i32.const 20) (local.set 1)) (local.get 1))
 (func (export "sel") (param i32 i32 i32) (result i32) (select (local.get 0) (local.get 1) (local.get 2))))'''
for op in ['choose','escape','nested','table']:
    for x in [0,1,2,-1]: add('control',f'{op}_{x}',control,[(op,[x])],source='adapted test/core/{if,br_if,br_table,block}.wast')
for x in [0,1,-1]: add('control',f'select_{x}',control,[('sel',[9,-3,x])],source='adapted test/core/select.wast')
loop='''(module (func (export "sum") (param $n i32) (result i32) (local $s i32)
 (block $out (loop $again (br_if $out (i32.eqz (local.get $n)))
 (local.set $s (i32.add (local.get $s) (local.get $n)))
 (local.set $n (i32.sub (local.get $n) (i32.const 1))) (br $again))) (local.get $s)))'''
for n in [0,1,2,10,100,1000]: add('loops',f'loop_sum_{n}',loop,[('sum',[n])],source='adapted test/core/loop.wast and br_if.wast')
call='''(module
 (func $fact (export "fact") (param $n i32) (result i32)
   (if (result i32) (i32.le_u (local.get $n) (i32.const 1)) (then (i32.const 1))
    (else (i32.mul (local.get $n) (call $fact (i32.sub (local.get $n) (i32.const 1)))))))
 (func $sub (param i32 i32) (result i32) (i32.sub (local.get 0) (local.get 1)))
 (func (export "compose") (param i32) (result i32) (call $sub (call $fact (local.get 0)) (i32.const 7)))
 (func (export "early") (param i32) (result i32) (local.get 0) (return) (i32.const 9)))'''
for n in [0,1,2,6,12]: add('calls',f'factorial_{n}',call,[('fact',[n]),('compose',[n]),('early',[n])],source='adapted test/core/call.wast recursive factorial and return semantics')
memory='''(module (memory (export "memory") 1 2) (data (i32.const 3) "ABC\\ff")
 (func (export "write") (param i32 i32) (local.get 0) (local.get 1) (i32.store))
 (func (export "read") (param i32) (result i32) (i32.load (local.get 0)))
 (func (export "signed8") (param i32) (result i32) (i32.load8_s (local.get 0)))
 (func (export "unsigned8") (param i32) (result i32) (i32.load8_u (local.get 0)))
 (func (export "signed16") (param i32) (result i32) (i32.load16_s (local.get 0)))
 (func (export "narrow") (param i32 i32) (i32.store8 (local.get 0) (local.get 1)))
 (func (export "grow") (param i32) (result i32) (memory.grow (local.get 0)))
 (func (export "size") (result i32) (memory.size)))'''
for addr in [0,1,7,65532]:
    add('memory',f'memory_roundtrip_{addr}',memory,[('write',[addr,-12345]),('read',[addr]),('signed8',[addr]),('unsigned8',[addr]),('signed16',[addr])],[{'offset':addr,'length':4}],source='adapted test/core/{memory,store,load,endianness}.wast')
for delta in [0,1,2,-1]: add('memory',f'grow_{delta}',memory,[('size',[]),('grow',[delta]),('size',[])],source='adapted test/core/memory_grow.wast')
for addr in [65533,65536,-1]: add('traps',f'oob_{addr}',memory,[('read',[addr]),('write',[addr,1]),('size',[])],source='adapted test/core/{load,store}.wast')
add('traps','unreachable','(module (func (export "f") (result i32) unreachable))',[('f',[])],source='test/core/unreachable.wast semantics')
for n in [3,9,32,200]:
    comp='''(module (memory (export "memory") 1)
     (func $step (param i32) (result i32) (i32.add (i32.mul (local.get 0) (i32.const 3)) (i32.const 1)))
     (func (export "run") (param $n i32) (result i32) (local $i i32)
      (block $done (loop $next (br_if $done (i32.ge_u (local.get $i) (local.get $n)))
       (i32.store (i32.mul (local.get $i) (i32.const 4)) (call $step (local.get $i)))
       (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next)))
      (i32.load (i32.mul (i32.sub (local.get $n) (i32.const 1)) (i32.const 4)))))'''
    add('composition',f'loop_call_store_{n}',comp,[('run',[n])],[{'offset':0,'length':min(n,12)*4}],source='author integration of official loop/call/store semantics')
for name,data in [('magic',b'BAD!\1\0\0\0'),('version',b'\0asm\2\0\0\0'),('truncated',b'\0asm\1\0\0\0\1\xff'),('size',b'\0asm\1\0\0\0\1\x05\x00')]:
    cases.append({'id':name,'group':'binary','request':{'module':data.hex()},'source':'test/core/binary.wast header/section framing semantics'})
requests=''.join(json.dumps(c['request'])+'\n' for c in cases)
p=subprocess.run(['node',str(ROOT/'authoring/oracle.js')],input=requests,text=True,capture_output=True,check=True)
expected=[json.loads(x) for x in p.stdout.splitlines()]
assert len(expected)==len(cases)
for c,e in zip(cases,expected): c['expected']=e
private=ROOT/'verifier/private';private.mkdir(parents=True,exist_ok=True)
(private/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
dev=[]
for group in dict.fromkeys(c['group'] for c in cases):
    dev.append(next(c for c in cases if c['group']==group))
(ROOT/'environment/dev_cases.json').write_text(json.dumps(dev,indent=2)+'\n')
(ROOT/'authoring/oracle-evidence.json').write_text(json.dumps({'command':['node','authoring/oracle.js'],'node_version':subprocess.check_output(['node','--version'],text=True).strip(),'stderr':p.stderr,'case_count':len(cases),'groups':dict(collections.Counter(c['group'] for c in cases))},indent=2)+'\n')
print(json.dumps({'cases':len(cases),'groups':dict(collections.Counter(c['group'] for c in cases))}))
