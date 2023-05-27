
from typing import Optional
import requests

from pylinks import OFFLINE_MODE as _OFFLINE_MODE
from pylinks import URL


class ReadTheDocs:

    URL_BASE = URL(base='https://readthedocs.org')

    def __init__(self, project: str, validate: Optional[bool] = None):
        if not isinstance(project, str):
            raise TypeError(f"`project` must be a string, not {type(project)}.")
        self.project = project
        self.project_url = self.URL_BASE / f'projects/{project}'
        if validate is True or (validate is None and not _OFFLINE_MODE):
            requests.get(str(self.project_url)).raise_for_status()
        self.website_url = URL(base=f'https://{project}.readthedocs.io')
        return

    @property
    def build_status_url(self):
        return self.project_url / 'builds'
