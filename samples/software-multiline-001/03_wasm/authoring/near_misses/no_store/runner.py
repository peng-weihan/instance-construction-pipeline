#!/usr/bin/env python3
"""Wasm i32 profile reference. No third-party runtime or native Wasm engine."""
import json, sys, struct

class Invalid(Exception): pass
class Trap(Exception): pass
class Branch(Exception):
    def __init__(self, depth): self.depth=depth
class Return(Exception): pass

class Reader:
    def __init__(self,data): self.data=data; self.p=0
    def take(self,n):
        if n<0 or self.p+n>len(self.data): raise Invalid()
        x=self.data[self.p:self.p+n]; self.p+=n; return x
    def byte(self): return self.take(1)[0]
    def leb(self,signed=False):
        x=0; shift=0
        for _ in range(5):
            b=self.byte(); x|=(b&127)<<shift; shift+=7
            if not b&128:
                if signed and b&64: x-=1<<shift
                return x
        raise Invalid()
    def name(self): return self.take(self.leb()).decode('utf8')
    def done(self):
        if self.p!=len(self.data): raise Invalid()

def instructions(r):
    out=[]
    while True:
        op=r.byte()
        if op in (5,11): return out,op
        if op in (2,3,4):
            typ=r.byte()
            if typ not in (64,127): raise Invalid()
            body,end=instructions(r); other=[]
            if end==5:
                if op!=4: raise Invalid()
                other,end=instructions(r)
            if end!=11: raise Invalid()
            out.append((op,typ,body,other))
        elif op in (12,13,16,32,33,34): out.append((op,r.leb()))
        elif op==14:
            labels=[r.leb() for _ in range(r.leb())]; out.append((op,labels,r.leb()))
        elif op==65: out.append((op,r.leb(True)))
        elif 40<=op<=62: out.append((op,r.leb(),r.leb()))
        elif op in (63,64):
            if r.byte()!=0: raise Invalid()
            out.append((op,))
        elif op in (0,1,15,26,27) or 69<=op<=79 or 103<=op<=120: out.append((op,))
        else: raise Invalid()

def u(x): return x&0xffffffff
def s(x): return (u(x)^0x80000000)-0x80000000

class Module:
    def __init__(self,data):
        r=Reader(data)
        if r.take(8)!=b'\0asm\x01\0\0\0': raise Invalid()
        self.types=[]; self.funcs=[]; self.exports={}; self.memory=bytearray(); self.maximum=16; tids=[]; bodies=[]; segments=[]; prev=0
        while r.p<len(r.data):
            sid=r.byte(); q=Reader(r.take(r.leb()))
            if sid==0: continue
            if sid<=prev: raise Invalid()
            prev=sid
            if sid==1:
                for _ in range(q.leb()):
                    if q.byte()!=96: raise Invalid()
                    args=[q.byte() for _ in range(q.leb())]; ret=[q.byte() for _ in range(q.leb())]
                    if any(t!=127 for t in args+ret) or len(ret)>1: raise Invalid()
                    self.types.append((len(args),len(ret)))
            elif sid==3: tids=[q.leb() for _ in range(q.leb())]
            elif sid==5:
                if q.leb()!=1: raise Invalid()
                flag=q.leb(); minimum=q.leb(); self.maximum=q.leb() if flag==1 else 16
                if flag not in (0,1) or minimum>self.maximum or self.maximum>16: raise Invalid()
                self.memory=bytearray(minimum*65536)
            elif sid==7:
                for _ in range(q.leb()):
                    name=q.name(); kind=q.byte(); idx=q.leb(); self.exports[name]=(kind,idx)
            elif sid==10:
                for _ in range(q.leb()):
                    b=Reader(q.take(q.leb())); local=[]
                    for _ in range(b.leb()):
                        n=b.leb()
                        if b.byte()!=127 or n>10000: raise Invalid()
                        local.extend([0]*n)
                    code,end=instructions(b); b.done()
                    if end!=11: raise Invalid()
                    bodies.append((local,code))
            elif sid==11:
                for _ in range(q.leb()):
                    if q.leb()!=0 or q.byte()!=65: raise Invalid()
                    offset=q.leb(True)
                    if q.byte()!=11: raise Invalid()
                    segments.append((offset,q.take(q.leb())))
            else: raise Invalid()
            q.done()
        if len(tids)!=len(bodies): raise Invalid()
        for tid,body in zip(tids,bodies):
            if tid>=len(self.types): raise Invalid()
            self.funcs.append((tid,*body))
        for off,data in segments:
            if off<0 or off+len(data)>len(self.memory): raise Trap()
            self.memory[off:off+len(data)]=data
        self.fuel=200000; self.depth=0

    def call(self,index,args):
        if index>=len(self.funcs) or self.depth>200: raise Trap()
        tid,local,code=self.funcs[index]; nargs,nret=self.types[tid]
        if len(args)!=nargs: raise Trap()
        loc=[u(x) for x in args]+local.copy(); stack=[]; self.depth+=1
        try:
            try: self.run(code,stack,loc)
            except Return: pass
            except Branch as b:
                if b.depth!=0: raise Trap()
            return [u(stack[-1])] if nret else []
        finally: self.depth-=1

    def run(self,code,st,loc):
        for ins in code:
            self.fuel-=1
            if self.fuel<0: raise Trap()
            op=ins[0]
            if op==0: raise Trap()
            elif op==1: pass
            elif op in (2,3,4):
                _,typ,body,other=ins; body=body if op!=4 or st.pop()!=0 else other; h=len(st); nret=int(typ==127)
                while True:
                    try: self.run(body,st,loc)
                    except Branch as b:
                        if b.depth:
                            b.depth-=1; raise
                        vals=st[-nret:] if op!=3 and nret else []
                        del st[h:]; st.extend(vals)
                        if op==3: continue
                    break
            elif op==12: raise Branch(ins[1])
            elif op==13:
                if st.pop(): raise Branch(ins[1])
            elif op==14:
                i=u(st.pop()); raise Branch(ins[1][i] if i<len(ins[1]) else ins[2])
            elif op==15: raise Return()
            elif op==16:
                tid=self.funcs[ins[1]][0]; n=self.types[tid][0]; args=st[-n:] if n else []
                if n: del st[-n:]
                st.extend(self.call(ins[1],args))
            elif op==26: st.pop()
            elif op==27:
                c=st.pop(); b=st.pop(); a=st.pop(); st.append(a if c else b)
            elif op==32: st.append(loc[ins[1]])
            elif op==33: loc[ins[1]]=st.pop()
            elif op==34: loc[ins[1]]=st[-1]
            elif op in (40,44,45,46,47,54,58,59):
                stores={54:4,58:1,59:2}; loads={40:4,44:1,45:1,46:2,47:2}
                value=st.pop() if op in stores else None; addr=u(st.pop())+ins[2]; size=(stores if op in stores else loads)[op]
                if addr+size>len(self.memory): raise Trap()
                if value is not None: None
                else: st.append(u(int.from_bytes(self.memory[addr:addr+size],'little',signed=op in (44,46))))
            elif op==63: st.append(len(self.memory)//65536)
            elif op==64:
                delta=u(st.pop()); old=len(self.memory)//65536
                if old+delta>self.maximum: st.append(0xffffffff)
                else: self.memory.extend(bytes(delta*65536)); st.append(old)
            elif op==65: st.append(u(ins[1]))
            elif op==69: st.append(int(st.pop()==0))
            elif 70<=op<=79:
                b=st.pop(); a=st.pop(); aa=s(a) if op in (72,74,76,78) else u(a); bb=s(b) if op in (72,74,76,78) else u(b)
                st.append(int({70:lambda:a==b,71:lambda:a!=b,72:lambda:aa<bb,73:lambda:aa<bb,74:lambda:aa>bb,75:lambda:aa>bb,76:lambda:aa<=bb,77:lambda:aa<=bb,78:lambda:aa>=bb,79:lambda:aa>=bb}[op]()))
            elif op in (103,104,105):
                a=u(st.pop()); st.append((32-a.bit_length()) if op==103 else (32 if not a else ((a&-a).bit_length()-1)) if op==104 else a.bit_count())
            elif 106<=op<=120:
                b=u(st.pop()); a=u(st.pop()); k=b&31
                if op in (109,110,111,112):
                    if b==0: raise Trap()
                    if op==109 and a==0x80000000 and b==0xffffffff: raise Trap()
                    aa=s(a) if op in (109,111) else a; bb=s(b) if op in (109,111) else b
                    quotient=(abs(aa)//abs(bb))*(-1 if (aa<0)!=(bb<0) else 1)
                    v=quotient if op in (109,110) else aa-quotient*bb
                else: v={106:lambda:a+b,107:lambda:a-b,108:lambda:a*b,113:lambda:a&b,114:lambda:a|b,115:lambda:a^b,116:lambda:a<<k,117:lambda:s(a)>>k,118:lambda:a>>k,119:lambda:(a<<k)|(a>>((32-k)&31)),120:lambda:(a>>k)|(a<<((32-k)&31))}[op]()
                st.append(u(v))
            else: raise Invalid()

def handle(req):
    try:
        m=Module(bytes.fromhex(req['module'])); results=[]
        for c in req.get('calls',[]):
            try:
                kind,index=m.exports[c['export']]
                if kind!=0: raise Trap()
                values=m.call(index,c.get('args',[])); results.append(s(values[0]) if values else None)
            except (Trap,IndexError,KeyError,RecursionError): results.append({'trap':True})
        return {'results':results,'memory':[bytes(m.memory[x['offset']:x['offset']+x['length']]).hex() for x in req.get('memory',[])]}
    except (Invalid,ValueError,KeyError,IndexError,UnicodeError): return {'error':'invalid'}
    except Trap: return {'error':'trap'}

if __name__=='__main__':
    for line in sys.stdin:
        try: print(json.dumps(handle(json.loads(line)),separators=(',',':')))
        except Exception: print(json.dumps({'error':'internal'}))
