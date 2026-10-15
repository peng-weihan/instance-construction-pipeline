from pathlib import Path
import os,json,subprocess,shutil,hashlib,struct,sys
R=Path(__file__).resolve().parents[1];T=R/'task';E=R/'evidence';E.mkdir(exist_ok=True)
commands=[]
def run(name,args,**kw):
 p=subprocess.run(args,capture_output=True,text=True,**kw);(E/(name+'.log')).write_text(p.stdout+p.stderr);commands.append({'name':name,'command':args,'exit_code':p.returncode});return p
# Execute the actual solution with an author-local explicit target.
injected=E/'injected-reference';shutil.copytree(T/'environment/starter',injected,dirs_exist_ok=True)
env={'PATH':'/usr/bin:/bin','SUBMISSION_ROOT':str(injected)}
p=run('solution-injection',['/bin/sh',str(T/'solution/solve.sh')],env=env);assert p.returncode==0,p.stderr
mismatches=[]
for p in (R/'material-src/tree-sitter').rglob('*'):
 if '.git' in p.parts or not p.is_file():continue
 q=injected/p.relative_to(R/'material-src/tree-sitter')
 if not q.is_file() or p.read_bytes()!=q.read_bytes():mismatches.append(str(q))
(E/'inverse-replay.json').write_text(json.dumps({'actual_solve_sh':True,'complete_reference_matches':not mismatches,'mismatches':mismatches},indent=2)+'\n');assert not mismatches
# Repeat immutable source controls with distinct result paths, using exactly the final frozen scoring spec.
for name,source in [('reference-repeat',R/'material-src/tree-sitter'),('nop-repeat',T/'environment/starter'),('online-baseline-repeat',E/'controls/full_reparse_starter'),('injected-reference',injected)]:
 p=run(name,[sys.executable,str(T/'tests/grader.py'),'--submission',str(source),'--base',str(T/'verifier'),'--output',str(E/name),'--build-parent',str(R/'candidate-builds')]);assert p.returncode==0,p.stdout+p.stderr
# Ordinary compile failures are scored. Simulated corrupt oracle must invalidate and remove stale rewards.
bad=E/'invalid-candidate';(bad/'lib/src').mkdir(parents=True,exist_ok=True);(bad/'lib/src/lib.c').write_text('#include "missing_candidate_header.h"\n')
p=run('candidate-failure',[sys.executable,str(T/'tests/grader.py'),'--submission',str(bad),'--base',str(T/'verifier'),'--output',str(E/'candidate-failure'),'--build-parent',str(R/'candidate-builds')]);assert p.returncode==0
r=json.loads((E/'candidate-failure/score.json').read_text());assert r['valid'] and r['score']==0 and (E/'candidate-failure/reward.txt').exists()
corrupt=E/'corrupt-judge';shutil.copytree(T/'verifier',corrupt,dirs_exist_ok=True);(corrupt/'private').chmod(0o700);(corrupt/'private/rename_same_shape.out').write_text('corrupted audit copy\n')
output=E/'infrastructure-failure';output.mkdir(exist_ok=True);(output/'reward.txt').write_text('0.75\n');(output/'reward.json').write_text('{"reward":0.75}')
p=run('infrastructure-failure',[sys.executable,str(T/'tests/grader.py'),'--submission',str(T/'environment/starter'),'--base',str(corrupt),'--output',str(output),'--build-parent',str(R/'candidate-builds')]);assert p.returncode==2
r=json.loads((output/'score.json').read_text());assert not r['valid'] and r['score'] is None and not (output/'reward.txt').exists() and not (output/'reward.json').exists()
(E/'checks-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
print(json.dumps({'inverse_patch':True,'repeats':4,'candidate_failure_valid_zero':True,'corrupt_reference_invalid_no_reward':True}))
