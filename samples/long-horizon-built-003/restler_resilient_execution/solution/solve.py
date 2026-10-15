import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--public',required=True);p.add_argument('--output',required=True);a=p.parse_args()
out=Path(a.output);shutil.copytree(Path(a.public)/'repo/restler',out,dirs_exist_ok=True)
shutil.copytree(Path(__file__).parent/'reference',out,dirs_exist_ok=True)
