# Standard libraries
from typing import Optional, Literal
from pathlib import Path
import re
import mimetypes

# Non-standard libraries
import pylinks as _pylinks


class GitHub:
    """GitHub API

    References
    ----------
    - [OpenAPI Description](https://github.com/github/rest-api-description)
    - [GraphQL API Documentation](https://docs.github.com/en/graphql)
    """

    def __init__(self, token: Optional[str] = None):
        self._endpoint = {
            "api": _pylinks.url.create("https://api.github.com"),
            "upload": _pylinks.url.create("https://uploads.github.com"),
        }
        self._token = token
        self._headers = {"X-GitHub-Api-Version": "2022-11-28"}
        if self._token:
            self._headers["Authorization"] = f"Bearer {self._token}"
        return

    def user(self, username) -> "User":
        return User(username=username, token=self._token)

    def user_from_id(self, user_id) -> "User":
        user_data = self.rest_query(f"user/{user_id}")
        return User(username=user_data["login"], token=self._token)

    def graphql_query(
        self,
        query: str,
        extra_headers: dict | None = None,
    ) -> dict:
        headers = self._headers | extra_headers if extra_headers else self._headers
        response = _pylinks.http.graphql_query(
            url=self._endpoint["api"] / "graphql",
            query=f"{{{query}}}",
            headers=headers,
        )
        return response

    def graphql_mutation(
        self, mutation_name: str,
        mutation_input_name: str,
        mutation_input: dict,
        mutation_payload: str,
        extra_headers: dict | None = None,
    ):
        headers = self._headers | extra_headers if extra_headers else self._headers
        query = (
            f'mutation($mutationInput:{mutation_input_name}!) '
            f'{{{mutation_name}(input:$mutationInput) {{{mutation_payload}}}}}'
        )
        response = _pylinks.http.graphql_query(
            url=self._endpoint["api"] / "graphql",
            query=query,
            variables={"mutationInput": mutation_input},
            headers=headers,
        )
        return response

    def rest_query(
        self,
        query: str,
        verb: Literal["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"] = "GET",
        data=None,
        json=None,
        response_type: Literal["json", "str", "bytes"] | None = "json",
        extra_headers: dict | None = None,
        endpoint: Literal['api', 'upload'] = "api"
    ):
        headers = self._headers | extra_headers if extra_headers else self._headers
        return _pylinks.http.request(
            verb=verb,
            url=self._endpoint[endpoint] / query,
            headers=headers,
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

    def _rest_query(
        self,
        query: str = "",
        verb: Literal["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"] = "GET",
        data=None,
        json=None,
        response_type: Literal["json", "str", "bytes"] | None = "json",
        extra_headers: dict | None = None,
        endpoint: Literal['api', 'upload'] = "api"
    ):
        query_part = f"/{query}" if query else ""
        return self._github.rest_query(
            query=f"users/{self.username}{query_part}",
            verb=verb,
            data=data,
            json=json,
            response_type=response_type,
            extra_headers=extra_headers,
            endpoint=endpoint
        )

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
        response_type: Literal["json", "str", "bytes"] | None = "json",
        extra_headers: dict | None = None,
        endpoint: Literal['api', 'upload'] = "api"
    ):
        query_part = f"/{query}" if query else ""
        return self._github.rest_query(
            f"repos/{self._username}/{self._name}{query_part}",
            verb=verb,
            data=data,
            json=json,
            response_type=response_type,
            extra_headers=extra_headers,
            endpoint=endpoint
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
    def branches(self) -> list[dict]:
        """
        List of all branches for the repository.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/branches/branches?apiVersion=2022-11-28#list-branches)
        """
        branches = []
        page = 1
        while True:
            response = self._rest_query(f"branches?per_page=100&page={page}")
            branches.extend(response)
            page += 1
            if len(response) < 100:
                break
        return branches

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

    @property
    def pages(self) -> dict:
        """
        Get information about the GitHub Pages site of the repository.

        Returns
        -------
        dict

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/free-pro-team@latest/rest/pages/pages?apiVersion=2022-11-28#get-a-github-pages-site)
        """
        return self._rest_query("pages")

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
                    _pylinks.http.download(
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
        _pylinks.http.download(
            url=content["download_url"],
            filepath=full_download_path,
            create_dirs=create_dirs,
            overwrite=overwrite,
        )
        return full_download_path

    def semantic_versions(self, tag_prefix: str = "v") -> list[str]:
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
        return sorted((tag[0] for tag in tags), key=lambda x: tuple(map(int, x.split("."))))

    def discussion_categories(self) -> list[dict[str, str]]:
        """Get discussion categories for a repository.

        Returns
        -------
            A list of discussion categories as dictionaries with keys "name", "slug", and "id".

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions)
        -
        """
        payload = "{discussionCategories(first: 100) {edges {node {name, slug, id}}}}"
        query = f'repository(name: "{self._name}", owner: "{self._username}") {payload}'
        data = self._github.graphql_query(query)
        discussions = [
            entry["node"]
            for entry in data["repository"]["discussionCategories"]["edges"]
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

    def issue_labels_add(self, number: int, labels: list[str]) -> list[dict]:
        """
        Add labels to an issue.

        Parameters
        ----------
        number : int
            Issue number.
        labels : list[str]
            List of label names. Pass an empty list to remove all labels.

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/rest/issues/labels?apiVersion=2022-11-28#add-labels-to-an-issue)
        """
        return self._rest_query(f"issues/{number}/labels", verb="POST", json={"labels": labels})

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

    def issue_labels_remove(self, number: int, label: str) -> list[dict]:
        """
        Remove a label from an issue.

        Parameters
        ----------
        number : int
            Issue number.
        label : str
            Label name.

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/rest/issues/labels?apiVersion=2022-11-28#remove-a-label-from-an-issue)
        """
        return self._rest_query(f"issues/{number}/labels/{label}", verb="DELETE")

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

    def pull_list(
        self,
        state: Literal["open", "closed", "all"] = "open",
        head: str | None = None,
        base: str | None = None,
        sort: Literal["created", "updated", "popularity", "long-running"] = "created",
        direction: Literal["asc", "desc"] = "desc",
    ) -> list[dict]:
        """
        List of all pull requests for the repository.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests)
        """
        query = f"pulls?state={state}&sort={sort}&direction={direction}&per_page=100"
        if head:
            query += f"&head={head}"
        if base:
            query += f"&base={base}"
        pulls = []
        page = 1
        while True:
            response = self._rest_query(query=f"{query}&page={page}")
            pulls.extend(response)
            page += 1
            if len(response) < 100:
                break
        return pulls

    def pull(self, number: int) -> dict:
        """
        Get details of a pull request.

        Parameters
        ----------
        number : int
            Pull request number.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#get-a-pull-request)
        """
        return self._rest_query(f"pulls/{number}")

    def pull_commits(self, number: int) -> list[dict]:
        """
        Get a list of commits for a pull request.

        Parameters
        ----------
        number : int
            Pull request number.

        Returns
        -------
        list[dict]
            A list of commits as dictionaries.
            Commits are ordered by ascending commit date.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/pulls/commits?apiVersion=2022-11-28#list-commits-on-a-pull-request)
        """
        commits = []
        page = 1
        while True:
            response = self._rest_query(f"pulls/{number}/commits?per_page=100&page={page}")
            commits.extend(response)
            page += 1
            if len(response) < 100:
                break
        return commits

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
        """
        Create a pull request.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request)

        """
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

    def pull_update(
        self,
        number: int,
        title: str | None = None,
        body: str | None = None,
        state: Literal["open", "closed"] | None = None,
        base: str | None = None,
        draft: bool | None = None,
        maintainer_can_modify: bool | None = None,
    ) -> dict:
        """
        Update a pull request.

        Parameters
        ----------
        number : int
            Pull request number.
        title : str, optional
            Title of the pull request.
        body : str, optional
            Body of the pull request.
        state : {'open', 'closed'}, optional
            State of the pull request.
        base : str, optional
            The branch into which the pull request will be merged.
        draft : bool, optional
            Whether the pull request is a draft.
        maintainer_can_modify : bool, optional
            Whether maintainers can modify the pull request.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#update-a-pull-request)
        """
        if draft is not None:
            self._github.graphql_mutation(
                mutation_name="convertPullRequestToDraft" if draft else "markPullRequestReadyForReview",
                mutation_input_name="ConvertPullRequestToDraftInput" if draft else "MarkPullRequestReadyForReviewInput",
                mutation_input={"pullRequestId": self.pull(number=number)["node_id"]},
                mutation_payload="pullRequest {isDraft}"
            )
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if base is not None:
            data["base"] = base
        if maintainer_can_modify is not None:
            data["maintainer_can_modify"] = maintainer_can_modify
        return self._rest_query(query=f"pulls/{number}", verb="PATCH", json=data)

    def pull_branch_update(self, number: int, head_sha: str):
        """
        Updates the pull request branch with the latest upstream changes
        by merging HEAD from the base branch into the pull request branch.

        Parameters
        ----------
        number : int
            Pull request number.
        head_sha : str, optional
            The expected SHA of the pull request's HEAD ref.
            This is the most recent commit on the pull request's branch.
            If the expected SHA does not match the pull request's HEAD,
            you will receive a 422 Unprocessable Entity status.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#update-a-pull-request-branch)
        """
        return self._rest_query(
            query=f"pulls/{number}/update-branch", verb="PUT", json={"expected_head_sha": head_sha}
        )

    def pull_merge(
        self,
        number: int,
        commit_title: str | None = None,
        commit_message: str | None = None,
        sha: str | None = None,
        merge_method: Literal['merge', 'squash', 'rebase'] | None = None,
    ):
        """
        Merge a pull request into the base branch.

        Parameters
        ----------
        number : int
            Pull request number.
        commit_title : str, optional
            Title for the merge commit. If omitted, the default commit title is used.
        commit_message : str, optional
            Message for the merge commit. If omitted, the default commit message is used.
        sha : str, optional
            SHA that pull request head must match to allow merge.
        merge_method : {'merge', 'squash', 'rebase'}, optional
            Merge method to use. If omitted, the default merge method is used.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#merge-a-pull-request)
        """
        data = {}
        if commit_title is not None:
            data["commit_title"] = commit_title
        if commit_message is not None:
            data["commit_message"] = commit_message
        if sha is not None:
            data["sha"] = sha
        if merge_method is not None:
            data["merge_method"] = merge_method
        return self._rest_query(query=f"pulls/{number}/merge", verb="PUT", json=data if data else None)

    def repo_update(
        self,
        name: str | None = None,
        description: str | None = None,
        homepage: str | None = None,
        visibility: Literal['public', 'private'] | None = None,
        advanced_security: bool | None = None,
        secret_scanning: bool | None = None,
        secret_scanning_push_protection: bool | None = None,
        has_issues: bool | None = None,
        has_discussions: bool | None = None,
        has_projects: bool | None = None,
        has_wiki: bool | None = None,
        is_template: bool | None = None,
        default_branch: str | None = None,
        allow_squash_merge: bool | None = None,
        allow_merge_commit: bool | None = None,
        allow_rebase_merge: bool | None = None,
        allow_auto_merge: bool | None = None,
        delete_branch_on_merge: bool | None = None,
        allow_update_branch: bool | None = None,
        squash_merge_commit_title: Literal['PR_TITLE', 'COMMIT_OR_PR_TITLE'] | None = None,
        squash_merge_commit_message: Literal['PR_BODY', 'COMMIT_MESSAGES', 'BLANK'] | None = None,
        merge_commit_title: Literal['PR_TITLE', 'MERGE_MESSAGE'] | None = None,
        merge_commit_message: Literal['PR_BODY', 'PR_TITLE', 'BLANK'] | None = None,
        archived: bool | None = None,
        allow_forking: bool | None = None,
        web_commit_signoff_required: bool | None = None,
        automated_security_fixes: bool | None = None,
        private_vulnerability_reporting: bool | None = None,
        vulnerability_alerts: bool | None = None,
    ) -> dict:
        """
        Update repository settings.

        References
        ----------
        - [GitHub API Docs: updating a repository](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#update-a-repository)
        - [GitHub API Docs: automated security fixes](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#enable-automated-security-fixes)
        - [GitHub API Docs: private vulnerability reporting](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#enable-private-vulnerability-reporting-for-a-repository)
        - [GitHub API Docs: vulnerability alerts](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#enable-vulnerability-alerts)
        """
        data = locals()
        data.pop("self")
        output = {}

        has_discussions = data.pop("has_discussions")
        if has_discussions is not None:
            out = self._github.graphql_mutation(
                mutation_name="updateRepository",
                mutation_input_name="UpdateRepositoryInput",
                mutation_input={
                    "hasDiscussionsEnabled": has_discussions,
                    "repositoryId": self.info["node_id"]
                },
                mutation_payload="repository {hasDiscussionsEnabled}"
            )
            output["hasDiscussionsEnabled"] = out['updateRepository']['repository']['hasDiscussionsEnabled']

        private_vulnerability_reporting = data.pop("private_vulnerability_reporting")
        if private_vulnerability_reporting is not None:
            self._rest_query(
                query="private-vulnerability-reporting",
                verb="PUT" if private_vulnerability_reporting else "DELETE",
                response_type="str"
            )

        vulnerability_alerts = data.pop("vulnerability_alerts")
        if vulnerability_alerts is not None:
            self._rest_query(
                query="vulnerability-alerts",
                verb="PUT" if vulnerability_alerts else "DELETE",
                response_type="str"
            )

        automated_security_fixes = data.pop("automated_security_fixes")
        if automated_security_fixes is not None:
            self._rest_query(
                query="automated-security-fixes",
                verb="PUT" if automated_security_fixes else "DELETE",
                response_type="str"
            )

        security_and_analysis = {}
        for arg_name, target_name in (
            ("advanced_security", "advanced_security"),
            ("secret_scanning", "secret_scanning"),
            ("secret_scanning_push_protection", "secret_scanning_push_protection"),
        ):
            arg = data.pop(arg_name)
            if arg is not None:
                security_and_analysis[target_name] = {"status": 'enabled' if arg else 'disabled'}
        if security_and_analysis:
            data["security_and_analysis"] = security_and_analysis

        final_data = {k: v for k, v in data.items() if v is not None}
        if final_data:
            output = self._rest_query(verb="PATCH", json=final_data)
        return output

    def repo_topics_replace(self, topics: list[str]):
        """Replace all repository topics.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#replace-all-repository-topics)
        """
        topic_pattern = re.compile(r"^[a-z0-9][a-z0-9\-]*$")
        for topic in topics:
            if not isinstance(topic, str):
                raise TypeError(f"Topic must be a string, not {type(topic)}: {topic}.")
            if len(topic) > 50:
                raise ValueError(f"Topic must be 50 characters or less: {topic}.")
            if not topic_pattern.match(topic):
                raise ValueError(f"Topic contains invalid pattern: {topic}.")
        return self._rest_query(query="topics", verb="PUT", json={"names": list(topics)})

    def pages_create(
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

    def pages_update(
        self,
        cname: str | None = None,
        https_enforced: bool | None = None,
        build_type: Literal['legacy', 'workflow'] | None = None,
        branch: str | None = None,
        path: Literal['/', '/docs'] = "/",
    ) -> None:
        """
        Update GitHub Pages settings for the repository.

        Parameters
        ----------
        cname : str, optional
            The custom domain for the Pages site.
            To remove the current custom domain, set this to an empty string.
        https_enforced : bool, optional
            Whether to enforce HTTPS for the Pages site.
        build_type : {'legacy', 'workflow'}, optional
            The process in which the Page will be built.
        branch : str, optional
            The repository branch name used to publish the site's source files.
            This is required when `build_type` is "legacy", and ignored otherwise.
        path : {'/', '/docs'}, default: '/'
            The repository directory that includes the source files for the Pages site.

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/free-pro-team@latest/rest/pages/pages?apiVersion=2022-11-28#update-information-about-a-github-pages-site)
        """
        data = {}
        if cname is not None:
            data["cname"] = cname if cname else None
        if https_enforced is not None:
            data["https_enforced"] = https_enforced
        if build_type is not None:
            if build_type not in ('legacy', 'workflow'):
                raise ValueError(f"Invalid build type: {build_type}")
            data["build_type"] = build_type
        if build_type == 'legacy':
            if not branch:
                raise ValueError("Branch must be specified for legacy builds.")
            if path not in ('/', '/docs'):
                raise ValueError("Path must be '/' or '/docs' for legacy builds.")
            data["source"] = {
                "branch": branch,
                "path": path,
            }
        self._rest_query(query="pages", verb="PUT", json=data, response_type="str")
        return

    def pages_delete(self):
        return self._rest_query(query="pages", verb="DELETE", response_type="str")

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

    def release_create(
        self,
        tag_name: str,
        name: str,
        body: str,
        target_commitish: str = "",
        draft: bool = False,
        prerelease: bool = False,
        discussion_category_name: str = "",
        generate_release_notes: bool = False,
        make_latest: Literal['true', 'false', 'legacy'] = 'true'
    ):
        """
        Create a new release.

        Parameters
        ----------
        tag_name : str
            The name of the tag.
        name : str
            The name of the release.
        body : str
            The body of the release post, i.e. text describing the release.
        target_commitish : str, optional
            The commitish value that determines where the Git tag is created from.
            Can be any branch or commit SHA. Unused if the Git tag already exists.
            The default is the repository's default branch.
        draft : bool, default: False
            `True` to create a draft (unpublished) release, `False` to create a published one.
        prerelease : bool, default: False
            `True` to identify the release as a prerelease, `False` to identify it as a full release.
        discussion_category_name : str, optional
            The name of the discussion category for the release, to be created and linked to the release.
            The value must be a category that already exists in the repository.
        generate_release_notes : bool, default: False
            Whether to automatically generate the name and body for the release.
            If `name` is specified, it will be used, otherwise a name will be automatically generated.
            If `body` is specified, it will be prepended to the automatically generated body.
        make_latest : {'true', 'false', 'legacy'}, default: 'true'
            Whether this release should be set as the latest release for the repository.
            Drafts and prereleases cannot be set as latest.
            Defaults to 'true' for newly published releases.
            'legacy' specifies that the latest release should be determined based on
            the release creation date and higher semantic version.

        References
        ----------
        [GitHub API Docs](https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#create-a-release)
        """
        data = {
            "tag_name": tag_name,
            "draft": draft,
            "prerelease": prerelease,
            "generate_release_notes": generate_release_notes,
            "make_latest": make_latest,
        }
        if name:
            data["name"] = name
        if body:
            data["body"] = body
        if target_commitish:
            data["target_commitish"] = target_commitish
        if discussion_category_name:
            data["discussion_category_name"] = discussion_category_name
        return self._rest_query(query="releases", verb="POST", json=data)

    def release_asset_upload(
        self,
        release_id: int,
        filepath: str | Path,
        mime_type: str = "",
        label: str = "",
    ) -> dict:
        """
        Upload a file as an asset to a release.

        Parameters
        ----------
        release_id : int
            ID of the release.
        filepath : str | pathlib.Path
            Path to the file to upload.
        mime_type : str, optional
            MIME type of the file. If not specified, it will be guessed from the file extension.
        label : str, optional
            Label for the uploaded file to display on GitHub UI instead of the actual filename.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/releases/assets?apiVersion=2022-11-28#upload-a-release-asset)
        - [List of MIME types](https://www.iana.org/assignments/media-types/media-types.xhtml)
        """
        filepath = Path(filepath).resolve()
        if not filepath.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")
        if not mime_type:
            mime_type = mimetypes.guess_type(filepath)[0]
            if not mime_type:
                raise RuntimeError(
                    f"Could not guess MIME type of file '{filepath}'. Please provide it as input argument."
                )
        headers = {"Content-Type": mime_type}
        query = f"releases/{release_id}/assets?name={filepath.name}"
        if label:
            query += f"&label={label}"
        return self._rest_query(
            query=query,
            verb="POST",
            data=filepath.read_bytes(),
            extra_headers=headers,
            endpoint="upload"
        )

    def rulesets(self, include_parents: bool = True) -> list[dict]:
        """
        List of all rulesets for the repository.

        References
        ----------
        - [GitHub Docs](https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28#get-all-repository-rulesets)
        """
        rulesets = []
        page = 1
        while True:
            response = self._rest_query(
                f"rulesets?per_page=100&page={page}&includes_parents={'true' if include_parents else 'false'}"
            )
            rulesets.extend(response)
            page += 1
            if len(response) < 100:
                break
        return rulesets

    def ruleset_create(
        self,
        name: str,
        target: Literal['branch', 'tag'] = "branch",
        enforcement: Literal['disabled', 'evaluate', 'active'] = 'active',
        bypass_actors: list[
           tuple[int, Literal['OrganizationAdmin', 'RepositoryRole', 'Team', 'Integration'], bool]
        ] | None = None,
        ref_name_include: list[str] | None = None,
        ref_name_exclude: list[str] | None = None,
        creation: bool = False,
        update: bool = False,
        update_allows_fetch_and_merge: bool = True,
        deletion: bool = False,
        required_linear_history: bool = False,
        required_deployment_environments: list[str] | None = None,
        required_signatures: bool = False,
        required_pull_request: bool = False,
        dismiss_stale_reviews_on_push: bool = False,
        require_code_owner_review: bool = False,
        require_last_push_approval: bool = False,
        required_approving_review_count: int = 0,
        required_review_thread_resolution: bool = False,
        required_status_checks: list[tuple[str, int] | str] | None = None,
        strict_required_status_checks_policy: bool = False,
        non_fast_forward: bool = False,
    ) -> dict:
        """
        Create a new ruleset.

        Parameters
        ----------
        name : str
            The name of the ruleset.
        target : {'branch', 'tag'}, default: 'branch'
            The target for the ruleset.
        enforcement : {'disabled', 'evaluate', 'active'}, default: 'active'
            The enforcement level for the ruleset.
            'evaluate' (only available with GitHub Enterprise) allows admins
            to test rules before enforcing them.
            Admins can then view insights on the Rule Insights page.
        bypass_actors : list[tuple[int, {'OrganizationAdmin', 'RepositoryRole', 'Team', 'Integration'}, bool]], optional
            A list of tuples of (actor ID, actor type, always bypass):
            - actor ID: The ID of the actor that can bypass a ruleset.
              If actor type is 'OrganizationAdmin', this should be 1.
            - actor type: The type of the actor that can bypass a ruleset.
              Can be one of 'OrganizationAdmin', 'RepositoryRole', 'Team', or 'Integration'.
            - always bypass: Whether the actor can always bypass the ruleset (True) or only on pull requests (False).
        ref_name_include : list[str], optional
            A list of ref names or patterns to include.
            One of these patterns must match for the condition to pass.
            Also accepts '~DEFAULT_BRANCH' to include the default branch
            or '~ALL' to include all branches.
        ref_name_exclude : list[str], optional
            A list of ref names or patterns to exclude.
            The condition will not pass if any of these patterns match.
        creation : bool, default: False
            Only allow users with bypass permission to create matching refs.
        update : bool, default: False
            Only allow users with bypass permission to update matching refs.
        update_allows_fetch_and_merge : bool, default: True
            Whether the branch can still pull changes from its upstream repository
            even when `update` is set to True.
        deletion : bool, default: False
            Only allow users with bypass permissions to delete matching refs.
        required_linear_history : bool, default: False
            Prevent merge commits from being pushed to matching refs.
        required_deployment_environments : list[str], optional
            A list of environments that must be successfully deployed to before branches can be merged.
        required_signatures : bool, default: False
            Commits pushed to matching refs must have verified signatures.
        required_pull_request : bool, default: False
            Require all commits be made to a non-target branch
            and submitted via a pull request before they can be merged.
        dismiss_stale_reviews_on_push : bool, default: False
            New, reviewable commits pushed will dismiss previous pull request review approvals.
        require_code_owner_review : bool, default: False
            Require an approving review in pull requests that modify files that have a designated code owner.
        require_last_push_approval : bool, default: False
            Whether the most recent reviewable push must be approved by someone other than the person who pushed it.
        required_approving_review_count : int, default: 0
            The number of approving reviews that are required before a pull request can be merged.
        required_review_thread_resolution : bool, default: False
            All conversations on code must be resolved before a pull request can be merged.
        required_status_checks : list[tuple[str, int] | str], optional
            A list of status checks that must pass before a pull request can be merged.
            Each element can either be a string with the name of the status check context,
            or a tuple of (name, integration ID).
        strict_required_status_checks_policy : bool, default: False
            Whether pull requests targeting a matching branch must be tested with the latest code.
            This setting will not take effect unless at least one status check is enabled.
        non_fast_forward : bool, default: False
            Prevent users with push access from force pushing to refs.

    References
    ----------
    - [GitHub API Docs](https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28#create-a-repository-ruleset)
    """
        data = {"name": name, "target": target, "enforcement": enforcement}
        if bypass_actors:
            data["bypass_actors"] = [
                {
                    "actor_id": actor_id,
                    "actor_type": actor_type,
                    "bypass_mode": 'always' if always_bypass else 'pull_request'
                } for actor_id, actor_type, always_bypass in bypass_actors
            ]
        if ref_name_include or ref_name_exclude:
            data["conditions"] = {
                "ref_name": {
                    "include": ref_name_include or [],
                    "exclude": ref_name_exclude or []
                }
            }
        rules = []
        if creation:
            rules.append({"type": "creation"})
        if update:
            rules.append(
                {
                    "type": "update",
                    "parameters": {"update_allows_fetch_and_merge": update_allows_fetch_and_merge}
                }
            )
        if deletion:
            rules.append({"type": "deletion"})
        if required_linear_history:
            rules.append({"type": "required_linear_history"})
        if required_deployment_environments:
            rules.append(
                {
                    "type": "required_deployments",
                    "parameters": {"required_deployment_environments": required_deployment_environments}
                }
            )
        if required_signatures:
            rules.append({"type": "required_signatures"})
        if required_pull_request:
            rules.append(
                {
                    "type": "pull_request",
                    "parameters": {
                        "dismiss_stale_reviews_on_push": dismiss_stale_reviews_on_push,
                        "require_code_owner_review": require_code_owner_review,
                        "require_last_push_approval": require_last_push_approval,
                        "required_approving_review_count": required_approving_review_count,
                        "required_review_thread_resolution": required_review_thread_resolution,
                    }
                }
            )
        if required_status_checks:
            rules.append(
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "required_status_checks": [
                            {"context": required_status_check} if isinstance(required_status_check, str)
                            else {
                                "context": required_status_check[0],
                                "integration_id": required_status_check[1]
                            } for required_status_check in required_status_checks
                        ],
                        "strict_required_status_checks_policy": strict_required_status_checks_policy,
                    }
                }
            )
        if non_fast_forward:
            rules.append({"type": "non_fast_forward"})
        if rules:
            data["rules"] = rules
        return self._rest_query(query="rulesets", verb="POST", json=data)

    def ruleset_update(
        self,
        ruleset_id: int,
        name: str | None = None,
        target: Literal['branch', 'tag'] | None = None,
        enforcement: Literal['disabled', 'evaluate', 'active'] | None = None,
        bypass_actors: list[
           tuple[int, Literal['OrganizationAdmin', 'RepositoryRole', 'Team', 'Integration'], bool]
        ] | None = None,
        ref_name_include: list[str] | None = None,
        ref_name_exclude: list[str] | None = None,
        creation: bool | None = None,
        update: bool | None = None,
        update_allows_fetch_and_merge: bool | None = None,
        deletion: bool | None = None,
        required_linear_history: bool | None = None,
        required_deployment_environments: list[str] | None = None,
        required_signatures: bool | None = None,
        required_pull_request: bool | None = None,
        dismiss_stale_reviews_on_push: bool | None = None,
        require_code_owner_review: bool | None = None,
        require_last_push_approval: bool | None = None,
        required_approving_review_count: int | None = None,
        required_review_thread_resolution: bool | None = None,
        require_status_checks: bool | None = None,
        required_status_checks: list[tuple[str, int] | str] | None = None,
        strict_required_status_checks_policy: bool | None = None,
        non_fast_forward: bool | None = None,
    ) -> dict:
        """
        Update a ruleset.

        Parameters
        ----------
        ruleset_id : int
            The ID of the ruleset.
        name : str, optional
            The name of the ruleset.
        target : {'branch', 'tag'}, optional
            The target for the ruleset.
        enforcement : {'disabled', 'evaluate', 'active'}, optional
            The enforcement level for the ruleset.
            'evaluate' (only available with GitHub Enterprise) allows admins
            to test rules before enforcing them.
            Admins can then view insights on the Rule Insights page.
        bypass_actors : list[tuple[int, {'OrganizationAdmin', 'RepositoryRole', 'Team', 'Integration'}, bool]], optional
            A list of tuples of (actor ID, actor type, always bypass):
            - actor ID: The ID of the actor that can bypass a ruleset.
              If actor type is 'OrganizationAdmin', this should be 1.
            - actor type: The type of the actor that can bypass a ruleset.
              Can be one of 'OrganizationAdmin', 'RepositoryRole', 'Team', or 'Integration'.
            - always bypass: Whether the actor can always bypass the ruleset (True) or only on pull requests (False).
        ref_name_include : list[str], optional
            A list of ref names or patterns to include.
            One of these patterns must match for the condition to pass.
            Also accepts '~DEFAULT_BRANCH' to include the default branch
            or '~ALL' to include all branches.
        ref_name_exclude : list[str], optional
            A list of ref names or patterns to exclude.
            The condition will not pass if any of these patterns match.
        creation : bool, optional
            Only allow users with bypass permission to create matching refs.
        update : bool, optional
            Only allow users with bypass permission to update matching refs.
        update_allows_fetch_and_merge : bool, optional
            Whether the branch can still pull changes from its upstream repository
            even when `update` is set to True.
        deletion : bool, optional
            Only allow users with bypass permissions to delete matching refs.
        required_linear_history : bool, optional
            Prevent merge commits from being pushed to matching refs.
        required_deployment_environments : list[str], optional
            A list of environments that must be successfully deployed to before branches can be merged.
        required_signatures : bool, optional
            Commits pushed to matching refs must have verified signatures.
        required_pull_request : bool, optional
            Require all commits be made to a non-target branch
            and submitted via a pull request before they can be merged.
        dismiss_stale_reviews_on_push : bool, optional
            New, reviewable commits pushed will dismiss previous pull request review approvals.
        require_code_owner_review : bool, optional
            Require an approving review in pull requests that modify files that have a designated code owner.
        require_last_push_approval : bool, optional
            Whether the most recent reviewable push must be approved by someone other than the person who pushed it.
        required_approving_review_count : int, optional
            The number of approving reviews that are required before a pull request can be merged.
        required_review_thread_resolution : bool, optional
            All conversations on code must be resolved before a pull request can be merged.
        require_status_checks : bool, optional
            Whether to require status checks to pass before merging for matching branches.
        required_status_checks : list[tuple[str, int] | str], optional
            A list of status checks that must pass before a pull request can be merged.
            Each element can either be a string with the name of the status check context,
            or a tuple of (name, integration ID).
        strict_required_status_checks_policy : bool, optional
            Whether pull requests targeting a matching branch must be tested with the latest code.
            This setting will not take effect unless at least one status check is enabled.
        non_fast_forward : bool, optional
            Prevent users with push access from force pushing to refs.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28#update-a-repository-ruleset)
        """
        data = {}
        if name is not None:
            data["name"] = name
        if target is not None:
            data["target"] = target
        if enforcement is not None:
            data["enforcement"] = enforcement
        if bypass_actors is not None:
            data["bypass_actors"] = [
                {
                    "actor_id": actor_id,
                    "actor_type": actor_type,
                    "bypass_mode": 'always' if always_bypass else 'pull_request'
                } for actor_id, actor_type, always_bypass in bypass_actors
            ]
        if ref_name_include is not None:
            data["conditions"] = {
                "ref_name": {"include": ref_name_include}
            }
        if ref_name_exclude is not None:
            ref_name_conditions = data.setdefault("conditions", {}).setdefault("ref_name", {})
            ref_name_conditions["exclude"] = ref_name_exclude
        rules = []
        update_rules = False
        if creation is not None:
            if creation:
                rules.append({"type": "creation"})
            else:
                update_rules = True
        if update is not None:
            if update:
                obj = {"type": "update"}
                if update_allows_fetch_and_merge is not None:
                    obj["parameters"] = {"update_allows_fetch_and_merge": update_allows_fetch_and_merge}
            else:
                update_rules = True
        if deletion is not None:
            if deletion:
                rules.append({"type": "deletion"})
            else:
                update_rules = True
        if required_linear_history is not None:
            if required_linear_history:
                rules.append({"type": "required_linear_history"})
            else:
                update_rules = True
        if required_deployment_environments is not None:
            if required_deployment_environments:
                rules.append(
                    {
                        "type": "required_deployments",
                        "parameters": {
                            "required_deployment_environments": required_deployment_environments
                        }
                    }
                )
            else:
                update_rules = True
        if required_signatures is not None:
            if required_signatures:
                rules.append({"type": "required_signatures"})
            else:
                update_rules = True
        if required_pull_request is not None:
            if required_pull_request:
                obj = {"type": "pull_request"}
                if dismiss_stale_reviews_on_push is not None:
                    obj["parameters"] = {"dismiss_stale_reviews_on_push": dismiss_stale_reviews_on_push}
                if require_code_owner_review is not None:
                    params = obj.setdefault("parameters", {})
                    params["require_code_owner_review"] = require_code_owner_review
                if require_last_push_approval is not None:
                    params = obj.setdefault("parameters", {})
                    params["require_last_push_approval"] = require_last_push_approval
                if required_approving_review_count is not None:
                    params = obj.setdefault("parameters", {})
                    params["required_approving_review_count"] = required_approving_review_count
                if required_review_thread_resolution is not None:
                    params = obj.setdefault("parameters", {})
                    params["required_review_thread_resolution"] = required_review_thread_resolution
                rules.append(obj)
            else:
                update_rules = True
        if require_status_checks is not None:
            if require_status_checks:
                obj = {"type": "required_status_checks"}
                if required_status_checks is not None:
                    params = obj.setdefault("parameters", {})
                    params["required_status_checks"] = [
                        {"context": required_status_check} if isinstance(required_status_check, str)
                        else {
                            "context": required_status_check[0],
                            "integration_id": required_status_check[1]
                        } for required_status_check in required_status_checks
                    ]
                if strict_required_status_checks_policy is not None:
                    params = obj.setdefault("parameters", {})
                    params["strict_required_status_checks_policy"] = strict_required_status_checks_policy
            else:
                update_rules = True
        if non_fast_forward is not None:
            if non_fast_forward:
                rules.append({"type": "non_fast_forward"})
            else:
                update_rules = True
        if update_rules:
            data["rules"] = rules
        if not data:
            raise ValueError("At least one of the ruleset parameters must be specified.")
        return self._rest_query(query=f"rulesets/{ruleset_id}", verb="PUT", json=data)

    def ruleset_delete(self, ruleset_id: int) -> None:
        """
        Delete a ruleset.

        Parameters
        ----------
        ruleset_id : int
            The ID of the ruleset.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/repos/rules?apiVersion=2022-11-28#delete-a-repository-ruleset)
        """
        self._rest_query(query=f"rulesets/{ruleset_id}", verb="DELETE")
        return

    def actions_permissions_workflow_default(self) -> dict:
        """
        Get default workflow permissions granted to the GITHUB_TOKEN when running workflows in the repository,
        as well as whether GitHub Actions can submit and approve pull request reviews.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/actions/permissions?apiVersion=2022-11-28#get-default-workflow-permissions-for-a-repository)
        """
        return self._rest_query(query="actions/permissions/workflow")

    def actions_permissions_workflow_default_set(
        self,
        permissions: Literal['read', 'write'] | None = None,
        can_approve_pull_requests: bool | None = None
    ) -> None:
        """
        Set default workflow permissions granted to the GITHUB_TOKEN when running workflows in the repository,
        as well as whether GitHub Actions can submit and approve pull request reviews.

        Parameters
        ----------
        permissions : {'read', 'write'}, optional
            The default permissions granted to the GITHUB_TOKEN when running workflows in the repository.
        can_approve_pull_requests : bool, optional
            Whether GitHub Actions can submit and approve pull request reviews.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/rest/actions/permissions?apiVersion=2022-11-28#set-default-workflow-permissions-for-a-repository)
        """
        data = {}
        if permissions is not None:
            data["default_workflow_permissions"] = permissions
        if can_approve_pull_requests is not None:
            data["can_approve_pull_request_reviews"] = can_approve_pull_requests
        if not data:
            raise ValueError("At least one of 'permissions' or 'can_approve_pull_requests' must be specified.")
        self._rest_query(query="actions/permissions/workflow", verb="PUT", json=data, response_type="str")
        return

    def branch_create_linked(
        self,
        issue_id: str | int,
        base_sha: str,
        name: str | None = None,
        repository_id: str | int | None = None
    ) -> dict[str, str]:
        """
        Create a branch linked to an issue.

        Parameters
        ----------
        issue_id : str | int
            ID of the issue.
        base_sha : str
            Commit SHA to base the new branch on.
        name : str, optional
            Name of the new branch. If not specified, defaults to issue number and title.
        repository_id : str | int, optional
            ID of the repository to create the branch in. If not specified, defaults to the issue repository.

        Returns
        -------
        dict[str, str]
            A dictionary with keys 'name' and 'sha', corresponding to the name and latest commit SHA of
            the created branch.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/graphql/reference/mutations#createlinkedbranch)
        """
        args = locals()
        args.pop("self")
        input_map = {
            "issue_id": "issueId",
            "base_sha": "oid",
            "name": "name",
            "repository_id": "repositoryId",
        }
        inputs = {input_map[k]: v for k, v in args.items() if v is not None}
        data = self._github.graphql_mutation(
            mutation_name="createLinkedBranch",
            mutation_input_name="CreateLinkedBranchInput",
            mutation_input=inputs,
            mutation_payload="linkedBranch {ref {name target {oid}}}"
        )
        out = data["createLinkedBranch"]["linkedBranch"]["ref"]
        return {"name": out["name"], "sha": out["target"]["oid"]}

    def branch_rename(self, old_name: str, new_name: str) -> dict:
        """
        Rename a branch.

        Parameters
        ----------
        old_name : str
            Old branch name.
        new_name : str
            New branch name.

        Returns
        -------

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/graphql/reference/mutations#renameref)
        """
        return self._rest_query(query=f"branches/{old_name}/rename", verb="POST", json={"new_name": new_name})

    def branch_protection_rules(self) -> list[dict]:
        """
        Get the branch protection rules for the repository.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/graphql/reference/objects#branchprotectionruleconnection)
        """
        payload = "{branchProtectionRules(first: 100) {nodes {id, pattern}}}"
        query = f'repository(name: "{self._name}", owner: "{self._username}") {payload}'
        data = self._github.graphql_query(query)
        return data["repository"]["branchProtectionRules"]["nodes"]

    def branch_protection_rule_create(
        self,
        pattern: str,
        allow_deletions: bool | None = None,
        allow_force_pushes: bool | None = None,
        block_creations: bool | None = None,
        dismiss_stale_reviews: bool | None = None,
        require_approving_reviews: bool | None = None,
        require_last_push_approval: bool | None = None,
        require_codeowner_reviews: bool | None = None,
        require_commit_signatures: bool | None = None,
        require_conversation_resolution: bool | None = None,
        require_deployments: bool | None = None,
        require_linear_history: bool | None = None,
        require_status_checks: bool | None = None,
        require_status_checks_strict: bool | None = None,
        restrict_push: bool | None = None,
        restrict_review_dismissals: bool | None = None,
        enforce_admins: bool | None = None,
        lock_branch: bool | None = None,
        lock_allows_fetch_and_merge: bool | None = None,
        required_approving_review_count: int | None = None,
        required_deployment_environments: list[str] | None = None,
        required_status_check_contexts: list[str] | None = None,
        push_actor_ids: list[str] | None = None,
        bypass_force_push_actor_ids: list[str] | None = None,
        bypass_pull_request_actor_ids: list[str] | None = None,
        review_dismissal_actor_ids: list[str] | None = None,
    ):
        """
        Create a branch protection rule.

        References
        ----------
        - [GitHub API Docs](https://docs.github.com/en/graphql/reference/mutations#createbranchprotectionrule)
        """
        args = locals()
        args.pop("self")
        inputs = self._prepare_branch_protection_rule_input(args)
        inputs["repositoryId"] = self.info["node_id"]
        data = self._github.graphql_mutation(
            mutation_name="createBranchProtectionRule",
            mutation_input_name="CreateBranchProtectionRuleInput",
            mutation_input=inputs,
            mutation_payload="branchProtectionRule {id}",
        )
        return data["createBranchProtectionRule"]["branchProtectionRule"]["id"]

    def branch_protection_rule_update(
        self,
        rule_id: str,
        pattern: str | None = None,
        allow_deletions: bool | None = None,
        allow_force_pushes: bool | None = None,
        block_creations: bool | None = None,
        dismiss_stale_reviews: bool | None = None,
        require_approving_reviews: bool | None = None,
        require_last_push_approval: bool | None = None,
        require_codeowner_reviews: bool | None = None,
        require_commit_signatures: bool | None = None,
        require_conversation_resolution: bool | None = None,
        require_deployments: bool | None = None,
        require_linear_history: bool | None = None,
        require_status_checks: bool | None = None,
        require_status_checks_strict: bool | None = None,
        restrict_push: bool | None = None,
        restrict_review_dismissals: bool | None = None,
        enforce_admins: bool | None = None,
        lock_branch: bool | None = None,
        lock_allows_fetch_and_merge: bool | None = None,
        required_approving_review_count: int | None = None,
        required_deployment_environments: list[str] | None = None,
        required_status_check_contexts: list[str] | None = None,
        push_actor_ids: list[str] | None = None,
        bypass_force_push_actor_ids: list[str] | None = None,
        bypass_pull_request_actor_ids: list[str] | None = None,
        review_dismissal_actor_ids: list[str] | None = None,
    ):
        args = locals()
        args.pop("self")
        inputs = self._prepare_branch_protection_rule_input(args)
        data = self._github.graphql_mutation(
            mutation_name="updateBranchProtectionRule",
            mutation_input_name="UpdateBranchProtectionRuleInput",
            mutation_input=inputs,
            mutation_payload="branchProtectionRule {id}",
        )
        return data["updateBranchProtectionRule"]["branchProtectionRule"]["id"]

    def _prepare_branch_protection_rule_input(self, kwargs: dict):
        arg_map = {
            "rule_id": "branchProtectionRuleId",
            "pattern": "pattern",
            "allow_deletions": "allowsDeletions",
            "allow_force_pushes": "allowsForcePushes",
            "block_creations": "blocksCreations",
            "bypass_force_push_actor_ids": "bypassForcePushActorIds",
            "bypass_pull_request_actor_ids": "bypassPullRequestActorIds",
            "dismiss_stale_reviews": "dismissesStaleReviews",
            "enforce_admins": "isAdminEnforced",
            "lock_allows_fetch_and_merge": "lockAllowsFetchAndMerge",
            "lock_branch": "lockBranch",
            "push_actor_ids": "pushActorIds",
            "require_last_push_approval": "requireLastPushApproval",
            "required_approving_review_count": "requiredApprovingReviewCount",
            "required_deployment_environments": "requiredDeploymentEnvironments",
            "required_status_check_contexts": "requiredStatusCheckContexts",
            "require_approving_reviews": "requiresApprovingReviews",
            "require_codeowner_reviews": "requiresCodeOwnerReviews",
            "require_commit_signatures": "requiresCommitSignatures",
            "require_conversation_resolution": "requiresConversationResolution",
            "require_deployments": "requiresDeployments",
            "require_linear_history": "requiresLinearHistory",
            "require_status_checks": "requiresStatusChecks",
            "require_status_checks_strict": "requiresStrictStatusChecks",
            "restrict_push": "restrictsPushes",
            "restrict_review_dismissals": "restrictsReviewDismissals",
            "review_dismissal_actor_ids": "reviewDismissalActorIds",
        }
        return {arg_map[k]: v for k, v in kwargs.items() if v is not None}

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
