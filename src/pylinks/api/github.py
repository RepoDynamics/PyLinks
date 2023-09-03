# Standard libraries
from typing import Optional
from pathlib import Path
import re

# Non-standard libraries
from pylinks import request, url


class GitHub:

    def __init__(self, token: Optional[str] = None):
        self._base = url("https://api.github.com")
        self._token = token
        self._headers = {"X-GitHub-Api-Version": "2022-11-28"}
        if self._token:
            self._headers["Authorization"] = f"Bearer {self._token}"
        return

    def user(self, username) -> "User":
        return User(username=username, token=self._token)

    def graphql_query(self, query):
        return request(
            url=self._base / "graphql",
            verb="POST",
            json={"query": f"{{{query}}}"},
            headers=self._headers,
            response_type="json",
        )

    def rest_query(self, query):
        return request(
            url=self._base / query,
            headers=self._headers,
            response_type="json"
        )

    @property
    def authenticated(self) -> bool:
        return self._token is not None


class User:
    def __init__(self, username: str, token: Optional[str] = None):
        self._username = username
        self._token = token
        self._github = GitHub(token)
        return

    def _rest_query(self, query: str = ""):
        return self._github.rest_query(f"users/{self.username}/{query}")

    @property
    def username(self) -> str:
        return self._username

    @property
    def info(self) -> dict:
        return self._rest_query()

    @property
    def social_accounts(self) -> dict:
        return self._rest_query(f"social_accounts")

    def repo(self, repo_name) -> "Repo":
        return Repo(username=self.username, name=repo_name, token=self._token)


class Repo:
    def __init__(self, username: str, name: str, token: Optional[str] = None):
        self._username = username
        self._name = name
        self._token = token
        self._github = GitHub(token)
        return

    def _rest_query(self, query: str = ""):
        return self._github.rest_query(f"repos/{self._username}/{self._name}/{query}")

    @property
    def username(self) -> str:
        return self._username

    @property
    def name(self) -> str:
        return self._name

    @property
    def info(self) -> dict:
        return self._rest_query()

    @property
    def tags(self) -> list[dict]:
        return self._rest_query(f"git/refs/tags")

    def tag_names(self, pattern: Optional[str] = None) -> list[str | tuple[str, ...]]:
        tags = [tag['ref'].removeprefix("refs/tags/") for tag in self.tags]
        if not pattern:
            return tags
        pattern = re.compile(pattern)
        hits = []
        for tag in tags:
            match = pattern.match(tag)
            if match:
                hits.append(match.groups() or tag)
        return hits

    def content(self, path: str = "", ref: str = None) -> dict:
        return self._rest_query(f"contents/{path.removesuffix('/')}{f'?ref={ref}' if ref else ''}")

    def download_content(
        self,
        path: str = "",
        ref: Optional[str] = None,
        recursive: bool = True,
        download_path: str | Path = ".",
        keep_full_path: bool = False,
    ) -> list[Path]:

        def download_file(file_data):
            file_content = request(url=file_data["download_url"], response_type="bytes")
            full_filepath = Path(file_data["path"])
            if keep_full_path:
                full_download_path = download_path / full_filepath
            else:
                rel_path = (
                    full_filepath.name if full_filepath == download_path
                    else full_filepath.relative_to(download_path)
                )
                full_download_path = download_path / rel_path
            full_download_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_download_path, "wb") as f:
                f.write(file_content)
            final_download_paths.append(full_download_path)
            return

        def download(content):
            if isinstance(content, dict):
                # when `path` is a file, GitHub returns a dict instead of a list
                content = [content]
            if not isinstance(content, list):
                raise RuntimeError(f"Unexpected response from GitHub: {content}")
            for entry in content:
                if entry["type"] == "file":
                    download_file(entry)
                elif entry["type"] == "dir" and recursive:
                    download(self.content(path=entry["path"], ref=ref))
            return

        download_path = Path(download_path)
        final_download_paths = []
        download(self.content(path=path, ref=ref))
        return final_download_paths

    def semantic_versions(self, tag_prefix: str = "v") -> list[tuple[int, int, int]]:
        """
        Get a list of all tags from a GitHub repository that represent SemVer version numbers,
        i.e. 'X.Y.Z' where X, Y, and Z are integers.

        Parameters
        ----------
        tag_prefix : str, default: 'v'
            Prefix of tags to match.

        Returns
        -------
        A sorted list of SemVer version numbers as tuples of integers. For example:
            `[(0, 1, 0), (0, 1, 1), (0, 2, 0), (1, 0, 0), (1, 1, 0)]`
        """
        tags = self.tag_names(pattern=rf"^{tag_prefix}(\d+\.\d+\.\d+)$")
        return sorted([tuple(map(int, tag[0].split("."))) for tag in tags])

    def discussion_categories(self) -> list[dict[str, str]]:
        """Get discussion categories for a repository.

        Parameters
        ----------
        access_token : str
            GitHub access token.

        Returns
        -------
            A list of discussion categories as dictionaries with keys "name", "slug", and "id".

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions)
        -
        """
        query = f"""
            repository(name: "{self._name}", owner: "{self._username}") {{
              discussionCategories(first: 25) {{
                edges {{
                  node {{
                    name
                    slug
                    id
                  }}
                }}
              }}
            }}
        """
        response: dict = self._github.graphql_query(query)
        discussions = [
            entry["node"]
            for entry in response["data"]["repository"]["discussionCategories"]["edges"]
        ]
        return discussions
