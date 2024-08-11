"""Generate data URIs."""
import re
import re as _re
import dataclasses as _dataclasses

from pylinks import media_type as _media_type
from pylinks.exception.uri import PyLinksDataURIParseError as _PyLinksDataURIParseError


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
    data: str = ""
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
    regex = re.compile(
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


def create(
    media_type: str | dict[str, str | None] | list[str | tuple[str, str]] = "",
    data: str = "",
    base64: bool = False,
) -> str:
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
    if isinstance(media_type, str):
        media_type = {media_type: None}
    elif isinstance(media_type, (list, tuple)):
        media_type = {media_type[0]: media_type[1] if len(media_type) == 2 else None}
    return f"data:{';'.join(f"{k}={v}" for k, v in media_type.items())};base64,{_base64.b64encode(data.encode()).decode() if base64 else data}"