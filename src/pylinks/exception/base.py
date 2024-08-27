"""PyLinks base exception."""

from pathlib import Path as _Path


class PyLinksException(Exception):
    """Base exception for PyLinks.

    All exceptions raised by PyLinks inherit from this class.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
        return


class PyLinksFileNotFoundError(PyLinksException):
    """File not found error."""
    def __init__(self, path: str | _Path):
        msg = f"No file found at input path '{path}.'"
        super().__init__(message=msg)
        self.path = path
        return
