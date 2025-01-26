import mdit as _mdit

from pylinks.exception import PyLinksError as _PyLinksError


class PyLinksDataURIParseError(_PyLinksError):
    """Error parsing a data URI."""
    def __init__(self, problem: str, data_uri: str):
        super().__init__(
            title="Data URI Parse Error",
            intro=_mdit.inline_container(
                "Failed to parse data URI ",
                _mdit.element.code_span(data_uri),
                ". ",
                problem,
            )
        )
        self.problem = problem
        self.data_uri = data_uri
        return
