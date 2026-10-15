"""Build submitted irregular sources against fixed, pre-fetched dependencies."""
import json,subprocess
from pathlib import Path
args=['cmake','-S','repo','-B','build','-DCMAKE_BUILD_TYPE=Release','-DPACKINGSOLVER_BUILD_TEST=OFF',
      '-DPACKINGSOLVER_USE_CLP=OFF','-DPACKINGSOLVER_USE_HIGHS=ON','-DFETCHCONTENT_FULLY_DISCONNECTED=ON']
for name,path in json.loads(Path('/opt/runtime/packing-dependencies.json').read_text()).items():
    args.append('-DFETCHCONTENT_SOURCE_DIR_'+name.upper()+'='+path)
subprocess.run(args,check=True)
subprocess.run(['cmake','--build','build','--target','PackingSolver_irregular_main','-j','2'],check=True)
