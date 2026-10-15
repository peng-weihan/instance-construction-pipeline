import sys,tempfile
sys.path.insert(0,'/judge/verifier')
from runtime import run
code="import os,hashlib,json;print(json.dumps({'seed':os.getenv('EDGE_GAME_RNG_SEED'),'binary_sha256':hashlib.sha256(open('/opt/runtime/wesnoth/bin/wesnoth','rb').read()).hexdigest()}))"
with tempfile.TemporaryDirectory() as work:print(run(work,['/opt/runtime/venv/bin/python','-c',code],seed=17))
