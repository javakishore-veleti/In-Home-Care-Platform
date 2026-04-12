"""REST routes for knowledge_svc.

All routes are public (no JWT gate) because this service is called by
api_gateway's admin routes which handle the role check. Direct access
to knowledge_svc ports (8010) is an internal-only path.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from .store import CollectionStore, RepositoryItemStore, RepositoryStore, SetupJobStore

log = logging.getLogger(__name__)

router = APIRouter(tags=['knowledge'])

_collections = CollectionStore()
_repos = RepositoryStore()
_items = RepositoryItemStore()
_setup_jobs = SetupJobStore()

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


# ----- Setup defaults (bulk seed from JSON) -----

DEFAULTS_JSON = os.getenv(
    'KNOWLEDGE_DEFAULTS_JSON',
    str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'DevOps' / 'Seeds' / 'collections-repositories-defaults.json'),
)

def _run_setup_defaults(job_id: int) -> None:
    """Background worker that reads the seed JSON and creates repos + items."""
    repos_created = 0
    repos_skipped = 0
    items_created = 0
    error_msg: str | None = None

    try:
        with open(DEFAULTS_JSON) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        log.error('setup_defaults.json_error path=%s error=%s', DEFAULTS_JSON, exc)
        _setup_jobs.complete_run(job_id, repos_created=0, repos_skipped=0, items_created=0, error=str(exc))
        return

    try:
        for col_spec in data.get('collections', []):
            slug = col_spec.get('slug')
            if not slug:
                continue
            collection = _collections.get_collection_by_slug(slug)
            if not collection:
                log.warning('setup_defaults.collection_not_found slug=%s', slug)
                continue
            collection_id = collection['id']
            existing_repos = {r['slug'] for r in _repos.list_repositories(collection_id)}
            for repo_spec in col_spec.get('repositories', []):
                from .store import slugify
                repo_slug = slugify(repo_spec.get('name', ''))
                if repo_slug in existing_repos:
                    repos_skipped += 1
                    continue
                source_path = str(Path(KNOWLEDGE_DATA_ROOT) / slug / repo_slug)
                repo = _repos.create_repository(
                    collection_id=collection_id,
                    name=repo_spec['name'],
                    repo_type=repo_spec.get('repo_type', 'others'),
                    description=repo_spec.get('description'),
                    source_mode='local',
                    source_path=source_path,
                )
                repos_created += 1
                for item_spec in repo_spec.get('items', []):
                    _items.create_item(
                        repository_id=repo['id'],
                        collection_id=collection_id,
                        item_type=item_spec.get('item_type', 'note'),
                        title=item_spec.get('title', 'Untitled'),
                        content_text=item_spec.get('content_text'),
                        source_url=item_spec.get('source_url'),
                    )
                    items_created += 1
                Path(source_path).mkdir(parents=True, exist_ok=True)
            _collections.refresh_counts(collection_id)
    except Exception as exc:  # pragma: no cover
        error_msg = str(exc)
        log.exception('setup_defaults.error error=%s', exc)

    _setup_jobs.complete_run(
        job_id,
        repos_created=repos_created,
        repos_skipped=repos_skipped,
        items_created=items_created,
        error=error_msg,
    )
    log.info('setup_defaults.done repos_created=%d repos_skipped=%d items_created=%d', repos_created, repos_skipped, items_created)


@router.post('/setup-defaults', status_code=status.HTTP_202_ACCEPTED)
def setup_defaults(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Bulk-seed repositories and items from the defaults JSON.

    Creates a tracked job row so the admin UI can poll status and
    show progress. Safe to call multiple times — existing repos are
    skipped, and a running job blocks duplicate starts.
    """
    latest = _setup_jobs.get_latest()
    if latest and latest.get('status') == 'running':
        return {'status': 'already_running', 'job': latest}
    job = _setup_jobs.create_run()
    background_tasks.add_task(_run_setup_defaults, job['id'])
    return {'status': 'started', 'job': job}


@router.get('/setup-defaults/status')
def setup_defaults_status() -> dict[str, Any]:
    """Return the latest setup-defaults job for the admin status card."""
    latest = _setup_jobs.get_latest()
    return {'job': latest}


@router.post('/setup-defaults/reset')
def reset_setup_defaults() -> dict[str, Any]:
    """Delete the latest job record so setup-defaults can be re-run.

    Only allowed when the job is NOT currently running.
    """
    latest = _setup_jobs.get_latest()
    if not latest:
        return {'status': 'nothing_to_reset'}
    if latest.get('status') == 'running':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Cannot reset while the job is still running.')
    _setup_jobs.reset(latest['id'])
    return {'status': 'reset_done'}
