"""Unprivileged SDK exerciser. No scores, reference implementation or expected answers."""
import asyncio
import importlib
import inspect
import io
import json
import sys
import typing
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
config = json.loads(sys.argv[2])
C = importlib.import_module('stream_sdk.client')
M = importlib.import_module('stream_sdk.models')
T = importlib.import_module('stream_sdk.types')
secured = importlib.import_module('stream_sdk.api.feed.secured')
anonymous = importlib.import_module('stream_sdk.api.feed.anonymous')
plain = importlib.import_module('stream_sdk.api.feed.plain')
optional = importlib.import_module('stream_sdk.api.feed.optional')
numbers = importlib.import_module('stream_sdk.api.feed.numbers')
mode = config['mode']
action = config['action']
result = {'events': [], 'values': [], 'requests': []}
events = result['events']


def value(v):
    return {'class': type(v).__name__, 'value': v.to_dict() if hasattr(v, 'to_dict') else v}


def chunks():
    if action == 'malformed':
        return [b'{"seq":1,"label":"ok"}\n', b'{broken}\n']
    if action == 'numbers':
        return [b'1\n\n2', b'\n3']
    # UTF-8 split in the middle of a codepoint; CRLF, blank line, final line without LF.
    return [b'{"seq":1,"label":"caf\xc3', b'\xa9","state":"ready"}\r\n', b' \r\n', b'{"seq":2,"label":"last"}']


class SyncBytes(httpx.SyncByteStream):
    def __iter__(self):
        for index, part in enumerate(chunks()):
            events.append(['read', index])
            yield part
    def close(self):
        events.append(['close'])


class AsyncBytes(httpx.AsyncByteStream):
    def __init__(self):
        self.waiting = asyncio.Event()
    async def __aiter__(self):
        for index, part in enumerate(chunks()):
            events.append(['read', index])
            yield part
            if action == 'cancel' and index == 1:
                self.waiting.set()
                await asyncio.Event().wait()
    async def aclose(self):
        # A suspension point makes cleanup under cancellation observable.
        await asyncio.sleep(0)
        events.append(['close'])


class InjectedAuth(httpx.Auth):
    def auth_flow(self, request):
        request.headers['Authorization'] = 'Injected hidden'
        yield request


def observe(request):
    data = request.read()
    result['requests'].append({'method':request.method, 'path':request.url.path, 'headers':dict(request.headers), 'body':data.decode('utf-8', errors='replace')})
    if request.url.path == '/plain':
        return httpx.Response(200, json={'seq':9,'label':'plain'})
    status = 409 if action == 'status' else (201 if action == 'numbers' else 200)
    media = 'text/plain' if action == 'media' else 'Application/X-NDJSON; charset=utf-8'
    return httpx.Response(status, headers={'content-type':media}, stream=active_stream)


def endpoint_args():
    if action in ('json_body','anonymous'):
        return anonymous, {'body':M.Filter(query='find café')}
    if action == 'multipart_body':
        return anonymous, {'body':M.Upload(label='upload', files=[T.File(payload=io.BytesIO(b'alpha'),file_name='a.txt',mime_type='text/plain'),T.File(payload=io.BytesIO(b'beta'),file_name='b.txt',mime_type='text/plain')])}
    if action == 'optional':
        return optional, {}
    if action == 'numbers':
        return numbers, {}
    return secured, {}


def inspect_types(module):
    fn = getattr(module, 'asyncio_stream' if mode=='async' else 'stream')
    wrapped = inspect.unwrap(fn)
    hints = typing.get_type_hints(wrapped)
    result['annotation'] = str(hints.get('return'))
    result['client_annotation'] = str(hints.get('client'))
    result['body_required'] = 'body' not in inspect.signature(fn).parameters or inspect.signature(fn).parameters['body'].default is inspect.Parameter.empty


def sync_main():
    global active_stream
    active_stream = SyncBytes()
    transport = None if config.get('real_http') else httpx.MockTransport(observe)
    underlying = httpx.Client(base_url=config.get('base_url','http://fixture.test'), transport=transport,
        headers={'Authorization':'Bearer token','X-Session':'stable'}, auth=InjectedAuth() if action=='anonymous' else None, timeout=3)
    if config.get('lazy'):
        underlying.close()
        client = C.AuthenticatedClient(base_url=config.get('base_url','http://fixture.test'), token='token', headers={'X-Session':'stable'}, httpx_args={'transport':httpx.MockTransport(observe)})
        underlying = client.get_httpx_client()
    else:
        client = C.AuthenticatedClient(base_url=str(underlying.base_url),token='token', auth_header_name=config.get('auth_header_name','Authorization')).set_httpx_client(underlying)
    if config.get('auth_header_name'):underlying.headers[config['auth_header_name']]='custom-secret'
    module, kwargs = endpoint_args()
    inspect_types(module)
    result['before'] = len(result['requests'])
    context = module.stream(client=client, **kwargs)
    result['after_construct'] = len(result['requests'])
    try:
        with context as records:
            result['at_enter'] = list(events)
            if action != 'empty':
                for item in records:
                    result['values'].append(value(item))
                    result.setdefault('after_first', list(events))
                    if action in ('network','network_early'):
                        print('FIRST',flush=True)
                    if action in ('early','consumer','network_early'):
                        if action == 'consumer': raise LookupError('consumer')
                        break
    except Exception as exc:
        result['error'] = type(exc).__name__
        if hasattr(exc,'status_code'):result['status_code'] = exc.status_code
        if hasattr(exc,'content'):result['error_content'] = exc.content.decode(errors='replace')
    result['after_exit'] = list(events)
    result['client_closed'] = underlying.is_closed
    result['default_headers'] = dict(underlying.headers)
    ordinary = plain.sync(client=client)
    result['ordinary'] = value(ordinary)
    underlying.close()


async def async_main():
    global active_stream
    active_stream = AsyncBytes()
    transport = None if config.get('real_http') else httpx.MockTransport(observe)
    underlying = httpx.AsyncClient(base_url=config.get('base_url','http://fixture.test'), transport=transport,
        headers={'Authorization':'Bearer token','X-Session':'stable'}, auth=InjectedAuth() if action=='anonymous' else None, timeout=3)
    if config.get('lazy'):
        await underlying.aclose()
        client = C.AuthenticatedClient(base_url=config.get('base_url','http://fixture.test'), token='token', headers={'X-Session':'stable'}, httpx_args={'transport':httpx.MockTransport(observe)})
        underlying = client.get_async_httpx_client()
    else:
        client = C.AuthenticatedClient(base_url=str(underlying.base_url),token='token', auth_header_name=config.get('auth_header_name','Authorization')).set_async_httpx_client(underlying)
    if config.get('auth_header_name'):underlying.headers[config['auth_header_name']]='custom-secret'
    module, kwargs = endpoint_args()
    inspect_types(module)
    result['before'] = len(result['requests'])
    context = module.asyncio_stream(client=client, **kwargs)
    result['after_construct'] = len(result['requests'])
    async def consume():
        async with context as records:
            result['at_enter'] = list(events)
            if action != 'empty':
                async for item in records:
                    result['values'].append(value(item))
                    result.setdefault('after_first', list(events))
                    if action in ('network','network_early'):print('FIRST',flush=True)
                    if action in ('early','consumer','network_early'):
                        if action=='consumer':raise LookupError('consumer')
                        break
    try:
        if action == 'cancel':
            task = asyncio.create_task(consume())
            await active_stream.waiting.wait()
            task.cancel()
            try: await task
            except asyncio.CancelledError:result['error']='CancelledError'
        else:await consume()
    except Exception as exc:
        result['error'] = type(exc).__name__
        if hasattr(exc,'status_code'):result['status_code']=exc.status_code
        if hasattr(exc,'content'):result['error_content']=exc.content.decode(errors='replace')
    result['after_exit'] = list(events)
    result['client_closed'] = underlying.is_closed
    result['default_headers'] = dict(underlying.headers)
    result['ordinary'] = value(await plain.asyncio(client=client))
    await underlying.aclose()


try:
    if mode=='async':asyncio.run(async_main())
    else:sync_main()
except BaseException as exc:
    result['fatal'] = type(exc).__name__+': '+str(exc)
print('RESULT '+json.dumps(result, ensure_ascii=False),flush=True)
