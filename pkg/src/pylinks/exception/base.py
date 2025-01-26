"""PyLinks base exception."""

from __future__ import annotations as _annotations
from typing import TYPE_CHECKING as _TYPE_CHECKING
from functools import partial as _partial

from exceptionman import ReporterException as _ReporterException
import mdit as _mdit

if _TYPE_CHECKING:
    from pathlib import Path


class PyLinksError(_ReporterException):
    """Base exception for PyLinks.

    All exceptions raised by PyLinks inherit from this class.
    """
    def __init__(
        self,
        title: str,
        intro,
        details = None,
    ):
        sphinx_config = {"html_title": "PyLinks Error Report"}
        sphinx_target_config = _mdit.target.sphinx(
            renderer=_partial(
                _mdit.render.sphinx,
                config=_mdit.render.get_sphinx_config(sphinx_config)
            )
        )
        report = _mdit.document(
            heading=title,
            body={"intro": intro},
            section={"details": _mdit.document(heading="Details", body=details)} if details else None,
            target_configs_md={"sphinx": sphinx_target_config},
        )
        super().__init__(report=report)
        return


class PyLinksFileNotFoundError(PyLinksError):
    """File not found error."""
    def __init__(self, path: Path):
        super().__init__(
            title="File Not Found Error",
            intro=_mdit.inline_container("No file found at input path ", _mdit.element.code_span(str(path))),
        )
        self.path = path
        return
