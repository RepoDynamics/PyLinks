from typing import Optional
import re

import requests

from pylinks import OFFLINE_MODE as _OFFLINE_MODE
from pylinks import URL


URL_BASE = URL(base='https://github.com')


class User:
    def __init__(self, username: str, validate: Optional[bool] = None):
        if not isinstance(username, str):
            raise TypeError(f"`name` must be a string, not {type(username)}.")
        if re.match(r'^[A-Za-z0-9-]+$', username) is None:
            raise ValueError('GitHub usernames can only contain alphanumeric characters and dashes.')
        self._username = username
        self._url = URL_BASE / username
        if validate is True or (validate is None and not _OFFLINE_MODE):
            requests.get(str(self.url)).raise_for_status()
        return

    @property
    def username(self) -> str:
        return self._username

    @property
    def url(self) -> URL:
        return self._url

    def __str__(self):
        return str(self.url)

    def __repr__(self):
        return f"User(username='{self.username}')"

    def repo(self, repo_name: str, validate: Optional[bool] = None):
        return Repo(user=self, repo_name=repo_name, validate=validate)


def user(username: str, validate: Optional[bool] = None) -> User:
    return User(username=username, validate=validate)


class Repo:
    def __init__(self, user: User, repo_name: str, validate: Optional[bool] = None):
        if not isinstance(user, User):
            raise TypeError("`user` must be a User instance.")
        self._user = user
        if not isinstance(repo_name, str):
            raise TypeError("`name` must be a string.")
        self._repo_name = repo_name
        if re.match(r'^[A-Za-z0-9_.-]+$', repo_name) is None:
            raise ValueError(
                'GitHub repository names can only contain "_", "-", ".", and alphanumeric characters.'
            )
        self._url = self.user.url / repo_name
        if validate is True or (validate is None and not _OFFLINE_MODE):
            requests.get(str(self.url)).raise_for_status()
        return

    @property
    def url(self) -> URL:
        return self._url

    def __str__(self):
        return str(self.url)

    def __repr__(self):
        return f"Repo(user=User(username='{self.user.username}'), repo_name='{self.repo_name}')"

    @property
    def user(self) -> User:
        return self._user

    @property
    def repo_name(self) -> str:
        return self._repo_name

    def workflow(self, filename: str) -> URL:
        return self.url / f'actions/workflows/{filename}'


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
        if validate is True or (validate is None and not _OFFLINE_MODE):
            requests.get(str(self.url)).raise_for_status()
        return

    @property
    def repo(self) -> Repo:
        return self._repo

    @property
    def url(self):
        return self._url

    @property
    def branch_name(self):
        return self._branch_name

    def workflow(self, filename: str) -> URL:
        url = self.repo.url / f'actions/workflows/{filename}'
        url.queries = {
            'query': f'branch:{self.branch_name}'
        }
        return url
