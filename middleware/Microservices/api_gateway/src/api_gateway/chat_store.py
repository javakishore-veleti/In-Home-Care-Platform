from __future__ import annotations

from typing import Any

from shared.storage import BaseStore, now_utc


class ChatStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('chat')

    def list_messages(self, member_id: int) -> list[dict[str, Any]]:
        if self.using_db:
            return self.fetch_all(
                '''
                SELECT id, member_id, role, message, created_at
                FROM member_schema.member_chat_messages
                WHERE member_id = %s
                ORDER BY id ASC
                ''',
                (member_id,),
            )
        return self.memory.list(
            self._memory_key('messages'),
            predicate=lambda row: row['member_id'] == member_id,
            sort_key=lambda row: row['id'],
        )

    def add_message(self, member_id: int, role: str, message: str) -> dict[str, Any]:
        record = {
            'member_id': member_id,
            'role': role,
            'message': message,
            'created_at': now_utc(),
        }
        if self.using_db:
            return self.fetch_one(
                '''
                INSERT INTO member_schema.member_chat_messages (member_id, role, message, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id, member_id, role, message, created_at
                ''',
                (member_id, role, message, record['created_at']),
            )
        return self.memory.insert(self._memory_key('messages'), record)
