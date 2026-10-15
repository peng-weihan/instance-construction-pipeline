#!/usr/bin/env python3
"""Public starting point: a small, deliberately incomplete stream evaluator."""
import sys,json,re
class Compile(Exception):pass
class Runtime(Exception):pass
def split(s,sep):
    depth=0; quote=False; escape=False; out=[]; start=0
    for i,c in enumerate(s):
        if escape:escape=False;continue
        if c=='\\' and quote:escape=True;continue
        if c=='"':quote=not quote
        if quote:continue
        if c in '[({':depth+=1
        if c in '])}':depth-=1
        if c==sep and depth==0:out.append(s[start:i]);start=i+1
    return out+[s[start:]]
def evaluate(p,x,env):
    p=p.strip()
    parts=split(p,'|')
    if len(parts)>1:
        values=[x]
        for part in parts:values=[v for item in values for v in evaluate(part,item,env)]
        return values
    parts=split(p,',')
    if len(parts)>1:return [v for part in parts for v in evaluate(part,x,env)]
    if p=='.':return [x]
    if p=='empty':return []
    if p=='type':return ['null' if x is None else 'boolean' if isinstance(x,bool) else 'number' if isinstance(x,(int,float)) else 'string' if isinstance(x,str) else 'array' if isinstance(x,list) else 'object']
    if p=='length':return [0 if x is None else len(x)]
    if p=='keys':return [sorted(x) if isinstance(x,dict) else list(range(len(x)))]
    if p=='add':
        if not x:return [None]
        value=x[0]
        for other in x[1:]:value=value+other
        return [value]
    if p in ('sort','unique','flatten'):
        if p=='sort':return [sorted(x)]
        if p=='unique':return [sorted(set(x))]
        def flatten(v):return [y for a in v for y in flatten(a)] if isinstance(v,list) else [v]
        return [flatten(x)]
    if p.startswith('$') and re.fullmatch(r'\$\w+',p):
        if p[1:] not in env:raise Compile()
        return [env[p[1:]]]
    if p.startswith('[') and p.endswith(']'):return [[v for v in evaluate(p[1:-1],x,env)]]
    if p.startswith('map(') and p.endswith(')'):return [[v for a in x for v in evaluate(p[4:-1],a,env)]]
    if p in ('.[]','.[]?'):
        if isinstance(x,dict):return list(x.values())
        if isinstance(x,list):return x
        if p.endswith('?'):return []
        raise Runtime()
    if re.fullmatch(r'\.\w+(?:\.\w+)*',p):
        for name in p[1:].split('.'):
            if x is None:x=None
            elif isinstance(x,dict):x=x.get(name)
            else:raise Runtime()
        return [x]
    if re.fullmatch(r'\.\[-?\d+\]',p):
        n=int(p[2:-1]);return [x[n] if -len(x)<=n<len(x) else None]
    if re.fullmatch(r'\.\[-?\d*:-?\d*\]',p):
        a,b=p[2:-1].split(':');return [x[int(a) if a else None:int(b) if b else None]]
    try:return [json.loads(p)]
    except:raise Compile()
def main():
    args=sys.argv[1:]; flags=set();env={};program=None;i=0
    while i<len(args):
        a=args[i]
        if a in ('--arg','--argjson'):
            env[args[i+1]]=args[i+2] if a=='--arg' else json.loads(args[i+2]);i+=3;continue
        if a.startswith('-'):flags.update(a[1:]);i+=1;continue
        program=a;i+=1
    if program is None:sys.exit(3)
    raw=sys.stdin.read();decoder=json.JSONDecoder();values=[];pos=0
    try:
        while pos<len(raw):
            if raw[pos].isspace():pos+=1;continue
            value,end=decoder.raw_decode(raw,pos);values.append(value);pos=end
    except Exception:print('parse error',file=sys.stderr);sys.exit(4)
    if 'n' in flags:values=[None]
    if 's' in flags:values=[values]
    last='none'
    try:
        for value in values:
            for v in evaluate(program,value,env):
                print(v if 'r' in flags and isinstance(v,str) else json.dumps(v,ensure_ascii=False,separators=(',',':')))
                last=v
    except Compile:print('compile error',file=sys.stderr);sys.exit(3)
    except Exception:sys.exit(0)
    if 'e' in flags:sys.exit(4 if last=='none' else 1 if last is None or last is False else 0)
if __name__=='__main__':main()
