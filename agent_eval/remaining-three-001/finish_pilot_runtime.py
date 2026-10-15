from pathlib import Path
import hashlib,json
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for kind in ['game','finance']:
 out=ROOT/(kind+'-pilot');F=out/'framework';task=out/'task'
 profile=json.loads((task/'pipeline-profile.json').read_text());profile['judge_cpuset']='2,3' if kind=='game' else '4,5';(task/'pipeline-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
 p=F/'edgebench_harbor/restler_scorer.py';s=p.read_text().replace("self.timeout_sec=timeout_sec;self.submission_root=", "self.timeout_sec=timeout_sec;self.cpuset=json.loads((self.task_dir/'pipeline-profile.json').read_text())['judge_cpuset'];self.submission_root=")
 s=s.replace("'--cpus','2','--memory'", "'--cpus','2','--cpuset-cpus',self.cpuset,'--memory'")
 p.write_text(s)
 inventory={p.relative_to(F).as_posix():sha(p) for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='framework-version.json'}
 tree=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()
 (F/'framework-version.json').write_text(json.dumps({'status':'frozen','kind':'six_hour_engineering_pilot','formal_acceptance':False,'runtime_tree_sha256':tree,'runtime_file_hashes':inventory},indent=2)+'\n')
 p=out/'preparation.json';d=json.loads(p.read_text());d['runtime_tree_sha256']=tree;p.write_text(json.dumps(d,indent=2)+'\n')
 print('frozen',kind,tree,flush=True)
