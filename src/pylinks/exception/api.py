"""Custom exceptions raised by the package."""

from __future__ import annotations as _annotations

import json
from typing import TYPE_CHECKING as _TYPE_CHECKING

import mdit as _mdit
import json as _json
from pylinks.exception import PyLinksError

if _TYPE_CHECKING:
    from typing import Any, Callable
    from requests import PreparedRequest, Request, Response
    from requests.exceptions import RequestException


class WebAPIError(PyLinksError):
    """Base Exception class for all web API exceptions."""
    pass


class WebAPIRequestError(WebAPIError):
    def __init__(self, request_error: RequestException):
        self.request = request_error.request
        self.response = request_error.response
        details = []
        if self.request:
            details.append(_process_request(self.request))
        if self.response:
            summary, response_details = _process_response(self.response)
            details.append(response_details)

        super().__init__(
            title="Web API Request Error",
            intro=str(request_error),
            details=_mdit.block_container(*details) if details else None,
        )
        return


class WebAPIStatusCodeError(WebAPIError):
    """
    Base Exception class for web API status code related exceptions.
    By default, raised when status code is in range [400, 600).
    """

    def __init__(self, response: Response):
        self.request = response.request
        self.response = response
        response_summary, response_details = _process_response(response)
        details = _mdit.block_container(
            _process_request(self.request),
            response_details,
        )
        super().__init__(
            title="Web API Status Code Error",
            intro=response_summary,
            details=details,
        )
        return


class WebAPITemporaryStatusCodeError(WebAPIStatusCodeError):
    """
    Exception class for status code errors related to temporary issues.
    By default, raised when status code is in (408, 429, 500, 502, 503, 504).
    """
    pass


class WebAPIPersistentStatusCodeError(WebAPIStatusCodeError):
    """
    Exception class for status code errors related to persistent issues.
    By default, raised when status code is in range [400, 600),
    but not in (408, 429, 500, 502, 503, 504).
    """
    pass


class WebAPIValueError(WebAPIError):
    """
    Exception class for response value errors.
    """

    def __init__(self, response_value: Any, response_verifier: Callable[[Any], bool]):
        self.response_value = response_value
        self.response_verifier = response_verifier
        error_msg = (
            f"Response verifier function {response_verifier} failed to verify {response_value}."
        )
        super().__init__(
            title="Web API Response Verification Error",
            intro=error_msg,
        )
        return


class GraphQLResponseError(WebAPIError):
    """
    Exception class for GraphQL
    """

    def __init__(self, response: dict):
        if "errors" in response:
            intro = "GraphQL response contains errors."
        elif "data" not in response:
            intro = "GraphQL response does not contain data."
        super().__init__(
            title="GraphQL Response Error",
            intro=intro,
            details=_mdit.element.code_block(
                json.dumps(response, indent=3), language="json", caption="GraphQL Response"
            ),
        )
        return


def _process_response(response: Response):
    # Decode error reason from server
    # This part is adapted from `requests` library; See PR #3538 on their GitHub
    if isinstance(response.reason, bytes):
        try:
            reason = response.reason.decode("utf-8")
        except UnicodeDecodeError:
            reason = response.reason.decode("iso-8859-1")
    else:
        reason = response.reason

    response_info = []
    response_summary = _mdit.element.field_list()
    side = "Client" if response.status_code < 500 else "Server"
    for title, value in (
        ("Status Code", response.status_code),
        ("Side", side),
        ("Reason", reason),
        ("URL", response.url),
    ):
        if value:
            response_summary.append(
                title=title,
                body=_mdit.element.code_span(str(value)),
            )
    if response_summary.content.elements():
        response_info.append(response_summary)
    if response.text:
        response_info.append(
            _mdit.element.code_block(response.text, caption="Content")
        )
    summary = f"HTTP {response.status_code} error ({side.lower()} side) from {response.url}: {reason}"
    return summary, _mdit.element.dropdown(
        title="Response",
        body=response_info,
        icon="📥"
    )


def _process_request(request: Request | PreparedRequest):
    request_info = []
    request_summary = _mdit.element.field_list()
    for title, attr_name in (
        ("Method", "method"),
        ("URL", "url"),
    ):
        value = getattr(request, attr_name, None)
        if value:
            request_summary.append(
                title=title,
                body=_mdit.element.code_span(value),
            )
    if request_summary.content.elements():
        request_info.append(request_summary)
    for title, attr_name in (
        ("Data", "data"),
        ("JSON", "json"),
        ("Parameters", "params"),
        ("Body", "body"),
    ):
        value = getattr(request, attr_name, None)
        if value:
            request_info.append(
                _mdit.element.code_block(str(value), caption=title)
            )
    return _mdit.element.dropdown(
        title="Request",
        body=request_info,
        icon="📤"
    )
