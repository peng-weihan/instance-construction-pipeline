#!/usr/bin/env python3
"""Trusted deterministic grader. Candidate C is compiled and run under separate UIDs."""
import argparse,hashlib,json,os,resource,shutil,signal,stat,subprocess,tempfile,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent if (ROOT.parent/'private').is_dir() else Path('/opt/judge')
SPEC=json.loads((BASE/'score-spec.json').read_text()) if (BASE/'score-spec.json').exists() else None

def sections(data):
 out={};tag=None;acc=[]
 for line in data.decode('utf-8',errors='strict').splitlines():
  if line=='@end':
   if tag is None:raise ValueError('orphan section')
   out.setdefault(tag,[]).append('\n'.join(acc));tag=None;acc=[]
  elif line.startswith('@'):
   if tag is not None:raise ValueError('nested section')
   tag=line[1:]
  elif tag is not None:acc.append(line)
  else:raise ValueError('unframed output')
 if tag is not None:raise ValueError('unfinished output')
 return out

def launch(cmd,cwd,uid,timeout,stdin=b''):
 def isolate():
  os.setsid();os.umask(0o077)
  resource.setrlimit(resource.RLIMIT_CPU,(timeout,timeout))
  resource.setrlimit(resource.RLIMIT_AS,(SPEC['limits']['memory_bytes'],)*2)
  resource.setrlimit(resource.RLIMIT_FSIZE,(SPEC['limits']['output_bytes'],)*2)
  resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  resource.setrlimit(resource.RLIMIT_NPROC,(SPEC['limits']['compile_processes'] if uid==SPEC['identities']['compile_uid'] else SPEC['limits']['run_processes'],)*2)
  os.setgroups([]);os.setgid(uid);os.setuid(uid)
  # No privilege recovery via exec of a setuid file.
  import ctypes
  if ctypes.CDLL(None).prctl(38,1,0,0,0)!=0:os._exit(125)
 with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
  p=subprocess.Popen(cmd,cwd=cwd,stdin=subprocess.PIPE,stdout=out,stderr=err,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','HOME':str(cwd),'TMPDIR':str(cwd)},preexec_fn=isolate)
  timed=False
  try:p.communicate(stdin,timeout=timeout)
  except subprocess.TimeoutExpired:timed=True;p.kill();p.communicate()
  finally:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  out.seek(0);err.seek(0)
  return {'returncode':p.returncode,'timeout':timed,'stdout':out.read(SPEC['limits']['output_bytes']),'stderr':err.read(SPEC['limits']['diagnostic_bytes']).decode(errors='replace')}

def snapshot(src,dst):
 # Only the core source tree is candidate-controlled. Never execute their build scripts.
 origin=src/'lib/src'
 for p in [src,src/'lib',origin]:
  if p.is_symlink() or not p.is_dir():raise ValueError('missing or symlinked lib/src')
 count=total=0
 for p in sorted(origin.rglob('*')):
  if p.is_symlink():raise ValueError('symlink in source')
  if p.is_dir():continue
  if not stat.S_ISREG(p.stat().st_mode):raise ValueError('non-regular source')
  if p.suffix not in {'.c','.h'}:continue
  count+=1;total+=p.stat().st_size
  if count>SPEC['limits']['source_files'] or total>SPEC['limits']['source_bytes']:raise ValueError('source budget exceeded')
  q=dst/'src'/p.relative_to(origin);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());q.chmod(0o644)
 if not (dst/'src/lib.c').is_file():raise ValueError('missing lib.c')
 for p in (dst/'src').rglob('*'):
  if p.is_dir():p.chmod(0o755)
 (dst/'src').chmod(0o755)

def trusted_objects(base,build):
 # Build trusted native harness and frozen grammar separately; compiler problems here are infrastructure failures.
 include=base/'public/include';grammar=base/'public/grammar/src'
 for name,src in [('probe',base/'probe.c'),('grammar',grammar/'parser.c'),('scanner',grammar/'scanner.c')]:
  p=subprocess.run(['/usr/bin/cc','-std=c11','-D_DEFAULT_SOURCE','-O1','-I'+str(include),'-I'+str(grammar),'-c',str(src),'-o',str(build/(name+'.o'))],capture_output=True,timeout=SPEC['limits']['compile_seconds'])
  if p.returncode:raise RuntimeError('trusted compilation failed: '+p.stderr.decode(errors='replace')[:SPEC['limits']['diagnostic_bytes']])
  (build/(name+'.o')).chmod(0o644)

def grade(submission,base,build_parent):
 global SPEC
 SPEC=json.loads((base/'score-spec.json').read_text())
 if os.geteuid()!=0:raise RuntimeError('grader must start as root to isolate candidate identities')
 if not Path('/usr/bin/cc').is_file():raise RuntimeError('promised compiler unavailable')
 private=base/'private'
 if private.stat().st_mode & 0o077:raise RuntimeError('private directory must be mode 0700')
 for rel,digest in json.loads((private/'oracle-hashes.json').read_text()).items():
  if hashlib.sha256((private/rel).read_bytes()).hexdigest()!=digest:raise RuntimeError('corrupt oracle asset: '+rel)
 cases=json.loads((private/'cases.json').read_text());checks=[];diagnostics={}
 build_parent.mkdir(parents=True,exist_ok=True);build_parent.chmod(0o755)
 with tempfile.TemporaryDirectory(prefix='grade-',dir=build_parent) as d:
  d=Path(d);d.chmod(0o755);trusted=d/'trusted';trusted.mkdir(mode=0o755)
  trusted_objects(base,trusted)
  sandbox=d/'candidate';sandbox.mkdir(mode=0o755)
  try:snapshot(submission,sandbox)
  except (ValueError,OSError) as e:
   diagnostics['candidate_error']=str(e);compiled=False
  else:
   build=sandbox/'build';build.mkdir(mode=0o755);os.chown(build,SPEC['identities']['compile_uid'],SPEC['identities']['compile_uid'])
   # Frozen headers and trusted object files are read-only to both candidate UIDs.
   inc=d/'include';shutil.copytree(base/'public/include',inc)
   compile_cmd=['/usr/bin/cc','-std=c11','-D_DEFAULT_SOURCE','-O1','-I'+str(inc),'-I'+str(sandbox/'src'),str(sandbox/'src/lib.c'),*[str(trusted/(n+'.o')) for n in ['probe','grammar','scanner']],'-o',str(build/'probe')]
   p=launch(compile_cmd,build,SPEC['identities']['compile_uid'],SPEC['limits']['compile_seconds'])
   compiled=p['returncode']==0 and not p['timeout']
   if compiled:
    binary=build/'probe'
    if binary.is_symlink() or not binary.is_file():compiled=False
    else:binary.chmod(0o755)
   diagnostics['compile']={k:v for k,v in p.items() if k!='stdout'}
  for c in cases:
   expected=sections((private/c['expected']).read_bytes());observed={};problem='compile failure'
   if compiled:
    r=launch([str(sandbox/'build/probe')],sandbox,SPEC['identities']['run_uid'],SPEC['limits']['case_seconds'],(private/c['input']).read_bytes())
    problem='timeout' if r['timeout'] else 'execution failure'
    if r['returncode']==0 and not r['timeout']:
     try:observed=sections(r['stdout']);problem='output mismatch'
     except (UnicodeError,ValueError):problem='invalid output'
   for group in c['groups']:
    tags=SPEC['group_tags'][group]
    passed=bool(observed) and all(observed.get(t)==expected.get(t) for t in tags)
    if c.get('native_expected') and group=='initial':passed=passed and observed.get('sexp')==[c['native_expected']]
    checks.append({'name':c['id']+'/'+group,'group':group,'passed':passed,'detail':'ok' if passed else problem})
 groups={}
 for group,weight in SPEC['weights'].items():
  selected=[c for c in checks if c['group']==group];passed=sum(c['passed'] for c in selected)
  if not selected:raise RuntimeError('empty scoring dimension: '+group)
  if [c['name'] for c in selected]!=SPEC['membership'][group]:raise RuntimeError('group membership drift')
  groups[group]={'passed':passed,'total':len(selected),'fraction':passed/len(selected),'weight':weight}
 score=sum(v['fraction']*v['weight'] for v in groups.values())
 return {'valid':True,'score':score,'pass_rate':sum(c['passed'] for c in checks)/len(checks),'checks':checks,'metrics':{'groups':groups,'compiled':compiled},'diagnostics':diagnostics,'scoring_version':SPEC['version']}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--submission',type=Path,default=Path('/home/workspace/tree-sitter/submission'));ap.add_argument('--base',type=Path,default=BASE);ap.add_argument('--output',type=Path,default=Path('/logs/verifier'));ap.add_argument('--build-parent',type=Path,default=Path('/candidate-builds'));a=ap.parse_args()
 a.output.mkdir(parents=True,exist_ok=True);a.output.chmod(0o700)
 for n in ['reward.txt','reward.json']:(a.output/n).unlink(missing_ok=True)
 try:r=grade(a.submission.resolve(),a.base.resolve(),a.build_parent.resolve());code=0
 except Exception as e:r={'valid':False,'score':None,'error':str(e),'traceback':traceback.format_exc()};code=2
 (a.output/'score.json').write_text(json.dumps(r,indent=2)+'\n')
 if r['valid']:(a.output/'reward.txt').write_text(format(r['score'],'.17g')+'\n')
 print(json.dumps({k:v for k,v in r.items() if k not in ['checks','traceback','diagnostics']}));return code
if __name__=='__main__':raise SystemExit(main())
