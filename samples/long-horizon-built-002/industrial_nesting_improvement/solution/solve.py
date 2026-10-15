"""Reference restores the real frozen solver; its quality is not assumed optimal."""
import argparse,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--public',required=True);p.add_argument('--output',required=True);a=p.parse_args()
for rel in ['src/irregular','include/packingsolver/irregular']:
    shutil.copytree(Path(a.public)/'repo'/rel,Path(a.output)/rel,dirs_exist_ok=True)
