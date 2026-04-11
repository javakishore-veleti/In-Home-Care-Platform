"""Store for support_cases.

Lives under member_svc because the table is in member_schema. The data is
read/written exclusively through the api_gateway support_routes.py — no
member-portal code touches cases.
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from shared.storage import BaseStore, now_utc


class SupportCaseStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('support_case')

    def create_case(
        self,
        *,
        member_id: int,
        subject: str,
        description: str | None,
        priority: str,
        created_by_user_id: int | None,
    ) -> dict[str, Any]:
        record = {
            'member_id': member_id,
            'subject': subject,
            'description': description,
            'priority': priority,
            'status': 'open',
            'created_by_user_id': created_by_user_id,
            'assigned_to_user_id': None,
            'created_at': now_utc(),
            'updated_at': now_utc(),
            'resolved_at': None,
        }
        if self.using_db:
            row = self.fetch_one(
                '''
                INSERT INTO member_schema.support_cases (
                    member_id, subject, description, priority, status,
                    created_by_user_id, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, 'open', %s, %s, %s)
                RETURNING id, member_id, subject, description, priority, status,
                          created_by_user_id, assigned_to_user_id,
                          created_at, updated_at, resolved_at
                ''',
                (
                    member_id,
                    subject,
                    description,
                    priority,
                    created_by_user_id,
                    record['created_at'],
                    record['updated_at'],
                ),
            )
            assert row is not None
            return row
        return self.memory.insert(self._memory_key('cases'), record)

    def list_cases(
        self,
        *,
        member_id: int | None = None,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, 100))
        status_clean = (status_filter or '').strip().lower()
        if self.using_db:
            params: list[Any] = []
            where: list[str] = []
            if member_id is not None:
                where.append('member_id = %s')
                params.append(member_id)
            if status_clean:
                where.append('LOWER(status) = %s')
                params.append(status_clean)
            where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
            total_row = self.fetch_one(
                f'SELECT COUNT(*) AS count FROM member_schema.support_cases {where_sql}',
                tuple(params),
            )
            params.extend([safe_page_size, (safe_page - 1) * safe_page_size])
            items = self.fetch_all(
                f'''
                SELECT id, member_id, subject, description, priority, status,
                       created_by_user_id, assigned_to_user_id,
                       created_at, updated_at, resolved_at
                FROM member_schema.support_cases
                {where_sql}
                ORDER BY id DESC
                LIMIT %s OFFSET %s
                ''',
                tuple(params),
            )
            total = int(total_row['count']) if total_row else 0
        else:
            rows = self.memory.list(self._memory_key('cases'))
            if member_id is not None:
                rows = [row for row in rows if row.get('member_id') == member_id]
            if status_clean:
                rows = [row for row in rows if str(row.get('status', '')).lower() == status_clean]
            rows.sort(key=lambda row: row['id'], reverse=True)
            total = len(rows)
            start = (safe_page - 1) * safe_page_size
            items = rows[start:start + safe_page_size]
        total_pages = max(1, (total + safe_page_size - 1) // safe_page_size)
        return {
            'items': items,
            'page': safe_page,
            'page_size': safe_page_size,
            'total': total,
            'total_pages': total_pages,
        }

    def get_case(self, case_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, member_id, subject, description, priority, status,
                       created_by_user_id, assigned_to_user_id,
                       created_at, updated_at, resolved_at
                FROM member_schema.support_cases
                WHERE id = %s
                ''',
                (case_id,),
            )
        else:
            row = self.memory.get(self._memory_key('cases'), case_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Support case not found.')
        return row
