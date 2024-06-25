"""URLs for GitHub users, repositories, branches, and more."""


# Standard libraries
import re
from typing import Literal, Optional

# Non-standard libraries
import requests
import pylinks as _pylinks


BASE_URL = _pylinks.url.create(url="https://github.com")


class User:
    """A GitHub user account."""

    def __init__(self, name: str, validate: Optional[bool] = None):
        """
        Parameters
        ----------
        name : str
            GitHub username.
        validate : bool
            Whether to validate online that the given username exists.
        """
        if not isinstance(name, str):
            raise TypeError(f"`name` must be a string, not {type(name)}.")
        if re.match(r"^[A-Za-z0-9-]+$", name) is None:
            raise ValueError(
                "GitHub usernames can only contain alphanumeric characters and dashes."
            )
        self._name = name
        if validate is True or (validate is None and not _pylinks.settings.offline_mode):
            requests.get(str(self.homepage)).raise_for_status()
        return

    def __str__(self):
        return str(self.homepage)

    def __repr__(self):
        return f"GitHub-User: {self.name} @ {self.homepage}"

    @property
    def name(self) -> str:
        """GitHub username."""
        return self._name

    @property
    def homepage(self) -> _pylinks.url.URL:
        """URL of the GitHub user's homepage."""
        return BASE_URL / self.name

    def repo(self, repo_name: str, validate: Optional[bool] = None) -> "Repo":
        """A repository of the user."""
        return Repo(user=self, name=repo_name, validate=validate)


class Repo:
    """A GitHub Repository."""

    def __init__(self, user: User | str, name: str, validate: Optional[bool] = None):
        """
        Parameters
        ----------
        user : User | str
            A GitHub user account, either as a User instance, or its name as a string.
        name : str
            Name of the repository in the user account.
        validate : bool, default: None
            Whether to validate the URL online (requires an active internet connection).
            If set to None (default), the global default value defined in `pylinks.OFFLINE_MODE` is used.
        """
        if isinstance(user, str):
            self._user = User(name=user, validate=validate)
        elif isinstance(user, User):
            self._user = user
        else:
            raise TypeError(
                f"`user` must be a User instance or a username as string, not {type(user)}."
            )
        if not isinstance(name, str):
            raise TypeError("`repo_name` must be a string.")
        self._name = name
        if re.match(r"^[A-Za-z0-9_.-]+$", name) is None:
            raise ValueError(
                'GitHub repository names can only contain "_", "-", ".", and alphanumeric characters.'
            )
        if validate is True or (validate is None and not _pylinks.settings.offline_mode):
            requests.get(str(self.homepage)).raise_for_status()
        return

    def __str__(self):
        return str(self.homepage)

    def __repr__(self):
        return f"GitHub-Repo: {self.name} by {self.user.name} @ {self.homepage}"

    @property
    def user(self) -> User:
        """The Repository's user account."""
        return self._user

    @property
    def name(self) -> str:
        """Name of the repository."""
        return self._name

    @property
    def homepage(self) -> _pylinks.url.URL:
        """URL of the repository's homepage."""
        return self.user.homepage / self.name

    def workflow(self, filename: str) -> _pylinks.url.URL:
        """
        URL of a GitHub Actions workflow in the repository.

        Parameters
        ----------
        filename : str
            Filename of the workflow, e.g. 'ci.yaml'.
        """
        return self.homepage / "actions/workflows" / filename

    def workflow_run(self, run_id: str) -> _pylinks.url.URL:
        """
        URL of the summary page of a specific GitHub Actions workflow run in the repository.

        Parameters
        ----------
        run_id : str
            The ID of the workflow run, e.g. '123456789'.
        """
        return self.homepage / "actions/runs" / run_id

    def pr_issues(
        self, pr: bool = True, closed: Optional[bool] = None, label: Optional[str] = None
    ) -> _pylinks.url.URL:
        """
        URL of pull requests or issues in the repository.

        Parameters
        ----------
        pr : bool, default: True
            Whether to link to pull requests (True) or issues (False).
        closed : bool, default: None
            Whether to link to closed (True) or open (False) pull requests/issues,
            or both (None).
        label : str, default: None
            A specific label to query.
        """
        url = self.homepage / ("pulls" if pr else "issues")
        if closed is None and label is None:
            return url
        url.quote_safe = "+"
        url.queries["q"] = f"is:{'pr' if pr else 'issue'}"
        if closed is not None:
            url.queries["q"] += f'+is:{"closed" if closed else "open"}'
        if label is not None:
            url.queries["q"] += f"+label:{label}"
        return url

    def commit(self, commit_hash: str) -> _pylinks.url.URL:
        """URL of a specific commit in the repository."""
        return self.homepage / "commit" / commit_hash

    def releases(self, tag: Optional[str | Literal["latest"]] = None) -> _pylinks.url.URL:
        """
        URL of the releases overview page, or a specific release.

        Parameters
        ----------
        tag : str, default: None
            An optional tag to query. If provided, the URL will point to the release page of that specific tag,
            otherwise, the URL of release summary page is returned.
            In addition to a tag name, the keyword 'latest' can also be used, in which case the URL will
            always point to the latest release page.
        """
        base_url = self.homepage / "releases"
        if not tag:
            return base_url
        if tag == "latest":
            return base_url / "latest"
        return base_url / "tag" / tag

    @property
    def commits(self) -> _pylinks.url.URL:
        """URL of commits page."""
        return self.homepage / "commits"

    def compare(self, base: str, head: str) -> _pylinks.url.URL:
        """
        URL of a comparison between two references, i.e., branches, tags, or hashes.

        Parameters
        ----------
        base : str
            The base reference.
        head : str
            The head reference.
        """
        return self.homepage / "compare" / f"{base}...{head}"

    def discussions(self, category: Optional[str] = None) -> _pylinks.url.URL:
        """
        URL of discussions page, or a specific discussion category page.

        Parameters
        ----------
        category : str, default: None
            An optional discussions category, e.g. 'announcements'.
        """
        url = self.homepage / "discussions"
        if category:
            url /= f"categories/{category}"
        return url

    def milestones(self, state: Literal["open", "closed"] = "open"):
        """
        URL of summary page for open or closed milestones.

        Parameters
        ----------
        state : {'open', 'closed'}, default: 'open'
            Whether to link to open or closed milestones.
        """
        url = self.homepage / "milestones"
        if state:
            url.queries["state"] = state
        return url

    def branch(self, branch_name: str, validate: Optional[bool] = None) -> "Branch":
        """A branch of the Repository"""
        return Branch(repo=self, name=branch_name, validate=validate)


class Branch:
    """A GitHub repository branch."""

    def __init__(self, repo: Repo, name: str, validate: Optional[bool] = None):
        """
        Parameters
        ----------
        repo : Repo
            The GitHub repository containing the branch.
        name : str
            Name of the branch.
        validate : bool, default: None
            Whether to validate the URL online (requires an active internet connection).
            If set to None (default), the global default value defined in `pylinks.OFFLINE_MODE` is used.
        """
        if not isinstance(repo, Repo):
            raise TypeError("`repo` must be a Repo instance.")
        self._repo = repo
        if not isinstance(name, str):
            raise TypeError("`name` must be a string.")
        self._name = name
        if re.match(r"^[A-Za-z0-9/_.-]+$", name) is None:
            raise ValueError(
                'GitHub branch names can only contain "_", "-", ".", "/", and alphanumeric characters.'
            )
        if validate is True or (validate is None and not _pylinks.settings.offline_mode):
            requests.get(str(self.homepage)).raise_for_status()
        return

    @property
    def repo(self) -> Repo:
        """The repository holding the branch."""
        return self._repo

    @property
    def homepage(self) -> _pylinks.url.URL:
        """URL of the branch's homepage."""
        return self.repo.homepage / "tree" / self.name

    @property
    def name(self) -> str:
        """Name of the branch."""
        return self._name

    def workflow(self, filename: str) -> _pylinks.url.URL:
        """
        URL of a GitHub Actions workflow for this specific branch.

        Parameters
        ----------
        filename : str
            Filename of the workflow, e.g. 'ci.yaml'.
        """
        url = self.repo.homepage / "actions/workflows" / filename
        url.queries = {"query": f"branch:{self.name}"}
        return url

    def file(self, filename: str, raw: bool = False) -> _pylinks.url.URL:
        """URL of a specific file in the branch."""
        if raw:
            return (
                _pylinks.url.create("https://raw.githubusercontent.com")
                / self.repo.user.name
                / self.repo.name
                / self.name
                / filename
            )
        return self.homepage / filename

    @property
    def commits(self) -> _pylinks.url.URL:
        """URL of commits page for this branch."""
        return self.repo.homepage / "commits" / self.name


def user(name: str, validate: Optional[bool] = None) -> User:
    """
    Create a new URL generator for a GitHub user.

    Parameters
    ----------
    name : str
        GitHub username.
    validate : bool, default: None
        Whether to validate the URL online (requires an active internet connection).
        If set to None (default), the global default value defined in `pylinks.OFFLINE_MODE` is used.
    """
    return User(name=name, validate=validate)
