# Standard libraries
from typing import Optional, Literal
from pathlib import Path
import re

# Non-standard libraries
import pylinks
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

    def graphql_mutation(self, name: str, input: dict, payload: dict = None):
        return request(
            url=self._base / "graphql",
            verb="POST",
            json={"mutation": f"{{{query}}}"},
            headers=self._headers,
            response_type="json",
        )

    def rest_query(
        self,
        query: str,
        verb: Literal["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"] = "GET",
        data=None,
        json=None,
        response_type: Literal["json", "str", "bytes"] | None = "json"
    ):
        return request(
            verb=verb,
            url=self._base / query,
            headers=self._headers,
            data=data,
            json=json,
            response_type=response_type
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

    def _rest_query(
        self,
        query: str = "",
        verb: Literal["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"] = "GET",
        data=None,
        json=None,
        response_type: Literal["json", "str", "bytes"] | None = "json"
    ):
        return self._github.rest_query(
            f"repos/{self._username}/{self._name}/{query}",
            verb=verb,
            data=data,
            json=json,
            response_type=response_type
        )

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

    @property
    def info_pages(self) -> dict:
        """
        Get information about the GitHub Pages site of the repository.

        Returns
        -------
        dict

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/free-pro-team@latest/rest/pages/pages?apiVersion=2022-11-28#create-a-github-pages-site)
        """
        return self._rest_query("pages")

    @property
    def labels(self) -> list[dict]:
        """
        List of all labels for the repository.

        Returns
        -------
        A list of dictionaries with following keys:

        id : int, example: 208045946
        node_id: str, example: MDU6TGFiZWwyMDgwNDU5NDY=
        url: str, example: https://api.github.com/repos/username/repo/labels/bug
        name: str, example: bug
        description: str, example: Something isn't working
        color: str, example: FFFFFF
        default: bool, example: True

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/rest/issues/labels?apiVersion=2022-11-28#list-labels-for-a-repository)
        """
        labels = []
        page = 1
        while True:
            response = self._rest_query(f"labels?per_page=100&page={page}")
            labels.extend(response)
            page += 1
            if len(response) < 100:
                break
        return labels

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

    # def download_content(
    #     self,
    #     path: str = "",
    #     ref: Optional[str] = None,
    #     recursive: bool = True,
    #     download_path: str | Path = ".",
    #     keep_full_path: bool = False,
    # ) -> list[Path]:
    #
    #     def download_file(file_data):
    #         file_content = request(url=file_data["download_url"], response_type="bytes")
    #         full_filepath = Path(file_data["path"])
    #         if keep_full_path:
    #             full_download_path = download_path / full_filepath
    #         else:
    #             rel_path = (
    #                 full_filepath.name if full_filepath == path
    #                 else full_filepath.relative_to(path)
    #             )
    #             full_download_path = download_path / rel_path
    #         full_download_path.parent.mkdir(parents=True, exist_ok=True)
    #         with open(full_download_path, "wb") as f:
    #             f.write(file_content)
    #         final_download_paths.append(full_download_path)
    #         return
    #
    #     def download(content):
    #         if isinstance(content, dict):
    #             # when `path` is a file, GitHub returns a dict instead of a list
    #             content = [content]
    #         if not isinstance(content, list):
    #             raise RuntimeError(f"Unexpected response from GitHub: {content}")
    #         for entry in content:
    #             if entry["type"] == "file":
    #                 download_file(entry)
    #             elif entry["type"] == "dir" and recursive:
    #                 download(self.content(path=entry["path"], ref=ref))
    #         return
    #
    #     download_path = Path(download_path)
    #     final_download_paths = []
    #     download(self.content(path=path, ref=ref))
    #     return final_download_paths

    def download_dir(
        self,
        path: str = "",
        ref: Optional[str] = None,
        recursive: bool = True,
        download_path: str | Path = ".",
        create_dirs: bool = True,
    ) -> list[Path]:

        def download(content):
            if isinstance(content, dict):
                # when `path` is a file, GitHub returns a dict instead of a list
                content = [content]
            if not isinstance(content, list):
                raise RuntimeError(f"Unexpected response from GitHub: {content}")
            for entry in content:
                if entry["type"] == "file":
                    filename = Path(entry["path"]).name
                    full_download_path = download_path / filename
                    pylinks.download(
                        url=entry["download_url"], filepath=full_download_path, create_dirs=create_dirs
                    )
                    final_download_paths.append(full_download_path)
                elif entry["type"] == "dir" and recursive:
                    download(self.content(path=entry["path"], ref=ref))
            return

        download_path = Path(download_path).resolve()
        final_download_paths = []
        dir_content = self.content(path=path, ref=ref)
        if not isinstance(dir_content, list):
            raise ValueError(f"Expected a directory, but got: {dir_content}")
        download(dir_content)
        return final_download_paths

    def download_file(
        self,
        path: str = "",
        ref: Optional[str] = None,
        download_path: str | Path = ".",
        download_filename: str | None = None,
        create_dirs: bool = True,
        overwrite: bool = False,
    ) -> Path:
        content = self.content(path=path, ref=ref)
        # when `path` is a file, GitHub returns a dict instead of a list
        if not isinstance(content, dict) or content["type"] != "file":
            raise ValueError(f"Expected a file, but got: {content}")
        download_path = Path(download_path).resolve()
        if download_filename:
            full_download_path = download_path / download_filename
        else:
            full_download_path = download_path / Path(content["path"]).name
        pylinks.download(
            url=content["download_url"],
            filepath=full_download_path,
            create_dirs=create_dirs,
            overwrite=overwrite,
        )
        return full_download_path

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

    def issue(self, number: int) -> dict:
        return self._rest_query(f"issues/{number}")

    def issue_update(
        self,
        number: int,
        title: str | int | None = None,
        body: str | None = None,
        state: Literal["open", "closed"] | None = None,
        state_reason: Literal["completed", "not_planned", "reopened"] | None = None,
    ):
        """
        Update an issue.

        Parameters
        ----------
        number : int
            Issue number.
        data : dict


        Returns
        -------

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#update-an-issue)
        """
        data = {}
        if title is not None:
            data["title"] = str(title)
        if body is not None:
            data["body"] = str(body)
        if state is not None:
            data["state"] = state
        if state_reason is not None:
            data["state_reason"] = state_reason
        return self._rest_query(f"issues/{number}", verb="PATCH", json=data)

    def issue_add_assignees(self, number: int, assignees: str | list[str]):
        if isinstance(assignees, str):
            assignees = [assignees]
        return self._rest_query(f"issues/{number}/assignees", verb="POST", json={"assignees": assignees})

    def issue_labels(self, number: int) -> list[dict]:
        labels = []
        page = 1
        while True:
            response = self._rest_query(f"issues/{number}/labels?per_page=100&page={page}")
            labels.extend(response)
            page += 1
            if len(response) < 100:
                break
        return labels

    def issue_labels_set(self, number: int, labels: list[str]) -> list[dict]:
        """
        Remove any previous labels and set the new labels for an issue.

        Parameters
        ----------
        number : int
            Issue number.
        labels : list[str]
            List of label names.

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/rest/issues/labels?apiVersion=2022-11-28#set-labels-for-an-issue)
        """
        return self._rest_query(f"issues/{number}/labels", verb="PUT", json={"labels": labels})

    def issue_comments(self, number: int, max_count: int = 1000) -> list[dict]:
        """
        Get a list of comments for an issue/pull request.

        Parameters
        ----------
        number : int
            Issue/pull request number.
        max_count : int, default: 1000
            Maximum number of comments to fetch. The default is 1000, which is the maximum allowed number.

        Returns
        -------
        list[dict]
            A list of comments as dictionaries.
            Comments are ordered by ascending ID.
            For the exact format of the dictionaries, see the GitHub Docs entry in References.

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments)
        """
        comments = []
        page = 1
        while True:
            response = self._rest_query(f"issues/{number}/comments?per_page=100&page={page}")
            comments.extend(response)
            page += 1
            if len(response) < 100 or len(comments) >= max_count:
                break
        return comments

    def issue_comment_create(self, number: int, body: str) -> dict:
        return self._rest_query(f"issues/{number}/comments", verb="POST", json={"body": body})

    def issue_comment_update(self, comment_id: int, body: str) -> dict:
        return self._rest_query(f"issues/comments/{comment_id}", verb="PATCH", json={"body": body})

    def pull_create(
        self,
        head: str,
        base: str,
        title: str = "",
        issue: int = 0,
        body: str = "",
        maintainer_can_modify: bool = True,
        draft: bool = False,
        head_repo: str = ""
    ) -> dict:
        data = {"head": head, "base": base, "maintainer_can_modify": maintainer_can_modify, "draft": draft}
        if not (issue or title):
            raise ValueError("Either 'issue' or 'title' must be specified.")
        if issue:
            data["issue"] = issue
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if head_repo:
            data["head_repo"] = head_repo
        return self._rest_query(query="pulls", verb="POST", json=data)

    def update_settings(self, settings: dict):
        """For settings, see https://docs.github.com/en/free-pro-team@latest/rest/repos/repos?apiVersion=2022-11-28#update-a-repository"""
        return self._rest_query(verb="PATCH", json=settings)

    def replace_topics(self, topics: list[str]):
        topic_pattern = re.compile(r"^[a-z0-9][a-z0-9\-]*$")
        for topic in topics:
            if not isinstance(topic, str):
                raise TypeError(f"Topic must be a string, not {type(topic)}: {topic}.")
            if len(topic) > 50:
                raise ValueError(f"Topic must be 50 characters or less: {topic}.")
            if not topic_pattern.match(topic):
                raise ValueError(f"Topic contains invalid pattern: {topic}.")
        return self._rest_query(query="topics", verb="PUT", json={"names": list(topics)})

    def activate_pages(
        self,
        build_type: Literal['legacy', 'workflow'],
        branch: str | None = None,
        path: Literal['/', '/docs'] = "/"
    ) -> dict:
        """
        Activate GitHub Pages for the repository.

        Parameters
        ----------
        build_type : {'legacy', 'workflow'}
            The process in which the Page will be built.
        branch : str, optional
            The repository branch name used to publish the site's source files.
            This is required when `build_type` is "legacy", and ignored otherwise.
        path : {'/', '/docs'}, default: '/'
            The repository directory that includes the source files for the Pages site.

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/free-pro-team@latest/rest/pages/pages?apiVersion=2022-11-28#create-a-github-pages-site)
        """
        if build_type not in ('legacy', 'workflow'):
            raise ValueError(f"Invalid build type: {build_type}")
        data = {"build_type": build_type}
        if build_type == 'legacy':
            if not branch:
                raise ValueError("Branch must be specified for legacy builds.")
            if path not in ('/', '/docs'):
                raise ValueError("Path must be '/' or '/docs' for legacy builds.")
            data["source"] = {
                "branch": branch,
                "path": path,
            }
        return self._rest_query(query="pages", verb="POST", json=data)

    def label_create(self, name: str, color: str = "", description: str = ""):
        self._validate_label_data(name, color, description)
        data = {"name": name}
        if color:
            data["color"] = color
        if description:
            data["description"] = description
        return self._rest_query(query="labels", verb="POST", json=data)

    def label_delete(self, name: str):
        if not isinstance(name, str):
            raise TypeError(
                f"Invalid input: name='{name}'. "
                f"The label name must be a string, not {type(name)}."
            )
        return self._rest_query(query=f"labels/{name}", verb="DELETE", response_type="str")

    def label_update(self, name: str, new_name: str = "", color: str = "", description: str = ""):
        self._validate_label_data(new_name, color, description)
        if not isinstance(name, str):
            raise TypeError(
                f"Invalid input: name='{name}'. "
                f"The label name must be a string, not {type(name)}."
            )
        data = {}
        if new_name:
            data["new_name"] = new_name
        if color:
            data["color"] = color
        if description:
            data["description"] = description
        if not data:
            raise ValueError("At least one of 'new_name', 'color', or 'description' must be specified.")
        return self._rest_query(query=f"labels/{name}", verb="PATCH", json=data)

    @staticmethod
    def _validate_label_data(name: str, color: str, description: str):
        color_pattern = re.compile(r"^[0-9a-fA-F]{6}$")
        for input_ in (name, color, description):
            if not isinstance(input_, str):
                raise TypeError(f"Input argument '{input_}' must be a string, not {type(input_)}.")
        if color and not color_pattern.match(color):
            raise ValueError(
                f"Invalid input: color='{color}'. "
                "The color must be a hexadecimal string of length 6, without the leading '#'."
            )
        if len(description) > 100:
            raise ValueError(
                f"Invalid input: description='{description}'. "
                "The description must be 100 characters or less."
            )
        return
