"""Admin-gated proxy routes for knowledge_svc.

All endpoints require admin role. The gateway proxies every call to
knowledge_svc HTTP on :8010 via the KnowledgeClient — same pattern as
the AppointmentClient proxy.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, File, UploadFile, status
from pydantic import BaseModel, Field

from .dependencies import require_roles

from .knowledge_client import KnowledgeClient

router = APIRouter(
    prefix='/api/admin/knowledge',
    tags=['knowledge'],
    dependencies=[Depends(require_roles({'admin'}))],
)

_client = KnowledgeClient()


# ----- Schemas -----

class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    service_type: str | None = None
    description: str | None = None
    icon_emoji: str = '📚'

class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon_emoji: str | None = None
    jurisdiction: str | None = None

class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    repo_type: str = 'others'
    description: str | None = None
    source_mode: str = 'local'
    jurisdictions: list[str] | None = None

class ItemCreate(BaseModel):
    item_type: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=255)
    content_text: str | None = None
    source_url: str | None = None


# ----- Collections -----

@router.get('/collections')
def list_collections() -> dict[str, Any]:
    return _client.list_collections()

@router.get('/collections/{collection_id}')
def get_collection(collection_id: int) -> dict[str, Any]:
    return _client.get_collection(collection_id)

@router.post('/collections', status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate = Body(...)) -> dict[str, Any]:
    return _client.create_collection(payload.model_dump())

@router.patch('/collections/{collection_id}')
def update_collection(collection_id: int, payload: CollectionUpdate = Body(...)) -> dict[str, Any]:
    return _client.update_collection(collection_id, payload.model_dump(exclude_unset=True))


# ----- Repositories -----

@router.get('/collections/{collection_id}/repositories')
def list_repositories(collection_id: int) -> dict[str, Any]:
    return _client.list_repositories(collection_id)

@router.get('/repositories/{repo_id}')
def get_repository(repo_id: int) -> dict[str, Any]:
    return _client.get_repository(repo_id)

@router.post('/collections/{collection_id}/repositories', status_code=status.HTTP_201_CREATED)
def create_repository(collection_id: int, payload: RepositoryCreate = Body(...)) -> dict[str, Any]:
    return _client.create_repository(collection_id, payload.model_dump())

@router.post('/repositories/{repo_id}/lock')
def lock_repository(repo_id: int) -> dict[str, Any]:
    return _client.lock_repository(repo_id)

@router.post('/repositories/{repo_id}/unlock')
def unlock_repository(repo_id: int) -> dict[str, Any]:
    return _client.unlock_repository(repo_id)

@router.post('/repositories/{repo_id}/publish')
def publish_repository(repo_id: int) -> dict[str, Any]:
    return _client.publish_repository(repo_id)

@router.post('/repositories/{repo_id}/reindex')
def reindex_repository(repo_id: int) -> dict[str, Any]:
    return _client.reindex_repository(repo_id)

@router.patch('/repositories/{repo_id}/target-vectordbs')
def update_target_vectordbs(repo_id: int, payload: dict = Body(...)) -> dict[str, Any]:
    return _client.update_target_vectordbs(repo_id, payload.get('target_vectordbs', []))

@router.get('/repositories/{repo_id}/indexing-history')
def list_indexing_history(repo_id: int, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    return _client.list_indexing_history(repo_id, page=page, page_size=page_size)

@router.get('/supported-vectordbs')
def list_supported_vectordbs() -> dict[str, Any]:
    return _client.list_supported_vectordbs()


# ----- Items -----

@router.get('/repositories/{repo_id}/items')
def list_items(repo_id: int) -> dict[str, Any]:
    return _client.list_items(repo_id)

@router.post('/repositories/{repo_id}/items', status_code=status.HTTP_201_CREATED)
def create_item(repo_id: int, payload: ItemCreate = Body(...)) -> dict[str, Any]:
    return _client.create_item(repo_id, payload.model_dump())

@router.post('/repositories/{repo_id}/items/upload', status_code=status.HTTP_201_CREATED)
async def upload_item(repo_id: int, file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    return _client.upload_item(repo_id, file.filename or 'unnamed', content, file.content_type or 'application/octet-stream')

@router.delete('/items/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None:
    _client.delete_item(item_id)


@router.post('/setup-defaults', status_code=status.HTTP_202_ACCEPTED)
def setup_defaults() -> dict[str, Any]:
    return _client.setup_defaults()

@router.get('/setup-defaults/status')
def setup_defaults_status() -> dict[str, Any]:
    return _client.setup_defaults_status()

@router.post('/setup-defaults/reset')
def reset_setup_defaults() -> dict[str, Any]:
    return _client.reset_setup_defaults()
