#!/usr/bin/env python3
"""Freeze outputs from the freshly built official jq 1.7.1, never from starter."""
import pathlib, json, subprocess, collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
JQ=ROOT/'authoring/build/jq'
cases=[]
def add(group,name,program,data='',flags=(),source='jq-1.7.1 tests/jq.test and docs/content/manual/v1.7/manual.yml semantics; author integration input'):
    cases.append({'id':name,'group':group,'argv':['-c',*flags,program],'stdin':data,'source':source})
for name,p,d in [
 ('identity','.', '{"a":1}\n[2,3]\nnull\n'),('iterate','.[]','[1,null,false,3]'),
 ('comma','.a,.b','{"a":1,"b":2}'),('pipe','.[] | .v','[{"v":1},{"v":2}]'),
 ('cartesian','(.a[], .b[])','{"a":[1,2],"b":[3,4]}'),
 ('empty','empty','1\n2'),('array_collect','[.[] | .[]]','[[1,2],[3]]'),
 ('comma_binding','.[] | (., .+10)','[1,2]'),('input_sequence','.,inputs','1\n2\n3\n'),
 ('optional_iterate','.[]?','null\n[1,2]\n4'),('recursive','.. | numbers','{"a":[1,{"b":2}],"c":3}'),
 ('nested_products','[.a[],.b[]]','{"a":[1,2],"b":[3,4]}')]:add('streams',name,p,d)
for name,p,d in [
 ('object','{x:.a,y:[.b[]]}','{"a":2,"b":[3,4]}'),('index','.[-1]','[1,2,3]'),
 ('slice','.[1:3]','[0,1,2,3]'),('missing','.unknown','{}'),
 ('update','.a |= .+1','{"a":3,"b":4}'),('assign','.a.b = 7','{"a":{}}'),
 ('delete','del(.a[1])','{"a":[1,2,3],"b":4}'),('paths','paths(scalars)','{"a":[1,null],"b":true}'),
 ('getpath','getpath(["a",1])','{"a":[9,8]}'),('entries','to_entries | from_entries','{"z":1,"a":2}'),
 ('keys','keys','{"z":1,"a":2}'),('has','[has("a"),has("b")]','{"a":null}')]:add('structure',name,p,d)
for name,p,d in [
 ('arithmetic','(.a+.b)*2-1','{"a":3,"b":4}'),('division','[./2, .%2]','5'),
 ('types','[type,length]','[1,2,3]'),('array_add','[1,2]+[3]','null'),
 ('object_merge','{a:1,b:2}+{b:7,c:9}','null'),('deep_merge','{a:{b:1}}*{a:{c:2}}','null'),
 ('alternative','.a // .b // 99','{"a":false,"b":0}'),('truth','[false and true, null or 1, 0|not]','null'),
 ('compare','[1<2, "a"=="a", null==false, [1]<[2]]','null'),
 ('string','[ascii_upcase,split(" "),length]','"héllo world"'),
 ('sort','sort | unique','[3,1,2,1]'),('group','group_by(.k)|map(map(.v))','[{"k":2,"v":9},{"k":1,"v":3},{"k":2,"v":8}]')]:add('operators',name,p,d)
for name,p,d in [
 ('lexical','.a as $x | .b | .+$x','{"a":2,"b":3}'),
 ('scope','. as $x | [(.+1 as $x | $x),$x]','4'),
 ('generator_binding','.[] as $x | [$x,.]','[2,3]'),
 ('destructure','. as [$a,$b] | $b-$a','[3,10]'),
 ('function','def twice(f): f|f; twice(.+1)','5'),
 ('function_stream','def both(f): f,f; [both(.[])]','[1,2]'),
 ('recursion','def f: if .<2 then 1 else . * (.-1|f) end; f','7'),
 ('shadow','def f: 1; def g: f; def f: 2; [f,g]','null'),
 ('function_argument','def apply(f): [f]; apply(.a[])','{"a":[1,2]}'),
 ('object_binding','. as {a:$x,b:$y} | $x+$y','{"a":4,"b":5}')]:add('bindings',name,p,d)
for name,p,d in [
 ('if','.[] | if .>0 then "positive" elif .==0 then "zero" else "negative" end','[-1,0,3]'),
 ('select','.[]|select(.v>=2)|.v','[{"v":1},{"v":3},{"v":2}]'),
 ('try','[.[] | try .a catch "bad"]','[{"a":1},2,null]'),
 ('suppress','[.[] | .a?]','[{"a":1},2,null]'),
 ('catch_message','try error("boom") catch .','null'),
 ('range','[range(1;8;2)]','null'),('limit','[limit(3;range(10))]','null'),
 ('until','until(.>=20;.*2)','3'),('while','[while(.<10;.+3)]','1'),
 ('label','[label $out | range(5) | if .==3 then break $out else . end]','null')]:add('control',name,p,d)
for name,p,d in [
 ('reduce','reduce .[] as $x (0; .+$x)','[1,2,3,4]'),
 ('foreach','[foreach .[] as $x (0; .+$x; .)]','[2,3,4]'),
 ('object_reduce','reduce .[] as $x ({}; .[$x.k] += $x.v)','[{"k":"a","v":2},{"k":"a","v":3},{"k":"b","v":4}]'),
 ('reduce_empty','reduce .[] as $x (7; .+$x)','[]'),
 ('map_select','map(select(.>0)|.*2)','[-2,1,3]'),
 ('add','add','[1,2,3]'),('flatten','flatten','[1,[2,[3]],[]]'),
 ('any','[any(.[];.>2),all(.[];.>0)]','[1,2,3]'),
 ('minmax','[min_by(.v).k,max_by(.v).k]','[{"k":"a","v":2},{"k":"b","v":5}]'),
 ('sortby','sort_by(.a,.b)|map(.id)','[{"id":1,"a":1,"b":3},{"id":2,"a":0,"b":5},{"id":3,"a":1,"b":2}]')]:add('reductions',name,p,d)
add('cli','null_input','[1,2,3]','', ['-n'])
add('cli','slurp','map(.v)|add','{"v":1}\n{"v":3}\n',['-s'])
add('cli','raw','.[ ]','["hello",2,null]',['-r'])
add('cli','arg','[$x,$n+1]','null',['--arg','x','hello','--argjson','n','9'])
add('cli','exit_false','false','null',['-e'])
add('cli','exit_null','null','null',['-e'])
add('cli','exit_empty','empty','null',['-e'])
add('cli','exit_zero','0','null',['-e'])
add('cli','multiple_raw','.[]','["a\\nb","héllo"]',['-r'])
for name,p,d in [('compile','if . then','null'),('bad_token','???','null'),('runtime_index','.a','2'),('divide_zero','1/0','null'),('explicit','error("bad")','null'),('input_json','.', '{broken'),('partial_output','.,error("bad")','1'),('invalid_iterate','.[]','true'),('scope_error','$missing','null')]:add('errors',name,p,d)
version=subprocess.check_output([str(JQ),'--version'],text=True).strip();assert version=='jq-1.7.1'
for c in cases:
    p=subprocess.run([str(JQ),*c['argv']],input=c['stdin'],capture_output=True,text=True,timeout=3)
    c['expected']={'stdout':p.stdout,'stderr_nonempty':bool(p.stderr),'exit':p.returncode}
    c['oracle_stderr']=p.stderr
    # Catch author typo at generation time, retaining all genuine error cases.
    if c['group']!='errors' and p.returncode not in ([0,1,4] if '-e' in c['argv'] else [0]):raise RuntimeError((c,p.stderr))
(ROOT/'verifier/private/cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
dev=[next(c for c in cases if c['group']==g) for g in dict.fromkeys(c['group'] for c in cases)]
(ROOT/'environment/dev_cases.json').write_text(json.dumps(dev,ensure_ascii=False,indent=2)+'\n')
(ROOT/'authoring/oracle-evidence.json').write_text(json.dumps({'version':version,'path':str(JQ),'system_jq_version':subprocess.check_output(['/usr/bin/jq','--version'],text=True).strip(),'host_platform':__import__('platform').platform(),'groups':dict(collections.Counter(c['group'] for c in cases)),'case_count':len(cases)},indent=2)+'\n')
print(json.dumps({'count':len(cases),'groups':dict(collections.Counter(c['group'] for c in cases))}))
