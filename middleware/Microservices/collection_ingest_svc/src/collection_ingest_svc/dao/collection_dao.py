"""Collection CRUD against Postgres.

The collections table is owned by the care_admin_portal. This DAO reads
and writes it so the ingest service can look up collection paths and the
admin portal can define new collections via its own API.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..common.exceptions import CollectionNotFoundError
from ..common.models import Collection


class CollectionDAO:
    """Postgres-backed DAO. Accepts a psycopg connection pool or a dict-based
    fake for tests (FakeCollectionDAO below).
    """

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    def create(self, collection: Collection) -> Collection:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO collections (name, description, base_path, categories, created_by, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                    (collection.name, collection.description, collection.base_path,
                     [c.value for c in collection.categories],
                     collection.created_by, datetime.now(tz=timezone.utc)),
                )
                collection.id = cur.fetchone()[0]
                conn.commit()
        return collection

    def get_by_id(self, collection_id: int) -> Collection:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM collections WHERE id = %s", (collection_id,))
                row = cur.fetchone()
                if not row:
                    raise CollectionNotFoundError(f"Collection {collection_id} not found")
                return self._row_to_model(row, cur.description)
        return Collection(name="")  # unreachable

    def list_all(self) -> list[Collection]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM collections ORDER BY created_at DESC")
                return [self._row_to_model(r, cur.description) for r in cur.fetchall()]

    def _row_to_model(self, row: tuple, desc: Any) -> Collection:
        cols = [d.name for d in desc]
        data = dict(zip(cols, row))
        return Collection(**data)


class FakeCollectionDAO:
    """In-memory DAO for tests. Same interface as CollectionDAO."""

    def __init__(self) -> None:
        self._store: dict[int, Collection] = {}
        self._seq = 0

    def create(self, collection: Collection) -> Collection:
        self._seq += 1
        collection.id = self._seq
        collection.created_at = datetime.now(tz=timezone.utc)
        self._store[collection.id] = collection
        return collection

    def get_by_id(self, collection_id: int) -> Collection:
        if collection_id not in self._store:
            raise CollectionNotFoundError(f"Collection {collection_id} not found")
        return self._store[collection_id]

    def list_all(self) -> list[Collection]:
        return sorted(self._store.values(), key=lambda c: c.created_at or datetime.min, reverse=True)
