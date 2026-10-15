"""Freeze the dev-selected reference and make the baseline constants inspectable."""
from pathlib import Path
import ast,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'samples/remaining-three-built-001/finance-task-r1'
DST=SRC.with_name('finance-task-r2');shutil.copytree(SRC,DST,dirs_exist_ok=True)
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
# Keep the measured baseline byte-for-byte. Every numeric literal in its source
# has a machine-readable location and value, in addition to semantic descriptions.
source=(SRC/'public/baseline_policy.py').read_text()
literals=[{'line':n.lineno,'column':n.col_offset,'value':n.value}
          for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Constant)
          and isinstance(n.value,(int,float)) and not isinstance(n.value,bool)]
contract={'implementation_sha256':hashlib.sha256(source.encode()).hexdigest(),
 'lookback_returns':126,'covariance_shrinkage':[.8,.2],'covariance_ridge':1e-9,
 'annual_days':252,'drift_clip':[-.15,.20],'drift_shrinkage':.25,
 'risk_safety_factor':.95,'risk_aversion':5,'turnover_weight':.002,
 'extra_trade_l1_threshold':.20,'numeric_source_literals':literals,
 'reference_selection':'best valid variant on 2012-2013 public development episodes only'}
dump(DST/'public/baseline_contract.json',contract)
shutil.copyfile(ROOT/'runs/remaining-three-001/finance-probe-001/slow.py',DST/'solution/policy.py')
runtime=(SRC/'verifier/runtime.py').read_text().replace("'--unshare-all','--die-with-parent'","'--unshare-all','--share-net','--uid','2000','--gid','2000','--die-with-parent'")
(DST/'verifier/runtime.py').write_text(runtime)
for name in ['scoring_metadata.json','score_design.json']:
 p=DST/'public'/name;d=json.loads(p.read_text());d.setdefault('baseline',{})['implementation']='public/baseline_policy.py, frozen verifier copy; baseline_contract.json'
 d['comparison_baseline_contract']='baseline_contract.json'
 d['reference_selection']={'variant':'slow','public_dev_score':.4828499974,'selection_uses_private_data':False}
 dump(p,d)
for side in ['agent','verifier']:
 ctx=DST/'environment'/side;shutil.rmtree(ctx/'public');shutil.copytree(DST/'public',ctx/'public')
 if side=='verifier':shutil.rmtree(ctx/'verifier');shutil.copytree(DST/'verifier',ctx/'verifier')
d=json.loads((DST/'REVISION.json').read_text());d.update(previous_revision='finance-task-r1',
 reference_selection='slow variant selected on public dev',baseline_bytes_unchanged=True,
 runtime_verified=False,user_data_preference='retain real history for local validation')
dump(DST/'REVISION.json',d);print(DST)
