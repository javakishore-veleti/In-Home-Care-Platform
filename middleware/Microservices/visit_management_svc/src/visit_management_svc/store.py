from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException, status

from shared.storage import BaseStore, now_utc

from .schemas import (
    VisitActionItemCreate,
    VisitDecisionCreate,
    VisitDocumentCreate,
    VisitNoteCreate,
    VisitCreate,
)


class VisitStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('visit')

    def create_visit(self, payload: VisitCreate) -> dict[str, Any]:
        record = {
            'member_id': payload.member_id,
            'appointment_id': payload.appointment_id,
            'staff_id': payload.staff_id,
            'visit_date': payload.visit_date or date.today(),
            'status': payload.status,
            'started_at': payload.started_at,
            'completed_at': payload.completed_at,
            'notes_summary': payload.notes_summary,
            'created_at': now_utc(),
        }
        if self.using_db:
            return self.fetch_one(
                '''
                INSERT INTO visit_schema.visits (
                    member_id, appointment_id, staff_id, visit_date, status,
                    started_at, completed_at, notes_summary, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, member_id, appointment_id, staff_id, visit_date, status,
                          started_at, completed_at, notes_summary, created_at
                ''',
                (
                    record['member_id'],
                    record['appointment_id'],
                    record['staff_id'],
                    record['visit_date'],
                    record['status'],
                    record['started_at'],
                    record['completed_at'],
                    record['notes_summary'],
                    record['created_at'],
                ),
            )
        return self.memory.insert(self._memory_key('visits'), record)

    def list_all_visits(
        self,
        *,
        query: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Cross-member visit listing for admin/support views."""
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, 100))
        search = (query or '').strip().lower()
        status_clean = (status_filter or '').strip().lower()
        if self.using_db:
            params: list[Any] = []
            where: list[str] = []
            if status_clean:
                where.append('LOWER(status) = %s')
                params.append(status_clean)
            if search:
                where.append("(CAST(id AS TEXT) ILIKE %s OR COALESCE(notes_summary, '') ILIKE %s OR status ILIKE %s)")
                match = f'%{search}%'
                params.extend([match, match, match])
            where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
            total_row = self.fetch_one(
                f'SELECT COUNT(*) AS count FROM visit_schema.visits {where_sql}',
                tuple(params),
            )
            params.extend([safe_page_size, (safe_page - 1) * safe_page_size])
            items = self.fetch_all(
                f'''
                SELECT id, member_id, appointment_id, staff_id, visit_date, status,
                       started_at, completed_at, notes_summary, created_at
                FROM visit_schema.visits
                {where_sql}
                ORDER BY visit_date DESC, id DESC
                LIMIT %s OFFSET %s
                ''',
                tuple(params),
            )
            total = int(total_row['count']) if total_row else 0
        else:
            rows = self.memory.list(self._memory_key('visits'))
            if status_clean:
                rows = [row for row in rows if str(row.get('status', '')).lower() == status_clean]
            if search:
                def _match(row: dict[str, Any]) -> bool:
                    haystack = ' '.join(
                        str(row.get(field) or '') for field in ('id', 'status', 'notes_summary')
                    ).lower()
                    return search in haystack
                rows = [row for row in rows if _match(row)]
            rows.sort(key=lambda row: (row.get('visit_date'), row['id']), reverse=True)
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

    def list_visits_for_appointment(self, appointment_id: int) -> list[dict[str, Any]]:
        if self.using_db:
            return self.fetch_all(
                '''
                SELECT id, member_id, appointment_id, staff_id, visit_date, status,
                       started_at, completed_at, notes_summary, created_at
                FROM visit_schema.visits
                WHERE appointment_id = %s
                ORDER BY visit_date DESC, id DESC
                ''',
                (appointment_id,),
            )
        return self.memory.list(
            self._memory_key('visits'),
            predicate=lambda row: row.get('appointment_id') == appointment_id,
            sort_key=lambda row: (row.get('visit_date'), row['id']),
            reverse=True,
        )

    def get_visit(self, visit_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, member_id, appointment_id, staff_id, visit_date, status,
                       started_at, completed_at, notes_summary, created_at
                FROM visit_schema.visits
                WHERE id = %s
                ''',
                (visit_id,),
            )
        else:
            row = self.memory.get(self._memory_key('visits'), visit_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Visit not found.')
        return row

    def create_note(self, visit_id: int, payload: VisitNoteCreate) -> dict[str, Any]:
        self.get_visit(visit_id)
        return self._create_artifact(
            'visit_notes',
            visit_id,
            {'note': payload.note, 'author_name': payload.author_name},
        )

    def create_decision(self, visit_id: int, payload: VisitDecisionCreate) -> dict[str, Any]:
        self.get_visit(visit_id)
        return self._create_artifact(
            'visit_decisions',
            visit_id,
            {'decision': payload.decision, 'owner_name': payload.owner_name},
        )

    def create_action_item(self, visit_id: int, payload: VisitActionItemCreate) -> dict[str, Any]:
        self.get_visit(visit_id)
        return self._create_artifact(
            'visit_action_items',
            visit_id,
            {'description': payload.description, 'due_date': payload.due_date, 'status': payload.status},
        )

    def create_document(self, visit_id: int, payload: VisitDocumentCreate) -> dict[str, Any]:
        self.get_visit(visit_id)
        return self._create_artifact(
            'visit_documents',
            visit_id,
            {
                'title': payload.title,
                'doc_type': payload.doc_type,
                'mime_type': payload.mime_type,
                'file_path': payload.file_path,
                'summary': payload.summary,
            },
        )

    def list_documents(self, visit_id: int) -> list[dict[str, Any]]:
        return self._list_artifacts('visit_documents', visit_id)

    def list_notes(self, visit_id: int) -> list[dict[str, Any]]:
        return self._list_artifacts('visit_notes', visit_id)

    def list_decisions(self, visit_id: int) -> list[dict[str, Any]]:
        return self._list_artifacts('visit_decisions', visit_id)

    def list_action_items(self, visit_id: int) -> list[dict[str, Any]]:
        return self._list_artifacts('visit_action_items', visit_id)

    def _create_artifact(self, table: str, visit_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        record = {'visit_id': visit_id, **fields, 'created_at': now_utc()}
        if self.using_db:
            if table == 'visit_notes':
                return self.fetch_one(
                    '''
                    INSERT INTO visit_schema.visit_notes (visit_id, note, author_name, created_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, visit_id, note, author_name, created_at
                    ''',
                    (visit_id, fields['note'], fields.get('author_name'), record['created_at']),
                )
            if table == 'visit_decisions':
                return self.fetch_one(
                    '''
                    INSERT INTO visit_schema.visit_decisions (visit_id, decision, owner_name, created_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, visit_id, decision, owner_name, created_at
                    ''',
                    (visit_id, fields['decision'], fields.get('owner_name'), record['created_at']),
                )
            if table == 'visit_action_items':
                return self.fetch_one(
                    '''
                    INSERT INTO visit_schema.visit_action_items (visit_id, description, due_date, status, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, visit_id, description, due_date, status, created_at
                    ''',
                    (visit_id, fields['description'], fields.get('due_date'), fields.get('status'), record['created_at']),
                )
            return self.fetch_one(
                '''
                INSERT INTO visit_schema.visit_documents (visit_id, title, doc_type, mime_type, file_path, summary, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, visit_id, title, doc_type, mime_type, file_path, summary, created_at
                ''',
                (
                    visit_id,
                    fields['title'],
                    fields['doc_type'],
                    fields.get('mime_type'),
                    fields.get('file_path'),
                    fields.get('summary'),
                    record['created_at'],
                ),
            )
        return self.memory.insert(self._memory_key(table), record)

    def _list_artifacts(self, table: str, visit_id: int) -> list[dict[str, Any]]:
        self.get_visit(visit_id)
        if self.using_db:
            columns = {
                'visit_notes': 'id, visit_id, note, author_name, created_at',
                'visit_decisions': 'id, visit_id, decision, owner_name, created_at',
                'visit_action_items': 'id, visit_id, description, due_date, status, created_at',
                'visit_documents': 'id, visit_id, title, doc_type, mime_type, file_path, summary, created_at',
            }[table]
            return self.fetch_all(
                f'SELECT {columns} FROM visit_schema.{table} WHERE visit_id = %s ORDER BY id DESC',
                (visit_id,),
            )
        return self.memory.list(
            self._memory_key(table),
            predicate=lambda row: row['visit_id'] == visit_id,
            sort_key=lambda row: row['id'],
            reverse=True,
        )
