from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET, Unset
from ... import errors

from ...models.event import Event
from typing import cast



def _get_kwargs(
    
) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/plain",
    }


    return _kwargs

def _anonymous_request(transport: httpx.Client | httpx.AsyncClient, client: AuthenticatedClient | Client, kwargs: dict[str, Any]) -> httpx.Request:
    request = transport.build_request(**kwargs)
    # Remove merged defaults from this request alone; injected httpx clients remain shared.
    request.headers.pop(getattr(client, "auth_header_name", "Authorization"), None)
    request.headers.pop("Authorization", None)
    return request



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Event | None:
    if response.status_code == 200:
        response_200 = Event.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Event]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,

) -> Response[Event]:
    """ 
    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Event]
     """


    kwargs = _get_kwargs(
        
    )

    transport = client.get_httpx_client()
    response = transport.send(_anonymous_request(transport, client, kwargs), auth=None)

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,

) -> Event | None:
    """ 
    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Event
     """


    return sync_detailed(
        client=client,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,

) -> Response[Event]:
    """ 
    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Event]
     """


    kwargs = _get_kwargs(
        
    )

    transport = client.get_async_httpx_client()
    response = await transport.send(_anonymous_request(transport, client, kwargs), auth=None)

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,

) -> Event | None:
    """ 
    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Event
     """


    return (await asyncio_detailed(
        client=client,

    )).parsed

