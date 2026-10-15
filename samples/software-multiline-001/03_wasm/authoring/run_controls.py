#!/usr/bin/env python3
"""Host-only trusted author controls; this is not Harbor/container acceptance."""
import pathlib,subprocess,sys,shutil,json,platform,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];wasm=ROOT.name=='03_wasm'
controls=ROOT/'authoring/controls';reference=controls/'reference_submission';reference.mkdir(exist_ok=True)
if wasm:shutil.copy2(ROOT/'solution/runtime.py',reference/'runner.py')
else:
    shutil.copy2(ROOT/'solution/runner.py',reference/'runner.py');shutil.copy2(ROOT/'authoring/build/jq',reference/'jq')
jobs=[('reference',reference),('reference_repeat',reference),('starter',ROOT/'environment/submission'),('nop',controls/'nop_submission')]
jobs += [(p.name,p) for p in sorted((ROOT/'authoring/near_misses').iterdir())]
(controls/'nop_submission').mkdir(exist_ok=True)
commands=[]
for name,submission in jobs:
    logs=controls/name
    cmd=[sys.executable,str(ROOT/'tests/grader.py'),'--submission',str(submission),'--cases',str(ROOT/'verifier/private/cases.json'),'--logs',str(logs)]
    p=subprocess.run(cmd,text=True,capture_output=True,timeout=900)
    evidence={'command':cmd,'cwd':str(ROOT),'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode,'platform':platform.platform(),'host_only':True}
    logs.mkdir(exist_ok=True);(logs/'command.json').write_text(json.dumps(evidence,indent=2)+'\n');commands.append(evidence)
    if p.returncode:raise RuntimeError(evidence)
    print(name,p.stdout.strip())
# Confirm ordinary candidate syntax failure remains a valid scored submission.
bad=controls/'syntax_submission';bad.mkdir(exist_ok=True);(bad/'runner.py').write_text('this is invalid Python !\n')
cmd=[sys.executable,str(ROOT/'tests/grader.py'),'--submission',str(bad),'--cases',str(ROOT/'verifier/private/cases.json'),'--logs',str(controls/'syntax')]
p=subprocess.run(cmd,text=True,capture_output=True,timeout=900);commands.append({'command':cmd,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode})
assert p.returncode==0 and json.loads((controls/'syntax/score.json').read_text())['score']==0
# A damaged trusted fixture must leave score null and no numeric reward.
damaged=controls/'damaged_fixture';damaged.mkdir(exist_ok=True);(damaged/'cases.json').write_text('broken');(damaged/'cases.sha256').write_text('0'*64)
cmd=[sys.executable,str(ROOT/'tests/grader.py'),'--submission',str(reference),'--cases',str(damaged/'cases.json'),'--logs',str(controls/'infra_failure')]
p=subprocess.run(cmd,text=True,capture_output=True,timeout=30);commands.append({'command':cmd,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode})
report=json.loads((controls/'infra_failure/score.json').read_text());assert p.returncode!=0 and report['valid']==False and not (controls/'infra_failure/reward.txt').exists()
(controls/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
scores={name:json.loads((controls/name/'score.json').read_text())['score'] for name,_ in jobs}
spec=json.loads((ROOT/'authoring/score-spec.json').read_text());spec['reference_observation']={'score':scores['reference'],'evidence':'controls/reference/score.json','host_only':True};spec['baseline_observation']={'score':scores['starter'],'evidence':'controls/starter/score.json','host_only':True};(ROOT/'authoring/score-spec.json').write_text(json.dumps(spec,indent=2)+'\n')
(controls/'summary.json').write_text(json.dumps({'scores':scores,'reference_repeat_equal':scores['reference']==scores['reference_repeat'],'syntax_valid_zero':True,'fixture_corruption_invalid_no_reward':True,'container_isolation_verified':False},indent=2)+'\n')
