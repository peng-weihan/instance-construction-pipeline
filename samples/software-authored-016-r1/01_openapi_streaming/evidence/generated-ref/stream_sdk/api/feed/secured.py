from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx
import json
import anyio
from contextlib import contextmanager, asynccontextmanager
from collections.abc import Iterator, AsyncIterator

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET, Unset
from ... import errors

from ...models.event import Event
from typing import cast



def _get_kwargs(
    
) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/secured",
    }


    return _kwargs



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
    client: AuthenticatedClient,

) -> Iterator[Iterator[Event]]:
    """Open one response. The supplied client stays owned by the caller."""
    kwargs = _get_kwargs()
    transport = client.get_httpx_client()
    request = transport.build_request(**kwargs)
    response = transport.send(request, stream=True)
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
    client: AuthenticatedClient,

) -> AsyncIterator[AsyncIterator[Event]]:
    """Open one async response and close it even on cancellation."""
    kwargs = _get_kwargs()
    transport = client.get_async_httpx_client()
    request = transport.build_request(**kwargs)
    response = await transport.send(request, stream=True)
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
