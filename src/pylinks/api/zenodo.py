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
        self._url = _pylinks.url.create(
            "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
        )
        self._headers = {"Authorization": f"Bearer {token}"}
        return

    def rest_query(
        self,
        query: str,
        verb: Literal["GET", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"] = "GET",
        params: dict | None = None,
        data = None,
        json = None,
        content_type: str | None = "application/json",
        response_type: Literal["str", "json", "bytes"] | None = "json"
    ) -> dict | list:
        content_header = {"Content-Type": content_type} if content_type else {}
        return _pylinks.http.request(
            url=self._url / query,
            verb=verb,
            params=params,
            data=data,
            json=json,
            headers=self._headers | content_header,
            response_type=response_type, # All responses are JSON (https://developers.zenodo.org/#responses)
        )

    def create_and_publish(
        self,
        metadata: dict,
        files: list[str | _Path | tuple[str | _Path, str]],
        previous_id: str | int | None = None
    ):
        def add_files(bucket_id: str):
            for file in files:
                if not isinstance(file, (str, _Path)):
                    filepath = file[0]
                    name = file[1]
                else:
                    filepath = file
                    name = None
                self.file_create(
                    bucket_id=bucket_id,
                    filepath=filepath,
                    name=name,
                )
            return

        if not previous_id:
            new_depo = self.deposition_create(metadata=metadata)
            add_files(bucket_id=new_depo["links"]["bucket"])
            return self.deposition_publish(new_depo["id"])
        new_ver = self.deposition_new_version(deposition_id=previous_id)
        for previous_file in new_ver["files"]:
            self.file_delete(deposition_id=new_ver["id"], file_id=previous_file["id"])
        add_files(new_ver["links"]["bucket"])
        return self.deposition_publish(new_ver["id"])


    def deposition_list(
        self,
        query: str | None = None,
        status: Literal["draft", "published"] | None = None,
        sort: Literal["bestmatch", "mostrecent", "-bestmatch", "-mostrecent"] | None = None,
        page: int | None = None,
        size: int | None = None,
        all_versions: bool | None = None,
    ):
        params = {k: v for k, v in locals().items() if k not in ("self", "query") and v}
        if query:
            params["q"] = query
        return self.rest_query(
            "deposit/depositions",
            verb="GET",
            params=params,
        )

    def deposition_retrieve(self, deposition_id: str | int):
        return self.rest_query(
            f"deposit/depositions/{deposition_id}",
            verb="GET",
        )

    def deposition_delete(self, deposition_id: str | int):
        self.rest_query(
            f"deposit/depositions/{deposition_id}",
            verb="DELETE",
            response_type=None
        )
        return

    def deposition_create(self, metadata: dict | None = None) -> dict:
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
            json={"metadata": metadata} if metadata else {},
        )

    def deposition_new_version(self, deposition_id: int | str):
        """Create a new version of a deposition as a draft."""
        return self.rest_query(
            query=f"deposit/depositions/{deposition_id}/actions/newversion",
            verb="POST",
        )

    def deposition_update(self, deposition_id: int | str, metadata: dict):
        """Update and existing deposition."""
        return self.rest_query(
            query=f"deposit/depositions/{deposition_id}",
            verb="PUT",
            json={"metadata": metadata},
        )

    def deposition_publish(self, deposition_id: int | str) -> dict:
        """Publish a deposition."""
        return self.rest_query(
            query=f"deposit/depositions/{deposition_id}/actions/publish",
            verb="POST",
        )

    def file_list(self, deposition_id: str | int):
        return self.rest_query(
            f"deposit/depositions/{deposition_id}/files",
            verb="GET"
        )

    def file_create(
        self,
        bucket_id: str,
        filepath: str | _Path,
        name: str | None = None,
    ) -> dict:
        """Upload a file to a Zenodo bucket.

        Parameters
        ----------
        bucket_id
            Bucket ID (e.g., `"d7524553-7f8c-4632-bffb-8bea6a90b88b"`)
            or bucket URL (e.g., `"https://zenodo.org/api/files/d7524553-7f8c-4632-bffb-8bea6a90b88b"`)

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
        bucket_id = bucket_id.removeprefix(f"{self._url}/files/")
        filepath = _Path(filepath)
        name = name or filepath.name
        with open(filepath, "rb") as file:
            return self.rest_query(
                query=f"files/{bucket_id}/{name}",
                verb="PUT",
                data=file,
                content_type=None,
            )

    def file_delete(self, deposition_id: str | int, file_id: str | int):
        return self.rest_query(
            f"deposit/depositions/{deposition_id}/files/{file_id}",
            verb="DELETE",
            response_type=None,
        )