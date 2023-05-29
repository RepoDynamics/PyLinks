"""PyLinks: Create, Modify and Manage URLs.

PyLinks implements a URL object, making it easy to manipulate and work with URLs.
It also offers a number of URL generators for popular online platforms
such as GitHub, PyPI, Anaconda, ReadTheDocs etc., allowing for facile and dynamic
creation of many useful URLs.
"""


from .url import URL
from . import binder, conda, github, pypi, readthedocs


OFFLINE_MODE: bool = False
"""Global variable to set whether URL generators should verify the created URLs online."""
