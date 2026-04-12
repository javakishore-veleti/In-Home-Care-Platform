"""REST routes for knowledge_svc.

All routes are public (no JWT gate) because this service is called by
api_gateway's admin routes which handle the role check. Direct access
to knowledge_svc ports (8010) is an internal-only path.
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from .store import CollectionStore, RepositoryItemStore, RepositoryStore

log = logging.getLogger(__name__)

router = APIRouter(tags=['knowledge'])

_collections = CollectionStore()
_repos = RepositoryStore()
_items = RepositoryItemStore()

KNOWLEDGE_DATA_ROOT = os.getenv('KNOWLEDGE_DATA_ROOT', './knowledge_data')


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
    items = _collections.list_collections()
    return {'items': items, 'total': len(items)}


@router.get('/collections/{collection_id}')
def get_collection(collection_id: int) -> dict[str, Any]:
    return _collections.get_collection(collection_id)


@router.post('/collections', status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate = Body(...)) -> dict[str, Any]:
    return _collections.create_collection(
        name=payload.name,
        service_type=payload.service_type,
        description=payload.description,
        icon_emoji=payload.icon_emoji,
    )


@router.patch('/collections/{collection_id}')
def update_collection(collection_id: int, payload: CollectionUpdate = Body(...)) -> dict[str, Any]:
    return _collections.update_collection(collection_id, payload.model_dump(exclude_unset=True))


# ----- Repositories -----

@router.get('/collections/{collection_id}/repositories')
def list_repositories(collection_id: int) -> dict[str, Any]:
    _collections.get_collection(collection_id)
    items = _repos.list_repositories(collection_id)
    return {'items': items, 'total': len(items)}


@router.get('/repositories/{repo_id}')
def get_repository(repo_id: int) -> dict[str, Any]:
    return _repos.get_repository(repo_id)


@router.post('/collections/{collection_id}/repositories', status_code=status.HTTP_201_CREATED)
def create_repository(collection_id: int, payload: RepositoryCreate = Body(...)) -> dict[str, Any]:
    collection = _collections.get_collection(collection_id)
    from .store import slugify
    source_path = str(Path(KNOWLEDGE_DATA_ROOT) / collection.get('slug', '') / slugify(payload.name))
    repo = _repos.create_repository(
        collection_id=collection_id,
        name=payload.name,
        repo_type=payload.repo_type,
        description=payload.description,
        source_mode=payload.source_mode,
        source_path=source_path,
        jurisdictions=payload.jurisdictions,
    )
    Path(source_path).mkdir(parents=True, exist_ok=True)
    _collections.refresh_counts(collection_id)
    return repo


# ----- Repository lifecycle -----

@router.post('/repositories/{repo_id}/lock')
def lock_repository(repo_id: int) -> dict[str, Any]:
    return _repos.transition_status(repo_id, 'locked')


@router.post('/repositories/{repo_id}/unlock')
def unlock_repository(repo_id: int) -> dict[str, Any]:
    return _repos.transition_status(repo_id, 'draft')


@router.post('/repositories/{repo_id}/publish')
def publish_repository(repo_id: int) -> dict[str, Any]:
    """Set status to publishing. In Phase 2, this also produces a Kafka
    event consumed by Airflow. For now it just transitions the status."""
    repo = _repos.transition_status(repo_id, 'publishing')
    # Phase 2: publish Kafka event here
    # For now, auto-transition to indexed (no-op indexing)
    repo = _repos.transition_status(repo_id, 'indexed')
    log.info('repository.published repo_id=%d (Phase 2: Airflow indexing will replace this no-op)', repo_id)
    return repo


@router.post('/repositories/{repo_id}/reindex')
def reindex_repository(repo_id: int) -> dict[str, Any]:
    return _repos.transition_status(repo_id, 'publishing')


# ----- Repository items -----

@router.get('/repositories/{repo_id}/items')
def list_items(repo_id: int) -> dict[str, Any]:
    _repos.get_repository(repo_id)
    items = _items.list_items(repo_id)
    return {'items': items, 'total': len(items)}


@router.post('/repositories/{repo_id}/items', status_code=status.HTTP_201_CREATED)
def create_item(repo_id: int, payload: ItemCreate = Body(...)) -> dict[str, Any]:
    repo = _repos.get_repository(repo_id)
    if repo.get('status') != 'draft':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Items can only be added to repositories in draft status.')
    return _items.create_item(
        repository_id=repo_id,
        collection_id=repo['collection_id'],
        item_type=payload.item_type,
        title=payload.title,
        content_text=payload.content_text,
        source_url=payload.source_url,
    )


@router.post('/repositories/{repo_id}/items/upload', status_code=status.HTTP_201_CREATED)
async def upload_item(repo_id: int, file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a file (PDF, DOCX, image, text) into a draft repository."""
    repo = _repos.get_repository(repo_id)
    if repo.get('status') != 'draft':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Files can only be uploaded to repositories in draft status.')
    source_path = repo.get('source_path') or KNOWLEDGE_DATA_ROOT
    dest_dir = Path(source_path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or 'unnamed'
    dest = dest_dir / filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    file_size = dest.stat().st_size
    mime = file.content_type or 'application/octet-stream'
    item_type = 'document'
    if mime.startswith('image/'):
        item_type = 'image'
    return _items.create_item(
        repository_id=repo_id,
        collection_id=repo['collection_id'],
        item_type=item_type,
        title=filename,
        file_path=str(dest),
        file_name=filename,
        file_size_bytes=file_size,
        mime_type=mime,
    )


@router.delete('/items/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> None:
    item = _items.get_item(item_id)
    repo = _repos.get_repository(item['repository_id'])
    if repo.get('status') != 'draft':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Items can only be deleted from repositories in draft status.')
    _items.delete_item(item_id)
