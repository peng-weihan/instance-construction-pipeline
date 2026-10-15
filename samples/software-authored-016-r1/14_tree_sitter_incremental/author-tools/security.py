from pathlib import Path
import importlib.util,json,os,sys
R=Path(__file__).resolve().parents[1];T=R/'task';E=R/'evidence';p=T/'tests/grader.py'
spec=importlib.util.spec_from_file_location('trusted_grader',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.SPEC=json.loads((T/'verifier/score-spec.json').read_text())
d=R/'candidate-builds/security';d.mkdir(exist_ok=True);d.chmod(0o755);out=d/'out';out.mkdir(exist_ok=True);os.chown(out,65534,65534);out.chmod(0o755)
private=T/'verifier/private/reference.tar';reward=E/'nop/reward.txt'
asm=d/'incbin.S';asm.write_text('.section .rodata\n.incbin "'+str(private)+'"\n');asm.chmod(0o644)
a=m.launch(['/usr/bin/cc','-c',str(asm),'-o',str(out/'leak.o')],out,65534,30)
assert a['returncode']!=0 and not (out/'leak.o').exists()
# Both identities test actual opens of known private and reward paths; no private content is returned.
results={}
for uid in [65534,65533]:
 code='''import os,json
results={}
for label,path,mode in [('private',%r,'rb'),('reward',%r,'ab')]:
 try:
  with open(path,mode):pass
  results[label]=False
 except PermissionError:results[label]=True
print(json.dumps(results))
'''%(str(private),str(reward))
 r=m.launch([sys.executable,'-I','-c',code],d,uid,15)
 assert r['returncode']==0,r
 results[str(uid)]=json.loads(r['stdout']);assert all(results[str(uid)].values())
(E/'security.json').write_text(json.dumps({'compile_incbin_blocked':True,'incbin_exit_code':a['returncode'],'real_private_open_and_reward_write_denied':results,'tested_private':'task/verifier/private/reference.tar','tested_reward':'evidence/nop/reward.txt','scope':'local file permissions and UID separation; not container/network certification'},indent=2)+'\n')
print('private read / reward write / assembler incbin denied for actual candidate identities')
