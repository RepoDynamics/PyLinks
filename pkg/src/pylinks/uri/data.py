"""Generate and process [data URIs](https://en.wikipedia.org/wiki/Data_URI_scheme).

"""

import base64 as _base64
import re as _re
from pathlib import Path as _Path
import dataclasses as _dataclasses
from typing import Literal as _Literal

from pylinks.url import URL as _URL
from pylinks.http import request as _request
from pylinks import media_type as _media_type
from pylinks.exception.uri import PyLinksDataURIParseError as _PyLinksDataURIParseError
from pylinks.exception.base import PyLinksFileNotFoundError as _PyLinksFileNotFoundError


@_dataclasses.dataclass
class DataURI:
    """A data URI.

    Attributes
    ----------
    media_type : pylinks.media_type.MediaType, default: ""
        The media type of the data.
    data : str, default: ""
        The data.
    base64 : bool, default: False
        Whether the data is base64 encoded.
    """
    media_type: _media_type.MediaType | None = None
    data: str | None = None
    base64: bool = False

    def __str__(self) -> str:
        media_type = str(self.media_type) if self.media_type else ""
        if self.base64:
            media_type += ";base64"
        return f"data:{media_type},{self.data}"


def parse(data_uri: str) -> DataURI:
    """Parse a data URI.

    Parameters
    ----------
    data_uri : str
        The data URI to parse.

    Returns
    -------
    DataURI
        The parsed data URI.
    """
    regex = _re.compile(
        r"^data:(?P<media_type>.*?)(?P<base64>\s*;\s*base64)?\s*,(?P<data>.*)$"
    )
    match = regex.match(data_uri)
    if not match:
        raise _PyLinksDataURIParseError(
            f"The input does not match the regex pattern '{regex.pattern}'.",
            data_uri,
        )
    components = match.groupdict()
    media_type = components["media_type"] or None
    if media_type:
        media_type = _media_type.parse(media_type)
    components["media_type"] = media_type
    components["base64"] = bool(components["base64"])
    return DataURI(**components)


def create_from_path(
    path_type: _Literal["file", "url"],
    path: str,
    media_type: _media_type.MediaType | None = None,
    guess_media_type: bool = True,
    base64: bool = False,
) -> DataURI:
    if path_type == "file":
        return create_from_filepath(
            filepath=path,
            media_type=media_type,
            guess_media_type=guess_media_type,
            base64=base64,
        )
    elif path_type == "url":
        return create_from_url(
            url=path,
            media_type=media_type,
            guess_media_type=guess_media_type,
            base64=base64,
        )
    raise ValueError(f"path_type '{path_type}' is invalid.")


def create_from_url(
    url: str | _URL,
    media_type: _media_type.MediaType | None = None,
    guess_media_type: bool = True,
    base64: bool = False,
) -> DataURI:
    """Create a data URI from a URL.

    Parameters
    ----------
    url : str | pylinks.url.URL
        The URL of the data.
    media_type : pylinks.media_type.MediaType | str | None, optional
        Media (MIME) Type of the data.
    guess_media_type : bool, default: True
        Whether to guess the media type from the URL.
        This is only done if the media type is not provided,
        and will raise an error if the media type cannot be guessed.
    base64 : bool, default: False
        Whether to base64 encode the data.

    Returns
    -------
    pylinks.uri.data.DataURI
        The data URI.
    """
    url = str(url)
    if media_type is None and guess_media_type:
        media_type = _media_type.guess_from_uri(url)
    data = _request(url, response_type="str" if not base64 else "bytes")
    return create_from_data(data=data, media_type=media_type, base64=base64)


def create_from_filepath(
    filepath: str | _Path,
    media_type: _media_type.MediaType | None = None,
    guess_media_type: bool = True,
    base64: bool = False,
) -> DataURI:
    """Create a data URI from a file.

    Parameters
    ----------
    filepath : str | pathlib.Path
        Path to the file.
    media_type : pylinks.media_type.MediaType | str | None, optional
        Media (MIME) Type of the data.
    guess_media_type : bool, default: True
        Whether to guess the media type from the URL.
        This is only done if the media type is not provided,
        and will raise an error if the media type cannot be guessed.
    base64 : bool, default: False
        Whether to base64 encode the data.

    Returns
    -------
    pylinks.uri.data.DataURI
        The data URI.
    """
    filepath = _Path(filepath).resolve()
    if not filepath.is_file():
        raise _PyLinksFileNotFoundError(filepath)
    if media_type is None and guess_media_type:
        media_type = _media_type.guess_from_uri(str(filepath))
    data = filepath.read_bytes() if base64 else filepath.read_text()
    return create_from_data(data=data, media_type=media_type, base64=base64)


def create_from_data(
    data: str | bytes,
    media_type: _media_type.MediaType | None = None,
    base64: bool = False,
) -> DataURI:
    """Create a data URI.

    Parameters
    ----------
    media_type : str | list[str | tuple[str, str]] | dict[str, str | None], optional
        The media type of the data.
        This can be either a fully formed media type as a string,
        a dictionary of parameter name and value pairs (using None for parameters without values),
        or an iterable where the elements are either strings (for parameters without values)
        or tuples of parameter name and value.
        For example, all of the following are valid and equivalent:
        - As a string: "text/plain;charset=UTF-8"
        - As a list of strings (attribute-value pairs not separated): `["text/plain", "charset=UTF-8"]`
        - As a list of strings and tuples: `["text/plain", ("charset", "UTF-8")]`
        - As a dictionary: `{"text/plain": None, "charset": "UTF-8"}`
    data : str, optional
        The data to include in the URI.
    base64 : bool, default: False
        Whether the data is base64 encoded.

    Returns
    -------
    str
        The data URI.
    """
    if base64:
        data_bytes = data.encode() if isinstance(data, str) else data
        data_str = _base64.b64encode(data_bytes).decode()
    else:
        data_str = data
    return DataURI(media_type=media_type, data=data_str, base64=base64)
