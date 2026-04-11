from __future__ import annotations

import copy
import os
import threading
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Callable, Iterable

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover
    psycopg = None
    dict_row = None

DEFAULT_DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://care:care@localhost:5432/in_home_care_platform',
)
_DB_AVAILABLE: bool | None = None
_DB_LOCK = threading.Lock()


class MemoryBackend:
    def __init__(self) -> None:
        self._tables: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
        self._counters: dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()

    def reset(self) -> None:
        with self._lock:
            self._tables = defaultdict(dict)
            self._counters = defaultdict(int)

    def insert(self, table: str, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            next_id = record.get('id') or (self._counters[table] + 1)
            self._counters[table] = max(self._counters[table], int(next_id))
            stored = copy.deepcopy(record)
            stored['id'] = int(next_id)
            self._tables[table][stored['id']] = stored
            return copy.deepcopy(stored)

    def get(self, table: str, record_id: int) -> dict[str, Any] | None:
        with self._lock:
            record = self._tables[table].get(int(record_id))
            return copy.deepcopy(record) if record else None

    def list(
        self,
        table: str,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
        sort_key: Callable[[dict[str, Any]], Any] | None = None,
        reverse: bool = False,
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = [copy.deepcopy(row) for row in self._tables[table].values()]
        if predicate is not None:
            rows = [row for row in rows if predicate(row)]
        if sort_key is not None:
            rows.sort(key=sort_key, reverse=reverse)
        return rows

    def update(self, table: str, record_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            if int(record_id) not in self._tables[table]:
                return None
            self._tables[table][int(record_id)].update(copy.deepcopy(updates))
            return copy.deepcopy(self._tables[table][int(record_id)])

    def delete(self, table: str, record_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self._tables[table].pop(int(record_id), None)
            return copy.deepcopy(row) if row else None


_memory_backend = MemoryBackend()


def get_memory_backend() -> MemoryBackend:
    return _memory_backend


def reset_memory_backend() -> None:
    _memory_backend.reset()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def force_memory_storage() -> bool:
    return os.getenv('IHCP_FORCE_MEMORY_STORAGE', '').lower() in {'1', 'true', 'yes'}


def reset_db_availability_cache() -> None:
    global _DB_AVAILABLE
    with _DB_LOCK:
        _DB_AVAILABLE = None


def get_database_url() -> str:
    return os.getenv('DATABASE_URL', DEFAULT_DATABASE_URL)


def database_available() -> bool:
    global _DB_AVAILABLE
    if force_memory_storage() or psycopg is None:
        return False
    with _DB_LOCK:
        if _DB_AVAILABLE is None:
            try:
                with psycopg.connect(get_database_url(), connect_timeout=1):
                    _DB_AVAILABLE = True
            except Exception:
                _DB_AVAILABLE = False
        return bool(_DB_AVAILABLE)


class BaseStore:
    def __init__(self, memory_namespace: str) -> None:
        self.memory = get_memory_backend()
        self.memory_namespace = memory_namespace

    @property
    def using_db(self) -> bool:
        return database_available()

    def fetch_one(self, query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        with psycopg.connect(get_database_url(), row_factory=dict_row, connect_timeout=1) as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                return cur.fetchone()

    def fetch_all(self, query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with psycopg.connect(get_database_url(), row_factory=dict_row, connect_timeout=1) as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                return list(cur.fetchall())

    def execute(self, query: str, params: Iterable[Any] = ()) -> None:
        with psycopg.connect(get_database_url(), row_factory=dict_row, connect_timeout=1) as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))

    def _memory_key(self, name: str) -> str:
        return f'{self.memory_namespace}.{name}'


def serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_value(item) for key, item in value.items()}
    return value
