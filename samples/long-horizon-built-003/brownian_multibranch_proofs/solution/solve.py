import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
shutil.copytree(Path(__file__).parent/'reference',a.output,dirs_exist_ok=True)
