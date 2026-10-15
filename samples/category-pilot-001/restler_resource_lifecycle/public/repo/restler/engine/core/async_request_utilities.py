# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import time
import json

import engine.core.request_utilities as request_utilities
from restler_settings import Settings

def get_polling_request(response):
    """ Helper that exctracts the URL from an azure-async-operation response
    and then creates and returns a valid GET request for it.

    @param response: The response to parse for the URL
    @type  response: Str

    @return: Tuple containing the rendered data for the GET request
             and a boolean that indicates whether or not to expect
             the parsable data to be included in the polling request.
    @rtype : Tuple(str, bool)

    """
    raise NotImplementedError("Restore lifecycle behavior: get_polling_request")

def make_GET_request(request_data):
    """ Helper that converts a request's rendered data to a GET
    with a matching endpoint. This function replaces @request_data's
    method with GET and removes a body, if present, before returning
    the new request data.

    @param request_data: The request to convert to a GET. This is fully
                         rendered request data in a format that is ready
                         to be sent to HttpSock's sendRecv function.
    @type  request_data: Str

    @return: The new GET request
    @rtype : Str

    """
    raise NotImplementedError("Restore lifecycle behavior: make_GET_request")

def try_parse_GET_request(request_data):
    """ Helper that creates a GET request from a request's rendered
    data, sends that request, and then checks for a success (200) status.

    @param request_data: The request to convert to a GET. This is fully
                         rendered request data in a format that is ready
                         to be sent to HttpSock's sendRecv function.
    @type  request_data: Str

    @return: The response of the GET request if it's a 200, otherwise None
    @rtype : Str

    """
    raise NotImplementedError("Restore lifecycle behavior: try_parse_GET_request")

def try_async_poll(request_data, response, max_async_wait_time, poll_delete_status=False):
    """ Helper that will poll the server until a certain resource
    becomes available.

    This function will check the response from a PUT or POST request to
    see if it contains one of the known async resource creations strings and,
    if so, will poll the URL specified in the response until the resource is
    said to be available or a max timeout has been reached.

    @param request_data: The request that was sent's data string
    @type  request_data: Str
    @param response: The response returned after @request was sent
    @type  response: Str
    @param max_async_wait_time: The maximum amount of time we will wait (in
                                seconds) for the resource to become available
    @type  max_async_wait_time: Int
    @param poll_delete_status: A boolean that indicates whether or not to poll the status of a DELETE request.
    @type  poll_delete_status: Bool
    
    @return: A tuple containing:
             - The list of responses for parsing, which will either contain the @response
             passed to this function, or in the case of an async request, the
             response from the end of the async operation (if finished),
             and the response from the GET request.
             It is possible that the response of the async request when finished does not
             contain all of the expected fields in the schema of the async response, so as a
             workaround the GET response is also returned to try to obtain this additional information.
             - A boolean that is True if there was an error when creating the
             resource
             - A Boolean that tells the caller whether or not async polling was
             attempted
    @rtype : Tuple(HttpResponse, boolean, boolean)

    """
    raise NotImplementedError("Restore lifecycle behavior: try_async_poll")
