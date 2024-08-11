"""PyLinks base exception."""


class PyLinksException(Exception):
    """Base exception for PyLinks.

    All exceptions raised by PyLinks inherit from this class.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
        return
