"""
Handling HTTP requests and responses.
"""
from __future__ import annotations as _annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING, NamedTuple as _NamedTuple

import time
from functools import wraps
from pathlib import Path

import mdit as _mdit
import requests

from pylinks.exception import api as _exception

if _TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        List,
        Literal,
        NoReturn,
        Optional,
        Sequence,
        Tuple,
        Union,
        Type,
    )
    from pylinks.url import URL



class RetryConfig(_NamedTuple):
    """
    Configuration for the `retry_on_exception` decorator.

    Attributes
    ----------
    num_tries : int, default: 3
        Maximum number of times the decorated function will be called
        before an exception is reraised.
    sleep_time_init : float, default: 1
        Amount of time (in seconds) to wait before two function calls.
    sleep_time_scale : float, default: 3
        Scaling factor for `sleep_time_init`.
        This can be used to scale down/up the waiting time between function calls.
        After the n-th function call, the waiting time will be equal to:
        `sleep_time_init` * `sleep_time_scale` ^ (n - 1).
    """

    num_tries: int = 3
    sleep_time_init: float = 1
    sleep_time_scale: float = 3


class HTTPRequestRetryConfig(_NamedTuple):
    """
    Configurations for retrying an HTTP request
    sent by `opencadd.webapi.http_request.response_http_request`.

    Attributes
    ----------
    status_codes_to_retry: Sequence[int], optional, default: (408, 429, 500, 502, 503, 504)
        Set of HTTP status codes of response that will trigger a retry.
        If set to `None`, all error status codes will immediately raise an
        `opencadd.webapi.http_request.WebAPIPersistentError`.
    retry_config_status: RetryConfig, optional, default: RetryConfig(5, 1, 2)
        Configurations for retrying when the status code of response is in `status_codes_to_retry`.
        If set to `None`, all error status codes will immediately raise an
        `opencadd.webapi.http_request.WebAPIPersistentError`.
    retry_config_response: RetryConfig, optional, default: RetryConfig(5, 1, 2)
        Configurations for retrying when `response_verifier` returns `False`.
        If set to `None`, all response errors will immediately raise an
        `opencadd.webapi.http_request.WebAPIValueError`.
    """

    status_codes_to_retry: Optional[Sequence[int]] = (408, 429, 500, 502, 503, 504)
    config_status: RetryConfig = RetryConfig(5, 1, 2)
    config_response: RetryConfig = RetryConfig(5, 1, 2)


def request(
    url: str | URL,
    verb: Union[str, Literal["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"]] = "GET",
    params: Optional[Union[dict, List[tuple], bytes]] = None,
    data: Optional[Union[dict, List[tuple], bytes]] = None,
    headers=None,
    cookies=None,
    files=None,
    auth=None,
    timeout: Optional[Union[float, Tuple[float, float]]] = (10, 20),
    allow_redirects=True,
    proxies=None,
    hooks=None,
    stream=None,
    verify=None,
    cert=None,
    json=None,
    response_type: Optional[Literal["str", "json", "bytes"]] = None,
    encoding: Optional[str] = None,
    response_verifier: Optional[Callable[[Any], bool]] = None,
    retry_config: Optional[HTTPRequestRetryConfig] = HTTPRequestRetryConfig(),
    ignored_status_codes: Optional[Sequence[int]] = None,
    json_kwargs: dict = None,
) -> Union[requests.Response, str, dict, list, bool, int, bytes]:
    """
    Send an HTTP request and get the response in specified type.

    Parameters
    ----------
    url : str
        URL of the API request.
    verb : Literal['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE'], optional, default: 'GET'
        HTTP verb of the API request. Besides the standard verbs, custom verbs are also accepted.
    params : dict | list[tuple] | bytes, optional, default: None
        Additional parameters to send in the query string of the request.
    data : dict | list[tuple] | bytes, optional, default: None
    response_verifier: Callable[[Any], bool], optional, default: None
        A single-parameter function that when called on the response value of the HTTP request,
        returns a boolean describing whether the response value is accepted (`True`),
        or the request must be retried (`False`). The type of response value is defined by user in
        argument `response_type` of `opencadd.webapi.http_request.response_http_request`.
    headers
    cookies
    files
    auth
    timeout
    allow_redirects
    proxies
    hooks
    stream
    verify
    cert
    json
    response_type
    encoding
    json_kwargs : dict
        Optional arguments for `json.loads`, when `response_type` is set to `"json"`.

    Returns
    -------

    Raises
    ------
    requests.exceptions.RequestException
        In case of an unsuccessful request.
    ValueError
        If some arguments are not recognized.

    References
    ----------
    * Documentation of the `requests.request` function:
        https://requests.readthedocs.io/en/latest/api/#requests.request
    * Documentation of JSON decoding keyword arguments:
        https://docs.python.org/3/library/json.html#json.loads
    """

    def get_response_value():
        def get_response():
            try:
                response = requests.request(
                    method=verb,
                    url=str(url),
                    params=params,
                    data=data,
                    headers=headers,
                    cookies=cookies,
                    files=files,
                    auth=auth,
                    timeout=timeout,
                    allow_redirects=allow_redirects,
                    proxies=proxies,
                    hooks=hooks,
                    stream=stream,
                    verify=verify,
                    cert=cert,
                    json=json,
                )
            except requests.exceptions.RequestException as e:
                raise _exception.WebAPIRequestError(e) from e
            _raise_for_status_code(
                response=response,
                temporary_error_status_codes=(
                    None if retry_config is None else retry_config.status_codes_to_retry
                ),
                ignored_status_codes=ignored_status_codes,
            )
            return response

        # Depending on specifications in argument `retry_config`, either decorate `get_response`
        # with `retry_on_exception`, or leave it as is.
        response_func = (
            get_response
            if (
                retry_config is None
                or retry_config.status_codes_to_retry is None
                or retry_config.config_status is None
            )
            else _retry_on_exception(
                get_response,
                config=retry_config.config_status,
                catch=_exception.WebAPITemporaryStatusCodeError,
            )
        )
        # Call the (decorated or non-decorated) response function.
        response = response_func()
        # Set encoding of response if specified
        if encoding is not None:
            response.encoding = encoding
        # Get the response value based on specified type
        if response_type is None:
            response_value = response
        elif response_type == "str":
            response_value = response.text
        elif response_type == "json":
            response_value = response.json(**(json_kwargs or {}))
        elif response_type == "bytes":
            response_value = response.content
        else:
            raise ValueError(f"`response_type` {response_type} not recognized.")
        # If no verifier is specified, or verifier accepts the response value, then return the value
        if response_verifier is None or response_verifier(response_value):
            return response_value
        # otherwise raise
        raise _exception.WebAPIValueError(response_value=response_value, response_verifier=response_verifier)

    # Depending on specifications in argument `retry_config`, either decorate `get_response_value`
    # with `retry_on_exception`, or leave it as is.
    response_val_func = (
        get_response_value if (
            retry_config is None
            or retry_config.config_response is None
            or response_verifier is None
        )
        else _retry_on_exception(
            get_response_value,
            config=retry_config.config_response,
            catch=_exception.WebAPIValueError,
        )
    )
    # Call the (decorated or non-decorated) response-value function and return.
    return response_val_func()


def graphql_query(
    url: str,
    query: str,
    variables: dict | None = None,
    params: Optional[Union[dict, List[tuple], bytes]] = None,
    data: Optional[Union[dict, List[tuple], bytes]] = None,
    headers=None,
    cookies=None,
    files=None,
    auth=None,
    timeout: Optional[Union[float, Tuple[float, float]]] = (10, 20),
    allow_redirects=True,
    proxies=None,
    hooks=None,
    stream=None,
    verify=None,
    cert=None,
    response_type: Optional[Literal["str", "json", "bytes"]] = "json",
    encoding: Optional[str] = None,
    response_verifier: Optional[Callable[[Any], bool]] = None,
    retry_config: Optional[HTTPRequestRetryConfig] = HTTPRequestRetryConfig(),
    ignored_status_codes: Optional[Sequence[int]] = None,
    json_kwargs: dict = None,
) -> Union[requests.Response, str, dict, list, bool, int, bytes]:
    args = locals()
    args["verb"] = "POST"
    args["json"] = {"query": args.pop('query')}
    variables = args.pop("variables")
    if variables is not None:
        args["json"]["variables"] = variables
    response = request(**args)
    if isinstance(response, dict):
        error_title = "GraphQL API Error"
        if "errors" in response:
            raise _exception.GraphQLResponseError(response)
        elif "data" not in response:
            raise _exception.GraphQLResponseError(response)
        else:
            response = response["data"]
    return response


def download(url: str, filepath: str | Path, create_dirs: bool = True, overwrite: bool = False) -> Path:
    """
    Download a file from a URL to a local path.

    Parameters
    ----------
    url : str
        URL of the file to download.
    filepath : str | Path
        Local path to save the downloaded file.
    create_dirs : bool, optional, default: True
        Whether to create directories in the local path if they do not exist.
    overwrite : bool, optional, default: False
        Whether to overwrite an existing file in the local path.

    Returns
    -------
    pathlib.Path
        Path to the downloaded file.

    Raises
    ------
    FileExistsError
        If `overwrite` is False and the file already exists.
    """
    filepath = Path(filepath).resolve()
    if filepath.exists():
        if filepath.is_dir():
            raise ValueError(f"Filepath {filepath} is a directory.")
        if not overwrite:
            raise FileExistsError(f"File {filepath} already exists.")
    if not filepath.parent.exists():
        if not create_dirs:
            raise FileNotFoundError(f"Directory {filepath.parent} does not exist.")
        filepath.parent.mkdir(parents=True, exist_ok=True)
    content = request(url=url, response_type="bytes")
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath


def _raise_for_status_code(
    response: requests.Response,
    error_status_code_range: Tuple[int, int] = (400, 599),
    temporary_error_status_codes: Optional[Sequence[int]] = (408, 429, 500, 502, 503, 504),
    ignored_status_codes: Optional[Sequence[int]] = None,
) -> NoReturn:
    """
    Raise an `opencadd.webapi.http_request.WebAPIStatusCodeError` for certain HTTP status codes.

    Parameters
    ----------
    response : requests.Response
        Response of an HTTP request, i.e. the returned object from `requests.request`.
    error_status_code_range : Tuple[int, int], optional, default: (400, 599)
        Range of HTTP status codes considered to be error codes.
    temporary_error_status_codes : Sequence[int], optional, default: (408, 429, 500, 502, 503, 504)
        Set of status codes related to temporary errors. If the status code of the response is
        one of these, an `opencadd.webapi.http_request.WebAPITemporaryStatusCodeError` is raised,
        otherwise an `opencadd.webapi.http_request.WebAPIPersistentStatusCodeError` is raised if
        the status code is inside `error_status_code_range`.
    ignored_status_codes : Sequence[int], optional, default: None
        Set of status codes inside `error_status_code_range` to ignore, i.e. not raise.

    Raises
    ------
    opencadd.webapi.http_request.WebAPITemporaryStatusCodeError
        When the status code is in `temporary_error_status_codes`.
    opencadd.webapi.http_request.WebAPIPersistentError
        When the satus code is in range `error_status_code_range`
        and not inside `temporary_error_status_codes`.
    """
    if ignored_status_codes is not None and response.status_code in ignored_status_codes:
        return
    if (
        temporary_error_status_codes is not None
        and response.status_code in temporary_error_status_codes
    ):
        raise _exception.WebAPITemporaryStatusCodeError(response)
    if error_status_code_range[0] <= response.status_code <= error_status_code_range[1]:
        raise _exception.WebAPIPersistentStatusCodeError(response)
    return


def _retry_on_exception(
    function: Optional[Callable] = None,
    *,
    config: RetryConfig = RetryConfig(),
    catch: Type[Exception] | tuple[Type[Exception]] = Exception,
) -> Callable:
    """
    Decorator to retry a function call for a given number of times
    (while waiting for a certain amount of time between calls),
    when one of the given exceptions is raised.

    Parameters
    ----------
    function : callable
        The function to be decorated.
    config : RetryConfig, default: RetryConfig(3, 1, 3)
        Retry configuration.
    catch : Type[Exception] | tuple[Type[Exception]], default: Exception
        Exception type(s) that will be ignored during the retries.
        All other exceptions will be raised immediately.

    Returns
    -------
    callable
        Decorated function.
    """
    if not isinstance(config.num_tries, int) or config.num_tries < 1:
        raise ValueError("`num_tries` must be a positive integer.")

    def retry_decorator(func):

        @wraps(func)
        def retry_wrapper(*args, **kwargs):
            curr_sleep_seconds = config.sleep_time_init
            for try_count in range(config.num_tries):
                try:
                    return func(*args, **kwargs)
                except catch as e:
                    if try_count == config.num_tries - 1:
                        raise e
                    time.sleep(curr_sleep_seconds)
                    curr_sleep_seconds *= config.sleep_time_scale

        return retry_wrapper

    return retry_decorator if function is None else retry_decorator(function)
