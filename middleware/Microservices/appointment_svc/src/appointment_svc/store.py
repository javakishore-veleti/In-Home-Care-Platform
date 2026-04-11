from __future__ import annotations

import math
from typing import Any

from fastapi import HTTPException, status

from shared.storage import BaseStore, now_utc

from .schemas import AppointmentCreate, AppointmentUpdate


class AppointmentStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('appointment')

    def create_appointment(self, payload: AppointmentCreate) -> dict[str, Any]:
        record = {
            'member_id': payload.member_id,
            'address_id': payload.address_id,
            'service_type': payload.service_type,
            'service_area': payload.service_area,
            'requested_date': payload.requested_date,
            'requested_time_slot': payload.requested_time_slot,
            'scheduled_start': payload.scheduled_start,
            'scheduled_end': payload.scheduled_end,
            'reason': payload.reason,
            'status': 'requested',
            'assigned_staff_id': None,
            'notes': payload.notes,
            'created_at': now_utc(),
            'updated_at': now_utc(),
            'cancelled_at': None,
        }
        if self.using_db:
            return self.fetch_one(
                '''
                INSERT INTO appointment_schema.appointments (
                    member_id, address_id, service_type, service_area, requested_date,
                    requested_time_slot, scheduled_start, scheduled_end, reason, status,
                    assigned_staff_id, notes, created_at, updated_at, cancelled_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, member_id, address_id, service_type, service_area, requested_date,
                          requested_time_slot, scheduled_start, scheduled_end, reason, status,
                          assigned_staff_id, notes, created_at, updated_at, cancelled_at
                ''',
                (
                    record['member_id'],
                    record['address_id'],
                    record['service_type'],
                    record['service_area'],
                    record['requested_date'],
                    record['requested_time_slot'],
                    record['scheduled_start'],
                    record['scheduled_end'],
                    record['reason'],
                    record['status'],
                    record['assigned_staff_id'],
                    record['notes'],
                    record['created_at'],
                    record['updated_at'],
                    record['cancelled_at'],
                ),
            )
        return self.memory.insert(self._memory_key('appointments'), record)

    def list_appointments(
        self,
        *,
        member_id: int,
        query: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, 50))
        search = (query or '').strip().lower()
        if self.using_db:
            params: list[Any] = [member_id]
            where = ['member_id = %s']
            if search:
                where.append("(CAST(id AS TEXT) ILIKE %s OR service_type ILIKE %s OR COALESCE(service_area, '') ILIKE %s OR status ILIKE %s)")
                match = f'%{search}%'
                params.extend([match, match, match, match])
            where_sql = ' AND '.join(where)
            total_row = self.fetch_one(
                f'SELECT COUNT(*) AS count FROM appointment_schema.appointments WHERE {where_sql}',
                tuple(params),
            )
            params.extend([safe_page_size, (safe_page - 1) * safe_page_size])
            items = self.fetch_all(
                f'''
                SELECT id, member_id, address_id, service_type, service_area, requested_date,
                       requested_time_slot, scheduled_start, scheduled_end, reason, status,
                       assigned_staff_id, notes, created_at, updated_at, cancelled_at
                FROM appointment_schema.appointments
                WHERE {where_sql}
                ORDER BY requested_date DESC, id DESC
                LIMIT %s OFFSET %s
                ''',
                tuple(params),
            )
            total = int(total_row['count']) if total_row else 0
        else:
            items = self.memory.list(
                self._memory_key('appointments'),
                predicate=lambda row: row['member_id'] == member_id and self._matches(row, search),
                sort_key=lambda row: (row['requested_date'], row['id']),
                reverse=True,
            )
            total = len(items)
            start = (safe_page - 1) * safe_page_size
            items = items[start:start + safe_page_size]
        total_pages = max(1, math.ceil(total / safe_page_size))
        return {
            'items': items,
            'page': safe_page,
            'page_size': safe_page_size,
            'total': total,
            'total_pages': total_pages,
        }

    def get_appointment(self, appointment_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, member_id, address_id, service_type, service_area, requested_date,
                       requested_time_slot, scheduled_start, scheduled_end, reason, status,
                       assigned_staff_id, notes, created_at, updated_at, cancelled_at
                FROM appointment_schema.appointments
                WHERE id = %s
                ''',
                (appointment_id,),
            )
        else:
            row = self.memory.get(self._memory_key('appointments'), appointment_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Appointment not found.')
        return row

    def update_appointment(self, appointment_id: int, payload: AppointmentUpdate) -> dict[str, Any]:
        self.get_appointment(appointment_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return self.get_appointment(appointment_id)
        if self.using_db:
            assignments = []
            values: list[Any] = []
            for field, value in updates.items():
                assignments.append(f'{field} = %s')
                values.append(value)
            assignments.append('updated_at = %s')
            values.append(now_utc())
            values.append(appointment_id)
            row = self.fetch_one(
                f'''
                UPDATE appointment_schema.appointments
                SET {', '.join(assignments)}
                WHERE id = %s
                RETURNING id, member_id, address_id, service_type, service_area, requested_date,
                          requested_time_slot, scheduled_start, scheduled_end, reason, status,
                          assigned_staff_id, notes, created_at, updated_at, cancelled_at
                ''',
                tuple(values),
            )
            assert row is not None
            return row
        updates['updated_at'] = now_utc()
        updated = self.memory.update(self._memory_key('appointments'), appointment_id, updates)
        assert updated is not None
        return updated

    def cancel_appointment(self, appointment_id: int) -> dict[str, Any]:
        self.get_appointment(appointment_id)
        if self.using_db:
            row = self.fetch_one(
                '''
                UPDATE appointment_schema.appointments
                SET status = 'cancelled', cancelled_at = %s, updated_at = %s
                WHERE id = %s
                RETURNING id, member_id, address_id, service_type, service_area, requested_date,
                          requested_time_slot, scheduled_start, scheduled_end, reason, status,
                          assigned_staff_id, notes, created_at, updated_at, cancelled_at
                ''',
                (now_utc(), now_utc(), appointment_id),
            )
            assert row is not None
            return row
        updated = self.memory.update(
            self._memory_key('appointments'),
            appointment_id,
            {'status': 'cancelled', 'cancelled_at': now_utc(), 'updated_at': now_utc()},
        )
        assert updated is not None
        return updated

    @staticmethod
    def _matches(row: dict[str, Any], search: str) -> bool:
        if not search:
            return True
        haystack = ' '.join(
            str(row.get(field) or '')
            for field in ('id', 'service_type', 'service_area', 'status')
        ).lower()
        return search in haystack
