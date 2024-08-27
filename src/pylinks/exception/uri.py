from pathlib import Path as _Path

from pylinks.exception import PyLinksException as _PyLinksException


class PyLinksDataURIParseError(_PyLinksException):
    """Error parsing a data URI."""
    def __init__(self, message: str, data_uri: str):
        msg = f"Failed to parse data URI '{data_uri}': {message}"
        super().__init__(message=msg)
        self.message = message
        self.data_uri = data_uri
        return
