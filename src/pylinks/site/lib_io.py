"""URLs for the Libraries.io website."""


# Non-standard libraries
import requests
import pylinks as _pylinks


BASE_URL = _pylinks.url.create(url="https://libraries.io")


class Package:
    """A Libraries.IO package site."""

    def __init__(self, platform: str, package: str, validate: bool | None = None):
        """
        Parameters
        ----------
        platform : str
            Name of the platform where the package is distributed, e.g. 'pypi', 'npm', etc.
        package : str
            Name of the package.
        validate : bool, default: None
            Whether to validate the URL online (requires an active internet connection).
            If set to None (default), the global default value defined in `pylinks.OFFLINE_MODE` is used.
        """
        if not isinstance(platform, str):
            raise TypeError(f"`platform` must be a string, not {type(platform)}.")
        if not isinstance(package, str):
            raise TypeError(f"`package` must be a string, not {type(package)}.")
        self._platform = platform
        self._package = package
        if validate is True or (validate is None and not _pylinks.settings.offline_mode):
            requests.get(str(self.homepage)).raise_for_status()
        return

    @property
    def platform(self) -> str:
        """Name of the platform."""
        return self._platform

    @property
    def package(self) -> str:
        """Name of the package."""
        return self._package

    @property
    def homepage(self) -> _pylinks.url.URL:
        """URL of the package's homepage."""
        return BASE_URL / self._platform / self._package

    def dependencies(self, version: str) -> _pylinks.url.URL:
        """URL of the webpage showing the dependencies of the package."""
        return self.homepage / version / "tree"

    @property
    def source_rank(self) -> _pylinks.url.URL:
        """URL of the webpage showing the source rank of the package."""
        return self.homepage / "sourcerank"


def package(
    platform: str,
    package: str,
    validate: bool | None = None,
):
    return Package(platform=platform, package=package, validate=validate)
