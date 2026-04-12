"""HTTP client wrapping knowledge_svc for the api_gateway admin routes."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from fastapi import HTTPException, status

log = logging.getLogger(__name__)

KNOWLEDGE_SVC_URL = os.getenv('KNOWLEDGE_SVC_URL', 'http://127.0.0.1:8010')
HTTP_TIMEOUT = float(os.getenv('KNOWLEDGE_SVC_TIMEOUT_SECONDS', '10'))


def _raise_for(resp: httpx.Response) -> None:
    if resp.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Knowledge resource not found.')
    if resp.status_code == 409:
        try:
            detail = resp.json().get('detail') or resp.text
        except ValueError:
            detail = resp.text
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    if resp.is_error:
        try:
            detail = resp.json().get('detail') or resp.text
        except ValueError:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)


class KnowledgeClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self._client = httpx.Client(base_url=base_url or KNOWLEDGE_SVC_URL, timeout=timeout or HTTP_TIMEOUT)

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    # ----- Collections -----

    def list_collections(self) -> dict[str, Any]:
        resp = self._client.get('/collections')
        _raise_for(resp)
        return resp.json()

    def get_collection(self, collection_id: int) -> dict[str, Any]:
        resp = self._client.get(f'/collections/{collection_id}')
        _raise_for(resp)
        return resp.json()

    def create_collection(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.post('/collections', json=payload)
        _raise_for(resp)
        return resp.json()

    def update_collection(self, collection_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.patch(f'/collections/{collection_id}', json=payload)
        _raise_for(resp)
        return resp.json()

    # ----- Repositories -----

    def list_repositories(self, collection_id: int) -> dict[str, Any]:
        resp = self._client.get(f'/collections/{collection_id}/repositories')
        _raise_for(resp)
        return resp.json()

    def get_repository(self, repo_id: int) -> dict[str, Any]:
        resp = self._client.get(f'/repositories/{repo_id}')
        _raise_for(resp)
        return resp.json()

    def create_repository(self, collection_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.post(f'/collections/{collection_id}/repositories', json=payload)
        _raise_for(resp)
        return resp.json()

    def lock_repository(self, repo_id: int) -> dict[str, Any]:
        resp = self._client.post(f'/repositories/{repo_id}/lock')
        _raise_for(resp)
        return resp.json()

    def unlock_repository(self, repo_id: int) -> dict[str, Any]:
        resp = self._client.post(f'/repositories/{repo_id}/unlock')
        _raise_for(resp)
        return resp.json()

    def publish_repository(self, repo_id: int) -> dict[str, Any]:
        resp = self._client.post(f'/repositories/{repo_id}/publish')
        _raise_for(resp)
        return resp.json()

    def reindex_repository(self, repo_id: int) -> dict[str, Any]:
        resp = self._client.post(f'/repositories/{repo_id}/reindex')
        _raise_for(resp)
        return resp.json()

    # ----- Items -----

    def list_items(self, repo_id: int) -> dict[str, Any]:
        resp = self._client.get(f'/repositories/{repo_id}/items')
        _raise_for(resp)
        return resp.json()

    def create_item(self, repo_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.post(f'/repositories/{repo_id}/items', json=payload)
        _raise_for(resp)
        return resp.json()

    def upload_item(self, repo_id: int, filename: str, content: bytes, content_type: str) -> dict[str, Any]:
        resp = self._client.post(
            f'/repositories/{repo_id}/items/upload',
            files={'file': (filename, content, content_type)},
        )
        _raise_for(resp)
        return resp.json()

    def delete_item(self, item_id: int) -> None:
        resp = self._client.delete(f'/items/{item_id}')
        _raise_for(resp)

    def setup_defaults(self) -> dict[str, Any]:
        resp = self._client.post('/setup-defaults')
        _raise_for(resp)
        return resp.json()

    def setup_defaults_status(self) -> dict[str, Any]:
        resp = self._client.get('/setup-defaults/status')
        _raise_for(resp)
        return resp.json()

    def reset_setup_defaults(self) -> dict[str, Any]:
        resp = self._client.post('/setup-defaults/reset')
        _raise_for(resp)
        return resp.json()
