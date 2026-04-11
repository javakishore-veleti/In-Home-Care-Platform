"""CRUD operations for collections — delegates to CollectionDAO."""
from __future__ import annotations

from ..common.models import Collection
from ..dao.collection_dao import CollectionDAO


class CollectionService:
    def __init__(self, dao: CollectionDAO) -> None:
        self._dao = dao

    def create(self, collection: Collection) -> Collection:
        return self._dao.create(collection)

    def get(self, collection_id: int) -> Collection:
        return self._dao.get_by_id(collection_id)

    def list_all(self) -> list[Collection]:
        return self._dao.list_all()
