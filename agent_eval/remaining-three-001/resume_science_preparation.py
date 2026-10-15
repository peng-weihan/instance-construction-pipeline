"""Resume unfinished preparation only; no learner has started."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tarfile
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');OUT=ROOT/'science-pilot';OLD=ROOT/'game-pilot';F=OUT/'framework';SOURCE=ROOT/'singlecell_cross_site_graph_lab-r2'
sys.path[:0]=[str(F),str(F/'sdk')]
from harbor.models.task.config import TaskConfig,EnvironmentConfig,AgentConfig,VerifierConfig
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
image=subprocess.check_output(['docker','image','inspect','edge-raymone-science:pilot-001','--format','{{.Id}}'],text=True).strip()
task=OUT/'task';context=task/'environment';assets=OUT/'public-runtime';runtime=assets/'opt/runtime'
old=OUT/'portable-runtime-check.json'
if old.exists():old.rename(OUT/'portable-runtime-check-failed-001.json')
source=(ROOT/'prepare_singlecell_remote.py').read_text()
assert 'NUMBA_CACHE_DIR' in source
start=source.index("wrapper='''")
exec(compile(source[start:],str(ROOT/'prepare_singlecell_remote.py'),'exec'))
