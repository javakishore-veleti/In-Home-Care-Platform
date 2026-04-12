"""Auto-seed one collection per appointment service type.

Runs on knowledge_svc startup so the admin portal's Knowledge Base page
shows collection cards even before anyone creates anything. Idempotent:
existing collections with the same slug are left alone.
"""
from __future__ import annotations

import logging

from .store import CollectionStore

log = logging.getLogger(__name__)

DEFAULT_SERVICE_TYPES = [
    ('Personal Care & Companionship', '🏥'),
    ('Skilled Nursing', '💊'),
    ('Physical Therapy', '🏃'),
    ('Home Health Aide', '🏠'),
    ('Occupational Therapy', '🧩'),
    ('Speech Therapy', '🗣️'),
    ('Respite Care', '🌿'),
]


def seed_collections() -> None:
    store = CollectionStore()
    for name, emoji in DEFAULT_SERVICE_TYPES:
        try:
            store.create_collection(name=name, service_type=name, icon_emoji=emoji)
        except Exception as exc:  # pragma: no cover
            log.warning('seed.collection_failed name=%s error=%s', name, exc)
    log.info('seed.collections_done count=%d', len(DEFAULT_SERVICE_TYPES))
