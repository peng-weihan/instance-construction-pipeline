from pathlib import Path
import shutil, subprocess, json
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'material-src/openapi-python-client'
PUB=ROOT/'task/environment'
START=PUB/'submission'
REF=ROOT/'task/solution/reference'
for dest in (START,REF):
    if not dest.exists():
        subprocess.run(['git','-C',str(SRC),'archive','--format=tar','HEAD'],stdout=(ROOT/'downloads/source.tar').open('wb'),check=True)
        dest.mkdir(parents=True)
        subprocess.run(['tar','xf',str(ROOT/'downloads/source.tar'),'-C',str(dest)],check=True)
p=REF/'openapi_python_client/parser/responses.py'
s=p.read_text().replace('JSON_SOURCE =', 'NDJSON_SOURCE = _ResponseSource(attribute="json.loads(line)", return_type="Any")\nJSON_SOURCE =',1)
s=s.replace('"application/json": JSON_SOURCE,','"application/json": JSON_SOURCE,\n        "application/x-ndjson": NDJSON_SOURCE,')
p.write_text(s)
p=REF/'openapi_python_client/parser/openapi.py';s=p.read_text()
s=s.replace('from .responses import HTTPStatusPattern, Responses, response_from_data','from .responses import HTTPStatusPattern, Responses, NDJSON_SOURCE, response_from_data')
s=s.replace('    @staticmethod\n    def _add_responses(','''    # Explicit security: [] disables auth, whereas omitted security inherits the document.
    anonymous: bool = False

    @property
    def stream_response(self):
        for response in self.responses:
            if response.source == NDJSON_SOURCE and response.status_code.range is not None and 200 <= response.status_code.range[0] < 300:
                return response
        return None

    @staticmethod
    def _add_responses(''',1)
s=s.replace('            requires_security=bool(data.security),','            requires_security=bool(data.security) and {} not in data.security,\n            anonymous=data.security == [],')
s=s.replace('        endpoint_collections_by_tag, schemas, parameters = EndpointCollection.from_data(','''        # Resolve inheritance once before the normal parser pipeline. Do not overwrite [] or [{}].
        for path_item in openapi.paths.values():
            for method in ("get", "put", "post", "delete", "options", "head", "patch", "trace"):
                operation = getattr(path_item, method)
                if operation is not None and operation.security is None:
                    operation.security = openapi.security
        endpoint_collections_by_tag, schemas, parameters = EndpointCollection.from_data(''')
p.write_text(s)
p=REF/'openapi_python_client/templates/endpoint_module.py.jinja';s=p.read_text()
s=s.replace('import httpx','import httpx\n{% if endpoint.stream_response %}\nimport json\nimport anyio\nfrom contextlib import contextmanager, asynccontextmanager\nfrom collections.abc import Iterator, AsyncIterator\n{% endif %}',1)
pos=s.index('{% if endpoint.responses.default %}')
s=s[:pos]+'''{% if endpoint.anonymous %}
def _anonymous_request(transport: httpx.Client | httpx.AsyncClient, client: AuthenticatedClient | Client, kwargs: dict[str, Any]) -> httpx.Request:
    request = transport.build_request(**kwargs)
    # Remove merged defaults from this request alone; injected httpx clients remain shared.
    request.headers.pop(getattr(client, "auth_header_name", "Authorization"), None)
    request.headers.pop("Authorization", None)
    return request
{% endif %}

{% if endpoint.stream_response %}
{% include "streaming_endpoint.py.jinja" %}
{% else %}
'''+s[pos:]+ '\n{% endif %}\n'
s=s.replace('''    response = client.get_httpx_client().request(
        **kwargs,
    )''','''    {% if endpoint.anonymous %}
    transport = client.get_httpx_client()
    response = transport.send(_anonymous_request(transport, client, kwargs), auth=None)
    {% else %}
    response = client.get_httpx_client().request(**kwargs)
    {% endif %}''')
s=s.replace('''    response = await client.get_async_httpx_client().request(
        **kwargs
    )''','''    {% if endpoint.anonymous %}
    transport = client.get_async_httpx_client()
    response = await transport.send(_anonymous_request(transport, client, kwargs), auth=None)
    {% else %}
    response = await client.get_async_httpx_client().request(**kwargs)
    {% endif %}''')
p.write_text(s)
(REF/'openapi_python_client/templates/streaming_endpoint.py.jinja').write_text('''{% set record = endpoint.stream_response %}
{% set record_type = record.prop.get_type_string() | as_unembedded_code %}

def _parse_record(line: str) -> {{ record_type }}:
    {{ parse_response(true, record) | indent(4) }}


def _validate_stream(response: httpx.Response) -> None:
    if response.status_code != {{ record.status_code.range[0] }}:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/x-ndjson":
        raise ValueError("Expected application/x-ndjson")
    # NDJSON uses UTF-8 regardless of optional charset parameters.
    response.encoding = "utf-8"


@contextmanager
def stream(
    {{ arguments(endpoint) | indent(4) }}
) -> Iterator[Iterator[{{ record_type }}]]:
    """Open one response. The supplied client stays owned by the caller."""
    kwargs = _get_kwargs({{ kwargs(endpoint, include_client=False) }})
    transport = client.get_httpx_client()
    {% if endpoint.anonymous %}
    request = _anonymous_request(transport, client, kwargs)
    response = transport.send(request, stream=True, auth=None)
    {% else %}
    request = transport.build_request(**kwargs)
    response = transport.send(request, stream=True)
    {% endif %}
    try:
        if response.status_code != {{ record.status_code.range[0] }}:
            response.read()
        _validate_stream(response)
        def records() -> Iterator[{{ record_type }}]:
            for line in response.iter_lines():
                if line.strip():
                    yield _parse_record(line)
        yield records()
    finally:
        response.close()


@asynccontextmanager
async def asyncio_stream(
    {{ arguments(endpoint) | indent(4) }}
) -> AsyncIterator[AsyncIterator[{{ record_type }}]]:
    """Open one async response and close it even on cancellation."""
    kwargs = _get_kwargs({{ kwargs(endpoint, include_client=False) }})
    transport = client.get_async_httpx_client()
    {% if endpoint.anonymous %}
    request = _anonymous_request(transport, client, kwargs)
    response = await transport.send(request, stream=True, auth=None)
    {% else %}
    request = transport.build_request(**kwargs)
    response = await transport.send(request, stream=True)
    {% endif %}
    try:
        if response.status_code != {{ record.status_code.range[0] }}:
            await response.aread()
        _validate_stream(response)
        async def records() -> AsyncIterator[{{ record_type }}]:
            async for line in response.aiter_lines():
                if line.strip():
                    yield _parse_record(line)
        yield records()
    finally:
        with anyio.CancelScope(shield=True):
            await response.aclose()
''')
print('source and reference constructed')
