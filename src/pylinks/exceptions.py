"""Custom exceptions raised by the package."""


from typing import Any, Callable
import requests


class WebAPIError(IOError):
    """Base Exception class for all web API exceptions."""
    pass


class WebAPIStatusCodeError(WebAPIError):
    """
    Base Exception class for web API status code related exceptions.
    By default, raised when status code is in range [400, 600).
    """

    def __init__(self, response: requests.Response):
        self.response: requests.Response = response
        # Decode error reason from server
        # This part is adapted from `requests` library; See PR #3538 on their GitHub
        if isinstance(response.reason, bytes):
            try:
                self.reason = response.reason.decode("utf-8")
            except UnicodeDecodeError:
                self.reason = response.reason.decode("iso-8859-1")
        else:
            self.reason = response.reason
        self.response_msg = response.text
        self.side = "client" if response.status_code < 500 else "server"
        self.status_code = response.status_code
        self.url = response.url

        error_msg = (
            f"HTTP {self.side} error (status code: {self.status_code})\n"
            f"- From: {self.url}\n"
            f"- Reason: {self.reason}\n"
            f"- Response: {self.response_msg}"
        )
        super().__init__(error_msg)
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
        super().__init__(error_msg)
        return
