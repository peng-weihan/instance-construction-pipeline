#!/usr/bin/env python3
import os,pathlib,sys
os.execv(str(pathlib.Path(__file__).resolve().with_name('jq')),['jq',*sys.argv[1:]])
