from pylinks.exception import PyLinksException as _PyLinksException


class PyLinksMediaTypeParseError(_PyLinksException):
    """Error parsing a media type."""
    def __init__(self, message: str, media_type: str):
        msg = f"Failed to parse media type '{media_type}': {message}"
        super().__init__(message=msg)
        self.message = message
        self.media_type = media_type
        return


class PyLinksMediaTypeGuessError(_PyLinksException):
    """Error guessing the media type of a data URI."""
    def __init__(self, path: str):
        msg = f"Failed to guess the media type of '{path}'."
        super().__init__(message=msg)
        self.path = path
        return
