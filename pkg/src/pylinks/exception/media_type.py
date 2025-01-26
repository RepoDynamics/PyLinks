import mdit as _mdit

from pylinks.exception import PyLinksError as _PyLinksError


class PyLinksMediaTypeParseError(_PyLinksError):
    """Error parsing a media type."""
    def __init__(self, problem: str, media_type: str):
        super().__init__(
            title="Media Type Parse Error",
            intro=_mdit.inline_container(
                "Failed to parse media type ",
                _mdit.element.code_span(media_type),
                ". ",
                problem,
            )
        )
        self.problem = problem
        self.media_type = media_type
        return


class PyLinksMediaTypeGuessError(_PyLinksError):
    """Error guessing the media type of a data URI."""
    def __init__(self, path: str):
        super().__init__(
            title="Media Type Guess Error",
            intro=_mdit.inline_container(
                "Failed to guess the media type of the file at path ",
                _mdit.element.code_span(path),
            )
        )
        self.path = path
        return
