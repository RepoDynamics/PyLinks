from __future__ import annotations as _annotations

from typing import TYPE_CHECKING as _TYPE_CHECKING
from pathlib import Path as _Path
import pylinks as _pylinks

if _TYPE_CHECKING:
    from typing import Literal


class Zenodo:
    """Zenodo API.

    References
    ----------
    - [API Manual](https://developers.zenodo.org/)
    - [Main Repository](https://github.com/zenodo/zenodo)
    """
    def __init__(self, token: str, sandbox: bool = False):
        self._sandbox = sandbox
        self._url = _pylinks.url.create("https://zenodo.org/api")
        self._url_sandbox = _pylinks.url.create("https://sandbox.zenodo.org/api")
        self._headers = {"Authorization": token}
        return

    def rest_query(
        self,
        query: str,
        verb: Literal["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"] = "GET",
        data = None,
        json = None,
        content_type: str | None = "application/json",
        sandbox: bool | None = None,
    ) -> dict | list:
        sandbox = sandbox if sandbox is not None else self._sandbox
        base_url = self._url_sandbox if sandbox else self._url
        content_header = {"Content-Type": content_type} if content_type else {}
        return _pylinks.http.request(
            url=base_url / query,
            verb=verb,
            data=data,
            json=json,
            headers=self._headers | content_header,
            response_type="json", # All responses are JSON (https://developers.zenodo.org/#responses)
        )

    def deposition_create(
        self,
        metadata: dict | None = None,
        sandbox: bool | None = None,
    ) -> dict:
        """Create a new deposition.

        Returns
        -------

        Example response:
        :::{code-block} json

        {
            "conceptrecid": "542200",
            "created": "2020-05-19T11:58:41.606998+00:00",
            "files": [],
            "id": 542201,
            "links": {
                "bucket": "https://zenodo.org/api/files/568377dd-daf8-4235-85e1-a56011ad454b",
                "discard": "https://zenodo.org/api/deposit/depositions/542201/actions/discard",
                "edit": "https://zenodo.org/api/deposit/depositions/542201/actions/edit",
                "files": "https://zenodo.org/api/deposit/depositions/542201/files",
                "html": "https://zenodo.org/deposit/542201",
                "latest_draft": "https://zenodo.org/api/deposit/depositions/542201",
                "latest_draft_html": "https://zenodo.org/deposit/542201",
                "publish": "https://zenodo.org/api/deposit/depositions/542201/actions/publish",
                "self": "https://zenodo.org/api/deposit/depositions/542201"
            },
            "metadata": {
                "prereserve_doi": {
                    "doi": "10.5072/zenodo.542201",
                    "recid": 542201
                }
            },
            "modified": "2020-05-19T11:58:41.607012+00:00",
            "owner": 12345,
            "record_id": 542201,
            "state": "unsubmitted",
            "submitted": false,
            "title": ""
        }
        :::
        """
        return self.rest_query(
            query="deposit/depositions",
            verb="POST",
            json=metadata or {},
            sandbox=sandbox,
        )

    def deposition_publish(self, deposition_id: str) -> dict:
        """Publish a deposition."""
        return self.rest_query(
            query=f"deposit/depositions/{deposition_id}/actions/publish",
            verb="POST",
        )

    def file_create(
        self,
        bucket_url: str | _pylinks.url.URL,
        filepath: str | _Path,
        upload_path: str | None = None,
    ) -> dict:
        """Upload a file to a Zenodo bucket.

        Returns
        -------

        Example response:
        :::{code-block} json

        {
          "key": "my-file.zip",
          "mimetype": "application/zip",
          "checksum": "md5:2942bfabb3d05332b66eb128e0842cff",
          "version_id": "38a724d3-40f1-4b27-b236-ed2e43200f85",
          "size": 13264,
          "created": "2020-02-26T14:20:53.805734+00:00",
          "updated": "2020-02-26T14:20:53.811817+00:00",
          "links": {
            "self": "https://zenodo.org/api/files/44cc40bc-50fd-4107-b347-00838c79f4c1/dummy_example.pdf",
            "version": "https://zenodo.org/api/files/44cc40bc-50fd-4107-b347-00838c79f4c1/dummy_example.pdf?versionId=38a724d3-40f1-4b27-b236-ed2e43200f85",
            "uploads": "https://zenodo.org/api/files/44cc40bc-50fd-4107-b347-00838c79f4c1/dummy_example.pdf?uploads"
          },
          "is_head": true,
          "delete_marker": false
        }
        :::
        """
        if not isinstance(bucket_url, _pylinks.url.URL):
            bucket_url = _pylinks.url.create(bucket_url)
        filepath = _Path(filepath)
        upload_path = upload_path or filepath.name
        with open(filepath, "rb") as file:
            return self.rest_query(
                query=bucket_url / upload_path,
                verb="PUT",
                data=file,
                content_type=None,
            )