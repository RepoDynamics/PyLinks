"""URLs for Binder images.

References
----------
- [Binder](https://mybinder.org/)
"""


import pylinks as _pylinks


_BASE_URL = _pylinks.url.create(url="https://mybinder.org/v2")


def github(
    user: str,
    repo: str,
    ref: str = "HEAD",
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a GitHub repository.

    Parameters
    ----------
    user : str
        GitHub username.
    repo : str
        GitHub repository name.
    ref : str, default: "HEAD"
        Branch, tag, or commit hash to use.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "gh" / user / repo / ref
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url


def gist(
    user: str,
    gist_id: str,
    ref: str = "HEAD",
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a GitHub Gist.

    Parameters
    ----------
    user : str
        GitHub username.
    gist_id : str
        GitHub Gist ID.
    ref : str, default: "HEAD"
        Commit hash to use.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "gist" / user / gist_id / ref
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url


def git(
    url: str,
    ref: str = "HEAD",
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a Git repository.

    Parameters
    ----------
    url : str
        URL of the Git repository.
    ref : str, default: "HEAD"
        Branch, tag, or commit hash to use.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "git" / url / ref
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url


def gitlab(
    user: str,
    repo: str,
    ref: str = "HEAD",
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a GitLab repository.

    Parameters
    ----------
    user : str
        GitLab username.
    project : str
        GitLab repository name.
    ref : str, default: "HEAD"
        Branch, tag, or commit hash to use.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "gl" / user / repo / ref
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url


def zenodo(
    doi: str,
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a Zenodo repository.

    Parameters
    ----------
    doi : str
        Zenodo DOI.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "zenodo" / doi
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url


def figshare(
    doi: str,
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a Figshare repository.

    Parameters
    ----------
    doi : str
        Figshare DOI.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "figshare" / doi
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url


def hydroshare(
    resource_id: str,
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a HydroShare resource.

    Parameters
    ----------
    resource_id : str
        HydroShare resource ID.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "hydroshare" / resource_id
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url


def dataverse(
    doi: str,
    notebook_path: str | None = None,
) -> _pylinks.url.URL:
    """Create a Binder URL for a Dataverse repository.

    Parameters
    ----------
    doi : str
        Dataverse DOI.
    notebook_path : str, optional
        Path to a Jupyter notebook file to open.
    """
    url = _BASE_URL / "dataverse" / doi
    if notebook_path is not None:
        url.queries["labpath"] = notebook_path
    return url
