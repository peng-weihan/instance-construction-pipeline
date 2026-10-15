"""Minimal stdio MCP bridge; executes nothing, forwards to an isolated host queue."""
import json
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / '.teacher_tools'
QUEUE.mkdir(exist_ok=True)


def respond(request, result):
    print(json.dumps({'jsonrpc':'2.0', 'id':request['id'], 'result':result}), flush=True)


for line in sys.stdin:
    request = json.loads(line)
    method = request.get('method')
    if 'id' not in request:
        continue
    if method == 'initialize':
        respond(request, {'protocolVersion': request['params']['protocolVersion'],
            'capabilities': {'tools': {}}, 'serverInfo': {'name':'edge-shell-queue', 'version':'1.0.0'}})
    elif method == 'ping':
        respond(request, {})
    elif method == 'tools/list':
        respond(request, {'tools':[{'name':'shell', 'description':
            'Run a shell command in the public task workspace via the isolated execution service. '
            'Use this for ALL reads, edits, builds, tests, and python3 feedback.py; native shell tools are unavailable.',
            'inputSchema': {'type':'object', 'properties': {'command': {'type':'string'},
                'timeout_seconds': {'type':'integer','minimum':1,'maximum':180}}, 'required':['command'],
                'additionalProperties':False}}]})
    elif method == 'tools/call':
        rid = uuid.uuid4().hex
        arguments = request.get('params',{}).get('arguments',{})
        temporary = QUEUE / (rid + '.tmp')
        temporary.write_text(json.dumps({'request_id':rid, 'arguments':arguments}))
        temporary.rename(QUEUE / (rid + '.request.json'))
        response_path = QUEUE / (rid + '.response.json')
        deadline = time.monotonic() + 200
        while not response_path.exists() and time.monotonic() < deadline:
            time.sleep(.1)
        value = json.loads(response_path.read_text()) if response_path.exists() else {'error':'execution service timeout'}
        respond(request, {'content':[{'type':'text','text':json.dumps(value)}], 'isError': bool(value.get('error'))})
    else:
        print(json.dumps({'jsonrpc':'2.0','id':request['id'], 'error':{'code':-32601,'message':'Method not found'}}), flush=True)
