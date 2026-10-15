#!/usr/bin/env python3
import sys,json
for line in sys.stdin:
    request=json.loads(line)
    print(json.dumps({'error':'invalid'}))
