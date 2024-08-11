from pylinks.exception import PyLinksException as _PyLinksException


class PyLinksMediaTypeParseError(_PyLinksException):
    """Error parsing a media type."""
    def __init__(self, message: str, media_type: str):
        msg = f"Failed to parse media type '{media_type}': {message}"
        super().__init__(message=msg)
        self.message = message
        self.media_type = media_type
        return
