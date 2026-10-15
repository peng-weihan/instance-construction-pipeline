"""Incremental compile in RAM; no new image or host source/build tree."""
from pathlib import Path
import hashlib,json,subprocess,uuid
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');out=ROOT/'game-entropy-build-004';out.mkdir()
image='edge-raymone-game:initial';export=subprocess.check_output(['docker','create',image],text=True).strip()
name='edge-raymone-entropy-'+uuid.uuid4().hex[:10]
cmd=['docker','run','-d','--name',name,'--network','none','--read-only','--memory','12g','--cpus','2','--cpuset-cpus','4,5',
 '--tmpfs','/tmp:rw,exec,size=2g','--tmpfs','/opt/runtime/wesnoth-source:rw,exec,size=3g',
 '--tmpfs','/opt/runtime/wesnoth-build:rw,exec,size=2g','--mount',f'type=bind,source={ROOT}/patch_game_entropy.py,target=/tmp/patch.py,readonly',
 '--entrypoint','sleep',image,'3600']
try:
 subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
 for folder in ['wesnoth-source','wesnoth-build']:
  copy=subprocess.Popen(['docker','cp',export+':/opt/runtime/'+folder,'-'],stdout=subprocess.PIPE)
  unpack=subprocess.run(['docker','exec','-i',name,'tar','-xf','-','-C','/opt/runtime'],stdin=copy.stdout)
  copy.stdout.close();rc=copy.wait();assert rc==0 and unpack.returncode==0
 subprocess.run(['docker','exec',name,'python3','/tmp/patch.py'],check=True)
 with (out/'build.log').open('wb') as log:
  subprocess.run(['docker','exec',name,'cmake','--build','/opt/runtime/wesnoth-build','-j','2'],stdout=log,stderr=subprocess.STDOUT,check=True)
 # Docker archive/cp can resolve the image backing tree rather than our live
 # tmpfs build. Read the actual running namespace and assert its binary hash.
 compiled_sha=subprocess.check_output(['docker','exec',name,'sha256sum','/opt/runtime/wesnoth-build/wesnoth'],text=True).split()[0]
 with (out/'wesnoth').open('wb') as target:
  subprocess.run(['docker','exec',name,'cat','/opt/runtime/wesnoth-build/wesnoth'],stdout=target,check=True)
 (out/'wesnoth').chmod(0o755)
 assert hashlib.sha256((out/'wesnoth').read_bytes()).hexdigest()==compiled_sha
 record={'base_image':image,'source_commit':'8ba2b3ebd33f6850c2dc4fe7c6478c7e4f9fc3fd',
  'patched_binary_sha256':compiled_sha,'export_matches_running_build':True,'compile_exit':0,
  'storage':'source and object files in container RAM only; exported binary retained',
  'patch':'honor trusted EDGE_GAME_RNG_SEED in default generator, seed_rng, Lua math and hash seeding'}
 (out/'report.json').write_text(json.dumps(record,indent=2)+'\n');print(record,flush=True)
finally:
 subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['docker','rm',export],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
