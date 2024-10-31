from typing import Optional

from pylinks.api.doi import DOI
from pylinks.api.github import GitHub
from pylinks.api.orcid import Orcid
from pylinks.api.zenodo import Zenodo


def doi(doi: str) -> DOI:
    return DOI(doi=doi)


def github(token: Optional[str] = None) -> GitHub:
    return GitHub(token=token)


def orcid(orcid_id: str) -> Orcid:
    return Orcid(orcid_id=orcid_id)


def zenodo(token: str, sandbox: bool = False) -> Zenodo:
    return Zenodo(token=token, sandbox=sandbox)