
from typing import Optional
from pylinks import URL
from pylinks import OFFLINE_MODE
import re
import requests


BASE_URL = URL(base="https://pypi.org")


class Project:

    def __init__(self, name: str, validate: Optional[bool] = None):
        if not isinstance(name, str):
            raise TypeError(f"`name` must be a string, not {type(name)}.")
        if re.match("^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", name, flags=re.IGNORECASE) is None:
            raise ValueError('Distribution name is invalid; see https://peps.python.org/pep-0508/#names.')
        self._name = name
        if validate is True or (validate is None and not OFFLINE_MODE):
            requests.get(str(self.home)).raise_for_status()

    @property
    def home(self) -> URL:
        return BASE_URL / 'project' / self.name

    @property
    def name(self) -> str:
        return self._name


def project(name: str, validate: Optional[bool] = None) -> Project:
    return Project(name=name, validate=validate)

