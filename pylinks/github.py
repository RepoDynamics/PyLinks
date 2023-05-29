"""GitHub URLs."""


from typing import Optional, Literal
import re

import requests

import pylinks
from pylinks import URL


BASE_URL = URL(base='https://github.com')


class User:
    """GitHub user."""

    def __init__(self, username: str, validate: Optional[bool] = None):
        """
        Parameters
        ----------
        username : str
            GitHub username.
        validate : bool
            Whether to validate online that the given username exists.
        """
        if not isinstance(username, str):
            raise TypeError(f"`name` must be a string, not {type(username)}.")
        if re.match(r'^[A-Za-z0-9-]+$', username) is None:
            raise ValueError('GitHub usernames can only contain alphanumeric characters and dashes.')
        self._username = username
        if validate is True or (validate is None and not pylinks.OFFLINE_MODE):
            requests.get(str(self.url)).raise_for_status()
        return

    def __str__(self):
        return str(self.url)

    def __repr__(self):
        return f"GitHub-User: {self.name} @ {self.url}"

    @property
    def name(self) -> str:
        """GitHub username."""
        return self._username

    @property
    def url(self) -> URL:
        """URL of the GitHub user's main page."""
        return BASE_URL / self.name

    def repo(self, repo_name: str, validate: Optional[bool] = None) -> 'Repo':
        """A repository of the user."""
        return Repo(user=self, repo_name=repo_name, validate=validate)


class Repo:
    def __init__(self, user: User | str, repo_name: str, validate: Optional[bool] = None):
        if isinstance(user, str):
            self._user = User(username=user, validate=validate)
        elif isinstance(user, User):
            self._user = user
        else:
            raise TypeError(f"`user` must be a User instance or a username as string, not {type(user)}.")
        self._user = user
        if not isinstance(repo_name, str):
            raise TypeError("`repo_name` must be a string.")
        self._repo_name = repo_name
        if re.match(r'^[A-Za-z0-9_.-]+$', repo_name) is None:
            raise ValueError(
                'GitHub repository names can only contain "_", "-", ".", and alphanumeric characters.'
            )
        if validate is True or (validate is None and not pylinks.OFFLINE_MODE):
            requests.get(str(self.url)).raise_for_status()
        return

    def __str__(self):
        return str(self.url)

    def __repr__(self):
        return f"GitHub-Repo: {self.name} by {self.user.name} @ {self.url}"

    @property
    def user(self) -> User:
        return self._user

    @property
    def name(self) -> str:
        return self._repo_name

    @property
    def url(self) -> URL:
        return self.user.url / self.name

    def workflow(self, filename: str) -> URL:
        return self.url / f'actions/workflows/{filename}'

    def pr_issues(self, pr: bool = True, closed: Optional[bool] = None, label: Optional[str] = None) -> URL:
        url = self.url / ('pulls' if pr else 'issues')
        if closed is None and label is None:
            return url
        url.queries['q'] = 'is' + ('pr' if pr else 'issue')
        if closed is not None:
            url.queries['q'] += f'+is:{"closed" if closed else "open"}'
        if label is not None:
            url.queries['q'] += f'+label:{label}'
        url.quote_safe = '+'
        return url

    def releases(self, tag: Optional[str | Literal['latest']] = None) -> URL:
        base_url = self.url / 'releases'
        if not tag:
            return base_url
        if tag == 'latest':
            return base_url / 'latest'
        return base_url / 'tag' / tag

    @property
    def commits(self) -> URL:
        return self.url / 'commits'

    def discussions(self, category: Optional[str]) -> URL:
        url = self.url / 'discussions'
        if category:
            url /= f'categories/{category}'
        return url

    def milestones(self, state: Literal['open', 'closed'] = 'open'):
        url = self.url / 'milestones'
        if state:
            url.queries['state'] = state
        return url


    def branch(self, branch_name: str, validate: Optional[bool] = None) -> 'Branch':
        """A branch of the Repository"""
        return Branch(repo=self, branch_name=branch_name, validate=validate)


class Branch:
    def __init__(self, repo: Repo, branch_name: str, validate: Optional[bool] = None):
        if not isinstance(repo, Repo):
            raise TypeError("`repo` must be a Repo instance.")
        self._repo = repo
        if not isinstance(branch_name, str):
            raise TypeError("`name` must be a string.")
        self._branch_name = branch_name
        if re.match(r'^[A-Za-z0-9_.-]+$', branch_name) is None:
            raise ValueError(
                'GitHub branch names can only contain "_", "-", ".", and alphanumeric characters.'
            )
        self._url = self.repo.url / 'tree' / branch_name
        if validate is True or (validate is None and not pylinks.OFFLINE_MODE):
            requests.get(str(self.url)).raise_for_status()
        return

    @property
    def repo(self) -> Repo:
        return self._repo

    @property
    def url(self) -> URL:
        return self._url

    @property
    def branch_name(self) -> str:
        return self._branch_name

    def workflow(self, filename: str) -> URL:
        url = self.repo.url / f'actions/workflows/{filename}'
        url.queries = {
            'query': f'branch:{self.branch_name}'
        }
        return url

    def file(self, filename: str) -> URL:
        return self.url / filename

    @property
    def commits(self) -> URL:
        return self.repo.url / 'commits' / self.branch_name


def user(username: str, validate: Optional[bool] = None) -> User:
    return User(username=username, validate=validate)

