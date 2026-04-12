"""Stores for knowledge_schema tables.

Collections, repositories, repository items, and indexing runs. All
operations work in both Postgres and in-memory backends (same pattern
as the rest of the middleware).
"""
from __future__ import annotations

import math
import re
from typing import Any

from fastapi import HTTPException, status

from shared.storage import BaseStore, now_utc


def slugify(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug or 'untitled'


REPO_TYPES = {'announcements', 'notes', 'policies', 'knowledgebases', 'research', 'experiences', 'others'}
ITEM_TYPES = {'document', 'announcement', 'link', 'note', 'image'}
VALID_TRANSITIONS = {
    'draft': {'locked'},
    'locked': {'draft', 'publishing'},
    'publishing': {'indexed', 'failed'},
    'indexed': {'draft', 'publishing'},
    'failed': {'draft', 'publishing'},
}


class CollectionStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('knowledge_collection')

    def list_collections(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        if self.using_db:
            params: list[Any] = []
            where = ''
            if org_id:
                where = 'WHERE org_id = %s'
                params.append(org_id)
            return self.fetch_all(
                f'''
                SELECT id, name, slug, service_type, description, icon_emoji,
                       org_id, jurisdiction, repo_count, total_chunks,
                       created_at, updated_at
                FROM knowledge_schema.collections
                {where}
                ORDER BY name
                ''',
                tuple(params),
            )
        rows = self.memory.list(self._memory_key('collections'))
        if org_id:
            rows = [r for r in rows if r.get('org_id') == org_id]
        return sorted(rows, key=lambda r: r.get('name', ''))

    def get_collection(self, collection_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, name, slug, service_type, description, icon_emoji,
                       org_id, jurisdiction, repo_count, total_chunks,
                       created_at, updated_at
                FROM knowledge_schema.collections WHERE id = %s
                ''',
                (collection_id,),
            )
        else:
            row = self.memory.get(self._memory_key('collections'), collection_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Collection not found.')
        return row

    def get_collection_by_slug(self, slug: str) -> dict[str, Any] | None:
        if self.using_db:
            return self.fetch_one(
                'SELECT id, name, slug, service_type FROM knowledge_schema.collections WHERE slug = %s',
                (slug,),
            )
        return next((r for r in self.memory.list(self._memory_key('collections')) if r.get('slug') == slug), None)

    def create_collection(self, *, name: str, service_type: str | None = None,
                          description: str | None = None, icon_emoji: str = '📚',
                          org_id: str = 'platform', jurisdiction: str | None = None) -> dict[str, Any]:
        slug = slugify(name)
        if self.using_db:
            row = self.fetch_one(
                '''
                INSERT INTO knowledge_schema.collections
                    (name, slug, service_type, description, icon_emoji, org_id, jurisdiction, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (slug) DO UPDATE SET updated_at = EXCLUDED.updated_at
                RETURNING id, name, slug, service_type, description, icon_emoji,
                          org_id, jurisdiction, repo_count, total_chunks, created_at, updated_at
                ''',
                (name, slug, service_type, description, icon_emoji, org_id, jurisdiction, now_utc(), now_utc()),
            )
            assert row is not None
            return row
        existing = self.get_collection_by_slug(slug)
        if existing:
            return self.get_collection(existing['id'])
        return self.memory.insert(self._memory_key('collections'), {
            'name': name, 'slug': slug, 'service_type': service_type,
            'description': description, 'icon_emoji': icon_emoji,
            'org_id': org_id, 'jurisdiction': jurisdiction,
            'repo_count': 0, 'total_chunks': 0,
            'created_at': now_utc(), 'updated_at': now_utc(),
        })

    def update_collection(self, collection_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        self.get_collection(collection_id)
        if self.using_db:
            assignments = []
            values: list[Any] = []
            for field in ('name', 'description', 'icon_emoji', 'jurisdiction'):
                if field in updates:
                    assignments.append(f'{field} = %s')
                    values.append(updates[field])
            if not assignments:
                return self.get_collection(collection_id)
            assignments.append('updated_at = %s')
            values.append(now_utc())
            values.append(collection_id)
            self.execute(
                f'UPDATE knowledge_schema.collections SET {", ".join(assignments)} WHERE id = %s',
                tuple(values),
            )
            return self.get_collection(collection_id)
        filtered = {k: v for k, v in updates.items() if k in ('name', 'description', 'icon_emoji', 'jurisdiction')}
        filtered['updated_at'] = now_utc()
        updated = self.memory.update(self._memory_key('collections'), collection_id, filtered)
        assert updated is not None
        return updated

    def refresh_counts(self, collection_id: int) -> None:
        if self.using_db:
            self.execute(
                '''
                UPDATE knowledge_schema.collections SET
                    repo_count = (SELECT COUNT(*) FROM knowledge_schema.repositories WHERE collection_id = %s),
                    total_chunks = COALESCE((SELECT SUM(chunk_count) FROM knowledge_schema.repositories WHERE collection_id = %s), 0),
                    updated_at = %s
                WHERE id = %s
                ''',
                (collection_id, collection_id, now_utc(), collection_id),
            )


class RepositoryStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('knowledge_repo')

    def list_repositories(self, collection_id: int) -> list[dict[str, Any]]:
        if self.using_db:
            return self.fetch_all(
                '''
                SELECT id, collection_id, name, slug, repo_type, status, description,
                       source_mode, source_path, org_id, jurisdictions,
                       item_count, chunk_count, last_indexed_at, last_error,
                       created_by_user_id, created_at, updated_at
                FROM knowledge_schema.repositories
                WHERE collection_id = %s
                ORDER BY name
                ''',
                (collection_id,),
            )
        return sorted(
            [r for r in self.memory.list(self._memory_key('repositories')) if r.get('collection_id') == collection_id],
            key=lambda r: r.get('name', ''),
        )

    def get_repository(self, repo_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, collection_id, name, slug, repo_type, status, description,
                       source_mode, source_path, org_id, jurisdictions,
                       item_count, chunk_count, last_indexed_at, last_error,
                       created_by_user_id, created_at, updated_at
                FROM knowledge_schema.repositories WHERE id = %s
                ''',
                (repo_id,),
            )
        else:
            row = self.memory.get(self._memory_key('repositories'), repo_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Repository not found.')
        return row

    def create_repository(self, *, collection_id: int, name: str, repo_type: str = 'others',
                          description: str | None = None, source_mode: str = 'local',
                          source_path: str | None = None, org_id: str = 'platform',
                          jurisdictions: list[str] | None = None,
                          created_by_user_id: int | None = None) -> dict[str, Any]:
        if repo_type not in REPO_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'repo_type must be one of {sorted(REPO_TYPES)}')
        slug = slugify(name)
        if self.using_db:
            row = self.fetch_one(
                '''
                INSERT INTO knowledge_schema.repositories
                    (collection_id, name, slug, repo_type, status, description,
                     source_mode, source_path, org_id, jurisdictions,
                     created_by_user_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, collection_id, name, slug, repo_type, status, description,
                          source_mode, source_path, org_id, jurisdictions,
                          item_count, chunk_count, last_indexed_at, last_error,
                          created_by_user_id, created_at, updated_at
                ''',
                (collection_id, name, slug, repo_type, description,
                 source_mode, source_path, org_id, jurisdictions,
                 created_by_user_id, now_utc(), now_utc()),
            )
            assert row is not None
            return row
        return self.memory.insert(self._memory_key('repositories'), {
            'collection_id': collection_id, 'name': name, 'slug': slug,
            'repo_type': repo_type, 'status': 'draft', 'description': description,
            'source_mode': source_mode, 'source_path': source_path,
            'org_id': org_id, 'jurisdictions': jurisdictions,
            'item_count': 0, 'chunk_count': 0,
            'last_indexed_at': None, 'last_error': None,
            'created_by_user_id': created_by_user_id,
            'created_at': now_utc(), 'updated_at': now_utc(),
        })

    def transition_status(self, repo_id: int, target: str) -> dict[str, Any]:
        repo = self.get_repository(repo_id)
        current = repo.get('status', 'draft')
        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Cannot transition from {current} to {target}. Allowed: {sorted(allowed)}',
            )
        updates: dict[str, Any] = {'status': target, 'updated_at': now_utc()}
        if target == 'indexed':
            updates['last_indexed_at'] = now_utc()
            updates['last_error'] = None
        if target == 'failed':
            pass
        if self.using_db:
            assignments = ', '.join(f'{k} = %s' for k in updates)
            values = list(updates.values()) + [repo_id]
            self.execute(
                f'UPDATE knowledge_schema.repositories SET {assignments} WHERE id = %s',
                tuple(values),
            )
            return self.get_repository(repo_id)
        updated = self.memory.update(self._memory_key('repositories'), repo_id, updates)
        assert updated is not None
        return updated


class RepositoryItemStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('knowledge_item')

    def list_items(self, repository_id: int) -> list[dict[str, Any]]:
        if self.using_db:
            return self.fetch_all(
                '''
                SELECT id, repository_id, collection_id, item_type, title,
                       content_text, source_url, file_path, file_name,
                       file_size_bytes, mime_type, chunk_count,
                       org_id, jurisdictions, created_by_user_id,
                       created_at, updated_at
                FROM knowledge_schema.repository_items
                WHERE repository_id = %s
                ORDER BY created_at DESC
                ''',
                (repository_id,),
            )
        return sorted(
            [r for r in self.memory.list(self._memory_key('items')) if r.get('repository_id') == repository_id],
            key=lambda r: r.get('created_at', ''),
            reverse=True,
        )

    def get_item(self, item_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, repository_id, collection_id, item_type, title,
                       content_text, source_url, file_path, file_name,
                       file_size_bytes, mime_type, chunk_count,
                       org_id, jurisdictions, created_by_user_id,
                       created_at, updated_at
                FROM knowledge_schema.repository_items WHERE id = %s
                ''',
                (item_id,),
            )
        else:
            row = self.memory.get(self._memory_key('items'), item_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found.')
        return row

    def create_item(self, *, repository_id: int, collection_id: int,
                    item_type: str, title: str,
                    content_text: str | None = None, source_url: str | None = None,
                    file_path: str | None = None, file_name: str | None = None,
                    file_size_bytes: int | None = None, mime_type: str | None = None,
                    org_id: str = 'platform', jurisdictions: list[str] | None = None,
                    created_by_user_id: int | None = None) -> dict[str, Any]:
        if item_type not in ITEM_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'item_type must be one of {sorted(ITEM_TYPES)}')
        if self.using_db:
            row = self.fetch_one(
                '''
                INSERT INTO knowledge_schema.repository_items
                    (repository_id, collection_id, item_type, title,
                     content_text, source_url, file_path, file_name,
                     file_size_bytes, mime_type, org_id, jurisdictions,
                     created_by_user_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, repository_id, collection_id, item_type, title,
                          content_text, source_url, file_path, file_name,
                          file_size_bytes, mime_type, chunk_count,
                          org_id, jurisdictions, created_by_user_id,
                          created_at, updated_at
                ''',
                (repository_id, collection_id, item_type, title,
                 content_text, source_url, file_path, file_name,
                 file_size_bytes, mime_type, org_id, jurisdictions,
                 created_by_user_id, now_utc(), now_utc()),
            )
            assert row is not None
            self._refresh_item_count(repository_id)
            return row
        inserted = self.memory.insert(self._memory_key('items'), {
            'repository_id': repository_id, 'collection_id': collection_id,
            'item_type': item_type, 'title': title,
            'content_text': content_text, 'source_url': source_url,
            'file_path': file_path, 'file_name': file_name,
            'file_size_bytes': file_size_bytes, 'mime_type': mime_type,
            'chunk_count': 0, 'org_id': org_id, 'jurisdictions': jurisdictions,
            'created_by_user_id': created_by_user_id,
            'created_at': now_utc(), 'updated_at': now_utc(),
        })
        return inserted

    def delete_item(self, item_id: int) -> None:
        item = self.get_item(item_id)
        if self.using_db:
            self.execute('DELETE FROM knowledge_schema.repository_items WHERE id = %s', (item_id,))
            self._refresh_item_count(item['repository_id'])
            return
        self.memory.delete(self._memory_key('items'), item_id)

    def _refresh_item_count(self, repository_id: int) -> None:
        if self.using_db:
            self.execute(
                '''
                UPDATE knowledge_schema.repositories SET
                    item_count = (SELECT COUNT(*) FROM knowledge_schema.repository_items WHERE repository_id = %s),
                    updated_at = %s
                WHERE id = %s
                ''',
                (repository_id, now_utc(), repository_id),
            )
