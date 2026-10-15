from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx
import json
import anyio
from contextlib import contextmanager, asynccontextmanager
from collections.abc import Iterator, AsyncIterator

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.event import Event
from ...models.filter_ import Filter
from ...models.upload import Upload
from typing import cast



def _get_kwargs(
    *,
    body:    Filter  |     Upload  | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/anonymous",
    }

    if isinstance(body, Filter):
        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"
    if isinstance(body, Upload):
        _kwargs["files"] = body.to_multipart()

        headers["Content-Type"] = "multipart/form-data; boundary=+++"

    _kwargs["headers"] = headers
    return _kwargs

def _anonymous_request(transport: httpx.Client | httpx.AsyncClient, client: AuthenticatedClient | Client, kwargs: dict[str, Any]) -> httpx.Request:
    request = transport.build_request(**kwargs)
    # Remove merged defaults from this request alone; injected httpx clients remain shared.
    request.headers.pop(getattr(client, "auth_header_name", "Authorization"), None)
    request.headers.pop("Authorization", None)
    return request


def _parse_record(line: str) -> Event:
    response_200 = Event.from_dict(json.loads(line))



    return response_200



def _validate_stream(response: httpx.Response) -> None:
    if response.status_code != 200:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/x-ndjson":
        raise ValueError("Expected application/x-ndjson")
    # NDJSON uses UTF-8 regardless of optional charset parameters.
    response.encoding = "utf-8"


@contextmanager
def stream(
    *,
    client: AuthenticatedClient | Client,
    body:    Filter  |     Upload  | Unset = UNSET,

) -> Iterator[Iterator[Event]]:
    """Open one response. The supplied client stays owned by the caller."""
    kwargs = _get_kwargs(body=body,
)
    transport = client.get_httpx_client()
    request = _anonymous_request(transport, client, kwargs)
    response = transport.send(request, stream=True, auth=None)
    try:
        if response.status_code != 200:
            response.read()
        _validate_stream(response)
        def records() -> Iterator[Event]:
            for line in response.iter_lines():
                if line.strip():
                    yield _parse_record(line)
        yield records()
    finally:
        response.close()


@asynccontextmanager
async def asyncio_stream(
    *,
    client: AuthenticatedClient | Client,
    body:    Filter  |     Upload  | Unset = UNSET,

) -> AsyncIterator[AsyncIterator[Event]]:
    """Open one async response and close it even on cancellation."""
    kwargs = _get_kwargs(body=body,
)
    transport = client.get_async_httpx_client()
    request = _anonymous_request(transport, client, kwargs)
    response = await transport.send(request, stream=True, auth=None)
    try:
        if response.status_code != 200:
            await response.aread()
        _validate_stream(response)
        async def records() -> AsyncIterator[Event]:
            async for line in response.aiter_lines():
                if line.strip():
                    yield _parse_record(line)
        yield records()
    finally:
        with anyio.CancelScope(shield=True):
            await response.aclose()
