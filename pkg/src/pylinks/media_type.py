"""Create and parse [media types](https://en.wikipedia.org/wiki/Media_type).

References
----------
- [Offical IANA Media Types](https://www.iana.org/assignments/media-types/media-types.xml)
- [Common MIME types](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types)
- [Database of mime types](https://github.com/jshttp/mime-db/tree/master)
- [Database of mime types](https://github.com/patrickmccallum/mimetype-io/blob/master/src/mimeData.json)
- [JSON list of file extensions with their mime types](https://github.com/micnic/mime.json)
- [Python mimetypes](https://docs.python.org/3/library/mimetypes.html)
"""

import mimetypes as _mimetypes
import dataclasses as _dataclasses
import re as _re

from pylinks import exception as _exception


@_dataclasses.dataclass
class MediaType:
    """A [Media Type](https://www.iana.org/assignments/media-types/media-types.xhtml) (aka MIME type).

    A media type consists of a type, a subtype with optional tree prefix,
    optional suffixes, and optional parameters in the following format:
    ```
    media-type = type "/" [tree "."] subtype ["+" suffix]* [";" parameter];
    ```

    Attributes
    ----------
    type : str, default: ""
        Type of the media. Standard types are
        'application', 'audio', 'example', 'font', 'haptics',
        'image', 'message', 'model', 'multipart', 'text', and 'video'.
    tree : str, default: ""
        Tree prefix of the media type, e.g., 'vnd', 'prs', 'x'.
    subtype : str, default: ""
        Subtype of the media (without the tree prefix), e.g.,
        'json', 'ms-excel', 'oasis.opendocument.text'.
    suffixes : list[str], default: []
        Type suffixes, e.g., 'json', 'xml', 'zip'.
    parameters : dict[str, str | None], default: {}
        Additional parameters, e.g., `{"charset": "UTF-8"}`.
    """
    type: str
    subtype: str
    tree: str = ""
    suffixes: list[str] = _dataclasses.field(default_factory=list)
    parameters: dict[str, str | None] = _dataclasses.field(default_factory=dict)

    def __str__(self) -> str:
        suffixes = "".join(f"+{suffix}" for suffix in self.suffixes)
        if self.parameters:
            joined = "; ".join(f"{k}={v}" if v else k for k, v in self.parameters.items())
            params = f"; {joined}"
        else:
            params = ""
        full_subtype = f"{self.tree}.{self.subtype}" if self.tree else self.subtype
        return f"{self.type}/{full_subtype}{suffixes}{params}"


def parse(media_type: str) -> MediaType:
    regex = _re.compile(
        r"""
            ^
            (?P<type>[\w\-]+)
            /
            (?:(?P<tree>[\w\-]+)\.)?
            (?P<subtype>[\w\-.]+)
            (?P<suffixes>(\+[\w\-.]+)*)?
            (?:\s*;\s*(?P<parameters>.*))?
            $
        """,
        _re.VERBOSE
    )
    match = regex.match(media_type)
    if not match:
        raise _exception.media_type.PyLinksMediaTypeParseError(
            f"The input does not match the regex pattern '{regex.pattern}'.",
            media_type
        )
    mime = match.groupdict()
    mime["suffixes"] = [suffix for suffix in mime.get("suffixes", "").split("+") if suffix]
    params = {}
    if mime["parameters"]:
        for param in mime["parameters"].split(";"):
            key, *value = param.split("=", 1)
            params[key.strip()] = value[0].strip() if value else None
    mime["parameters"] = params
    return MediaType(**mime)


def guess_from_uri(uri: str) -> MediaType:
    """Guess the media type of a given URI (e.g. URL or filepath).

    Parameters
    ----------
    uri : str
        The URI to guess the media type from.

    Returns
    -------
    MediaType
        The guessed media type.
    """
    uri = str(uri)
    mimetype = _mimetypes.guess_type(uri)[0]
    if mimetype is None:
        raise _exception.media_type.PyLinksMediaTypeGuessError(uri)
    return parse(mimetype)

# TODO: Add function to guess from file
# Refs:
# - https://pypi.org/project/python-magic/