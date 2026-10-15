from pathlib import Path
import importlib.util,json,shutil,os
r=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('edgebench_grader',r/'task/tests/grader.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
scoring=json.loads((r/'task/verifier/private/score-spec.json').read_text());runner=module.Runner(scoring,r/'.venv-offline/bin/python')
work=r/'.tmp/extra-audit'
if work.exists():shutil.rmtree(work)
work.mkdir(mode=0o755)
shutil.copytree(r/'evidence/generated-ref',work/'generated')
shutil.copyfile(r/'task/tests/worker.py',work/'worker.py');(work/'tmp').mkdir();module.prepare_dirs(work/'tmp',runner.uid,runner.gid)
records=[]
for mode in ['sync','async']:
 for config in [{'mode':mode,'action':'records','lazy':True},{'mode':mode,'action':'anonymous','auth_header_name':'X-Private-Key'}]:
  p=runner.run(['-I',str(work/'worker.py'),str(work/'generated'),json.dumps(config)],work,scoring['limits']['probe_wall_sec'])
  line=[x[7:] for x in p['output'].splitlines() if x.startswith('RESULT ')][-1];data=json.loads(line)
  good=not data.get('fatal') and not data.get('error') and not data['client_closed'] and data['after_exit'].count(['close'])==1
  if config.get('lazy'):good=good and data['values']==scoring['oracle']['record_values']
  else:good=good and all('authorization' not in x['headers'] and 'x-private-key' not in x['headers'] for x in data['requests']) and data['default_headers']['x-private-key']=='custom-secret'
  records.append({'config':config,'passed':good,'trace':data});assert good
reward=r/'evidence/audit/permission-reward';reward.mkdir(exist_ok=True);reward.chmod(0o700)
code='''import json,sys
results={}
for name,path,mode in [('private_read',sys.argv[1],'rb'),('reward_write',sys.argv[2],'w')]:
 try:
  with open(path,mode):pass
  results[name]='ALLOWED'
 except PermissionError:results[name]='DENIED'
print(json.dumps(results))
'''
p=runner.run(['-I','-c',code,str(r/'task/verifier/private/reference.patch'),str(reward/'candidate-write')],work,scoring['limits']['probe_wall_sec'])
permission=json.loads(p['output']);assert permission=={'private_read':'DENIED','reward_write':'DENIED'}
(rootout:=r/'evidence/audit/extra-contract.json').write_text(json.dumps({'checks':records,'permission':permission,'uid':runner.uid,'interpreter':runner.python},indent=2,ensure_ascii=False)+'\n')
print('lazy clients, custom auth headers and actual access denial passed')
