from pathlib import Path
import json,shutil,subprocess,sys
r=Path(__file__).resolve().parents[1]
near=r/'authoring/near-misses'
controls={'starter':r/'authoring/sources/restler-fuzzer-6d984deedbc54aad957fa3da0c7e9e5df23a2aee','reference-draft':r/'solution/reference-draft'}
for name in ('no-restore','ignore-fingerprint'):
    d=near/name
    shutil.copytree(r/'solution/reference-draft',d,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','RestlerResults','.pytest_cache'))
    p=d/'restler/utils/saver.py';s=p.read_text()
    if name=='no-restore': s=s.replace('if not _resume:', 'if True:')
    else: s=s.replace("header.get('fingerprint') != _fingerprint", 'False')
    p.write_text(s);controls[name]=d
controls['empty']=r/'authoring/empty';controls['empty'].mkdir(exist_ok=True)
summary={}
for name,candidate in controls.items():
    output=r/'authoring/evidence'/name
    command=[sys.executable,str(r/'tests/grader.py'),'--candidate',str(candidate),'--output',str(output),'--component-only']
    result=subprocess.run(command,capture_output=True,text=True)
    output.mkdir(exist_ok=True)
    (output/'command.json').write_text(json.dumps({'command':command,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2)+'\n')
    if (output/'score.json').exists():
        score=json.loads((output/'score.json').read_text())
        summary[name]={'formal_score':score['score'],'valid':score['valid'],'component_pass_rate':score['component_pass_rate'],'component_checks':score['component_checks']}
    else: summary[name]={'controller_exit':result.returncode,'error':result.stderr}
(r/'authoring/evidence/control-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
