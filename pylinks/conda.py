
from typing import Optional
import re
import requests

from pylinks import URL, OFFLINE_MODE


BASE_URL = URL(base="https://anaconda.org")


class Project:

    def __init__(self, name: str, channel: str, validate: Optional[bool] = None):
        if not isinstance(name, str):
            raise TypeError(f"`name` must be a string, not {type(name)}.")
        if re.match("^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", name, flags=re.IGNORECASE) is None:
            raise ValueError('Distribution name is invalid; see https://peps.python.org/pep-0508/#names.')
        self._name = name
        self._channel = channel
        if validate is True or (validate is None and not OFFLINE_MODE):
            requests.get(str(self.home)).raise_for_status()

    @property
    def home(self) -> URL:
        return BASE_URL / self.channel / self.name

    @property
    def name(self) -> str:
        return self._name

    @property
    def channel(self) -> str:
        return self._channel


def project(name: str, channel: str, validate: Optional[bool] = None) -> Project:
    return Project(name=name, channel=channel, validate=validate)
