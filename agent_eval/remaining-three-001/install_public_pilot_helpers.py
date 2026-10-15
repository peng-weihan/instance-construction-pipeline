"""Offline development helpers for public material only; does not change scoring."""
from pathlib import Path
import json,shutil
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001')
for kind in ['finance','game']:
 out=ROOT/(kind+'-pilot');task=out/'task';public=task/'environment/public'
 (task/'tests/test.sh').write_text('#!/bin/sh\nset -eu\nexec /opt/runtime/venv/bin/python /judge/verifier/judge_entry.py\n')
 if kind=='finance':
  ledger=(ROOT/'finance-task-r3/verifier/ledger.py').read_text().replace('from runtime import','from public_contract import')
  (public/'ledger.py').write_text(ledger)
  (public/'public_contract.py').write_text("from pathlib import Path\nimport json,math\nclass SubmissionError(Exception):pass\ndef finite(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)\ndef scoring_constants():return json.loads(Path(__file__).with_name('scoring_metadata.json').read_text())['constants']\n")
  helper='''import csv,json,importlib.util,sys
from pathlib import Path
import numpy as np
from ledger import simulate
import baseline_policy
root=Path(__file__).parent
spec=importlib.util.spec_from_file_location('candidate',Path(sys.argv[1]));policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
rows=[]
for name in ['train_prices.csv','dev_prices.csv']:
 with (root/'data'/name).open() as f:r=csv.reader(f);header=next(r);rows.extend(list(r))
for year in [2012,2013]:
 for label,cost,target in [('ordinary',.0005,.10),('costly',.002,.085)]:
  indices=[i for i,r in enumerate(rows) if str(year)<=r[0]<str(year+1)];first=indices[0];begin=max(0,first-253)
  p=np.array([[float(x) for x in r[1:]] for r in rows[begin:indices[-1]+1]]);p=100*p/p[0]
  dates=['step-%05d'%i for i in range(len(p))];assets=header[1:];mandate={**json.loads((root/'mandate.json').read_text()),'cost_per_abs_weight_change':cost,'risk_target_annual':target}
  state=policy.initialize({'assets':assets,'mandate':mandate})
  metrics=simulate(p,dates,first-begin,assets,mandate,lambda h,s:policy.decide(h,{**s,'user_state':state}))
  print(json.dumps({'public_year':year,'configuration':label,**metrics}),flush=True)
'''
  (public/'evaluate_dev.py').write_text(helper)
  extra='\n本地公开开发检查：python evaluate_dev.py submission/policy.py。会输出2012/2013年四个配置的真实指标；账本与正式评分相同，只使用公开数据。\n'
 else:
  source=ROOT/'game-task-r4/verifier'
  for name in ['adapter.lua','custom_ai.cfg']:shutil.copyfile(source/name,public/name)
  helper='''import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('policy');p.add_argument('--map');p.add_argument('--seat',type=int,default=1);p.add_argument('--seed',type=int,default=17);a=p.parse_args()
root=Path(__file__).parent;scene=Path(a.map) if a.map else sorted((root/'scenarios').glob('*.cfg'))[0]
with tempfile.TemporaryDirectory() as tmp:
 w=Path(tmp);addon=w/'userdata/data/add-ons/EdgeCandidate';addon.mkdir(parents=True)
 for src,name in [(Path(a.policy),'policy.lua'),(root/'adapter.lua','adapter.lua'),(root/'custom_ai.cfg','custom_ai.cfg'),(scene,'scenario.cfg')]:shutil.copyfile(src,addon/name)
 (addon/'_main.cfg').write_text('#ifdef MULTIPLAYER\\n{~add-ons/EdgeCandidate/scenario.cfg}\\n#endif\\n')
 import re
 scenario=re.search(r'(?m)^\\s*id=([^\\s]+)',scene.read_text()).group(1)
 engine='/opt/runtime/wesnoth'
 argv=[engine+'/bin/wesnoth','--data-dir',engine+'/share/wesnoth','--userdata-dir',str(w/'userdata'),'--userconfig-dir',str(w/'config'),'--usercache-dir',str(w/'cache'),'--nogui','--nosound','--multiplayer','--era','era_default','--scenario',scenario,'--side','1:Loyalists','--side','2:Rebels','--controller','1:ai','--controller','2:ai','--ai-config',str(a.seat)+':~add-ons/EdgeCandidate/custom_ai.cfg','--turns','45','--rng-seed',str(a.seed),'--log-info','ai/testing','--exit-at-end']
 env={**os.environ,'EDGE_GAME_RNG_SEED':str(a.seed),'LD_LIBRARY_PATH':'/opt/runtime/edge-game-libs','SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
 raise SystemExit(subprocess.run(argv,env=env,timeout=60).returncode)
'''
  (public/'play_public.py').write_text(helper)
  extra='\n本地真实公开对局：python play_public.py submission/policy.lua；可用 --map scenarios/某图.cfg --seat 2 --seed 17。自带真实引擎与公开Lua AI源码，默认一局双方为Loyalists/Rebels，不涉及隐藏地图。\n'
 (task/'instruction.md').write_text((task/'instruction.md').read_text()+extra)
 prep=json.loads((out/'preparation.json').read_text());prep['public_development_helpers_installed']=True;(out/'preparation.json').write_text(json.dumps(prep,indent=2)+'\n')
 print('public helpers ready',kind,flush=True)
