# Mandatory cheap baseline: existing JSON parser alias plus typed httpx line wrappers.
from pathlib import Path
root=Path(__file__).resolve().parents[1]
dest=root/'controls/cheap/openapi_python_client'
p=dest/'parser/responses.py';s=p.read_text().replace('"application/json": JSON_SOURCE,','"application/json": JSON_SOURCE,\n        "application/x-ndjson": JSON_SOURCE,');p.write_text(s)
p=dest/'templates/endpoint_module.py.jinja';s=p.read_text().replace('import httpx','import httpx\nimport json\nfrom contextlib import contextmanager, asynccontextmanager\nfrom collections.abc import Iterator, AsyncIterator',1)
s+='''
@contextmanager
def stream({{ arguments(endpoint) }}) -> Iterator[Iterator[{{ return_string | as_unembedded_code }}]]:
    kwargs = _get_kwargs({{ kwargs(endpoint, include_client=False) }})
    with client.get_httpx_client().stream(**kwargs) as response:
        def records():
            for line in response.iter_lines():
                if line.strip():
                    yield _parse_response(client=client, response=httpx.Response(response.status_code, json=json.loads(line)))
        yield records()

@asynccontextmanager
async def asyncio_stream({{ arguments(endpoint) }}) -> AsyncIterator[AsyncIterator[{{ return_string | as_unembedded_code }}]]:
    kwargs = _get_kwargs({{ kwargs(endpoint, include_client=False) }})
    async with client.get_async_httpx_client().stream(**kwargs) as response:
        async def records():
            async for line in response.aiter_lines():
                if line.strip():
                    yield _parse_response(client=client, response=httpx.Response(response.status_code, json=json.loads(line)))
        yield records()
''';p.write_text(s)
