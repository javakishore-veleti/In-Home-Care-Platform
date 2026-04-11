from __future__ import annotations

import math
from typing import Any

from fastapi import HTTPException, status

from shared.storage import BaseStore, now_utc

from .schemas import AppointmentCreate, AppointmentUpdate

# Single source of truth for the appointment SELECT shape. Every read path
# goes through here so claim metadata stays attached to the appointment row
# without each call site having to remember the LEFT JOIN.
_APPOINTMENT_SELECT_COLUMNS = '''
    a.id, a.member_id, a.address_id, a.service_type, a.service_area, a.requested_date,
    a.requested_time_slot, a.preferred_hour, a.preferred_minute, a.scheduled_start, a.scheduled_end, a.reason, a.status,
    a.assigned_staff_id, a.notes, a.created_at, a.updated_at, a.cancelled_at,
    a.slack_channel_id, a.slack_message_ts,
    c.slack_user_id AS claimed_by_slack_user_id,
    c.slack_user_name AS claimed_by_slack_user_name,
    c.claimed_at AS claimed_at
'''

_APPOINTMENT_SELECT_FROM = '''
    FROM appointment_schema.appointments a
    LEFT JOIN appointment_schema.appointment_claims c ON c.appointment_id = a.id
'''


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
            'preferred_hour': payload.preferred_hour,
            'preferred_minute': payload.preferred_minute,
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
            inserted = self.fetch_one(
                '''
                INSERT INTO appointment_schema.appointments (
                    member_id, address_id, service_type, service_area, requested_date,
                    requested_time_slot, preferred_hour, preferred_minute, scheduled_start, scheduled_end, reason, status,
                    assigned_staff_id, notes, created_at, updated_at, cancelled_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                ''',
                (
                    record['member_id'],
                    record['address_id'],
                    record['service_type'],
                    record['service_area'],
                    record['requested_date'],
                    record['requested_time_slot'],
                    record['preferred_hour'],
                    record['preferred_minute'],
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
            assert inserted is not None
            return self.get_appointment(int(inserted['id']))
        return self._with_claim_metadata(self.memory.insert(self._memory_key('appointments'), record))

    def list_appointments(
        self,
        *,
        member_id: int,
        query: str | None = None,
        service_type: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, 50))
        search = (query or '').strip().lower()
        service_type_filter = (service_type or '').strip().lower()
        if self.using_db:
            params: list[Any] = [member_id]
            where = ['a.member_id = %s']
            if service_type_filter:
                where.append('LOWER(a.service_type) = %s')
                params.append(service_type_filter)
            if search:
                where.append("(CAST(a.id AS TEXT) ILIKE %s OR a.service_type ILIKE %s OR COALESCE(a.service_area, '') ILIKE %s OR a.status ILIKE %s)")
                match = f'%{search}%'
                params.extend([match, match, match, match])
            where_sql = ' AND '.join(where)
            total_row = self.fetch_one(
                f'SELECT COUNT(*) AS count FROM appointment_schema.appointments a WHERE {where_sql}',
                tuple(params),
            )
            params.extend([safe_page_size, (safe_page - 1) * safe_page_size])
            items = self.fetch_all(
                f'''
                SELECT {_APPOINTMENT_SELECT_COLUMNS}
                {_APPOINTMENT_SELECT_FROM}
                WHERE {where_sql}
                ORDER BY a.requested_date DESC, a.id DESC
                LIMIT %s OFFSET %s
                ''',
                tuple(params),
            )
            total = int(total_row['count']) if total_row else 0
        else:
            items = self.memory.list(
                self._memory_key('appointments'),
                predicate=lambda row: row['member_id'] == member_id and self._matches_service_type(row, service_type_filter) and self._matches(row, search),
                sort_key=lambda row: (row['requested_date'], row['id']),
                reverse=True,
            )
            total = len(items)
            start = (safe_page - 1) * safe_page_size
            items = [self._with_claim_metadata(row) for row in items[start:start + safe_page_size]]
        total_pages = max(1, math.ceil(total / safe_page_size))
        return {
            'items': items,
            'page': safe_page,
            'page_size': safe_page_size,
            'total': total,
            'total_pages': total_pages,
        }

    def list_all_appointments(
        self,
        *,
        query: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Cross-member appointment listing for admin/support views.

        Joins ``appointment_claims`` so the response includes claimed-by data
        on every row. Useful for admin Dashboard 'pending claims' filters.
        """
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, 100))
        search = (query or '').strip().lower()
        status_clean = (status_filter or '').strip().lower()
        if self.using_db:
            params: list[Any] = []
            where: list[str] = []
            if status_clean:
                where.append('LOWER(a.status) = %s')
                params.append(status_clean)
            if search:
                where.append("(CAST(a.id AS TEXT) ILIKE %s OR a.service_type ILIKE %s OR COALESCE(a.service_area, '') ILIKE %s OR a.status ILIKE %s)")
                match = f'%{search}%'
                params.extend([match, match, match, match])
            where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
            total_row = self.fetch_one(
                f'SELECT COUNT(*) AS count FROM appointment_schema.appointments a {where_sql}',
                tuple(params),
            )
            params.extend([safe_page_size, (safe_page - 1) * safe_page_size])
            items = self.fetch_all(
                f'''
                SELECT {_APPOINTMENT_SELECT_COLUMNS}
                {_APPOINTMENT_SELECT_FROM}
                {where_sql}
                ORDER BY a.requested_date DESC, a.id DESC
                LIMIT %s OFFSET %s
                ''',
                tuple(params),
            )
            total = int(total_row['count']) if total_row else 0
        else:
            rows = self.memory.list(
                self._memory_key('appointments'),
                sort_key=lambda row: (row.get('requested_date'), row['id']),
                reverse=True,
            )
            if status_clean:
                rows = [row for row in rows if str(row.get('status', '')).lower() == status_clean]
            if search:
                rows = [row for row in rows if self._matches(row, search)]
            total = len(rows)
            start = (safe_page - 1) * safe_page_size
            items = [self._with_claim_metadata(row) for row in rows[start:start + safe_page_size]]
        total_pages = max(1, (total + safe_page_size - 1) // safe_page_size)
        return {
            'items': items,
            'page': safe_page,
            'page_size': safe_page_size,
            'total': total,
            'total_pages': total_pages,
        }

    def _matches_service_type(self, row: dict[str, Any], service_type: str) -> bool:
        if not service_type:
            return True
        return str(row.get('service_type', '')).strip().lower() == service_type

    def get_appointment(self, appointment_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                f'''
                SELECT {_APPOINTMENT_SELECT_COLUMNS}
                {_APPOINTMENT_SELECT_FROM}
                WHERE a.id = %s
                ''',
                (appointment_id,),
            )
        else:
            row = self.memory.get(self._memory_key('appointments'), appointment_id)
            if row is not None:
                row = self._with_claim_metadata(row)
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
            self.execute(
                f'''
                UPDATE appointment_schema.appointments
                SET {', '.join(assignments)}
                WHERE id = %s
                ''',
                tuple(values),
            )
            return self.get_appointment(appointment_id)
        updates['updated_at'] = now_utc()
        updated = self.memory.update(self._memory_key('appointments'), appointment_id, updates)
        assert updated is not None
        return self._with_claim_metadata(updated)

    def cancel_appointment(self, appointment_id: int) -> dict[str, Any]:
        self.get_appointment(appointment_id)
        if self.using_db:
            self.execute(
                '''
                UPDATE appointment_schema.appointments
                SET status = 'cancelled', cancelled_at = %s, updated_at = %s
                WHERE id = %s
                ''',
                (now_utc(), now_utc(), appointment_id),
            )
            return self.get_appointment(appointment_id)
        updated = self.memory.update(
            self._memory_key('appointments'),
            appointment_id,
            {'status': 'cancelled', 'cancelled_at': now_utc(), 'updated_at': now_utc()},
        )
        assert updated is not None
        return self._with_claim_metadata(updated)

    def attach_slack_message(self, appointment_id: int, channel_id: str, message_ts: str) -> dict[str, Any]:
        """Persist the Slack message coordinates onto the appointment row."""
        if self.using_db:
            self.execute(
                '''
                UPDATE appointment_schema.appointments
                SET slack_channel_id = %s, slack_message_ts = %s, updated_at = %s
                WHERE id = %s
                ''',
                (channel_id, message_ts, now_utc(), appointment_id),
            )
            return self.get_appointment(appointment_id)
        updated = self.memory.update(
            self._memory_key('appointments'),
            appointment_id,
            {'slack_channel_id': channel_id, 'slack_message_ts': message_ts, 'updated_at': now_utc()},
        )
        assert updated is not None
        return self._with_claim_metadata(updated)

    def claim_appointment_via_slack(
        self,
        appointment_id: int,
        *,
        slack_user_id: str,
        slack_user_name: str | None,
        slack_team_id: str | None,
        slack_channel_id: str | None,
        slack_message_ts: str | None,
    ) -> dict[str, Any]:
        """Record a Slack-originated claim and bump the appointment to status='claimed'.

        Idempotent: a second click returns the existing claim with
        ``already_claimed=True`` and does *not* re-bump the status row, so the
        ``updated_at`` timestamp reflects the moment of first claim.
        """
        # Make sure the appointment exists (raises 404 otherwise).
        self.get_appointment(appointment_id)
        if self.using_db:
            existing = self.fetch_one(
                'SELECT id, appointment_id, slack_user_id, slack_user_name, claimed_at '
                'FROM appointment_schema.appointment_claims WHERE appointment_id = %s',
                (appointment_id,),
            )
            if existing:
                return {
                    'appointment': self.get_appointment(appointment_id),
                    'claim': existing,
                    'already_claimed': True,
                }
            claim = self.fetch_one(
                '''
                INSERT INTO appointment_schema.appointment_claims (
                    appointment_id, slack_user_id, slack_user_name, slack_team_id,
                    slack_channel_id, slack_message_ts
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, appointment_id, slack_user_id, slack_user_name, slack_team_id,
                          slack_channel_id, slack_message_ts, claimed_at
                ''',
                (
                    appointment_id,
                    slack_user_id,
                    slack_user_name,
                    slack_team_id,
                    slack_channel_id,
                    slack_message_ts,
                ),
            )
            self.execute(
                '''
                UPDATE appointment_schema.appointments
                SET status = 'claimed', updated_at = %s
                WHERE id = %s
                ''',
                (now_utc(), appointment_id),
            )
            return {
                'appointment': self.get_appointment(appointment_id),
                'claim': claim,
                'already_claimed': False,
            }

        existing_mem = self.memory.list(
            self._memory_key('appointment_claims'),
            predicate=lambda row: row['appointment_id'] == appointment_id,
        )
        if existing_mem:
            return {
                'appointment': self.get_appointment(appointment_id),
                'claim': existing_mem[0],
                'already_claimed': True,
            }
        claim = self.memory.insert(
            self._memory_key('appointment_claims'),
            {
                'appointment_id': appointment_id,
                'slack_user_id': slack_user_id,
                'slack_user_name': slack_user_name,
                'slack_team_id': slack_team_id,
                'slack_channel_id': slack_channel_id,
                'slack_message_ts': slack_message_ts,
                'claimed_at': now_utc(),
            },
        )
        self.memory.update(
            self._memory_key('appointments'),
            appointment_id,
            {'status': 'claimed', 'updated_at': now_utc()},
        )
        return {
            'appointment': self.get_appointment(appointment_id),
            'claim': claim,
            'already_claimed': False,
        }

    def _with_claim_metadata(self, row: dict[str, Any]) -> dict[str, Any]:
        """Memory-backend equivalent of the SQL LEFT JOIN to appointment_claims."""
        if not row:
            return row
        merged = dict(row)
        claims = self.memory.list(
            self._memory_key('appointment_claims'),
            predicate=lambda r: r['appointment_id'] == row.get('id'),
        )
        if claims:
            claim = claims[0]
            merged['claimed_by_slack_user_id'] = claim.get('slack_user_id')
            merged['claimed_by_slack_user_name'] = claim.get('slack_user_name')
            merged['claimed_at'] = claim.get('claimed_at')
        else:
            merged.setdefault('claimed_by_slack_user_id', None)
            merged.setdefault('claimed_by_slack_user_name', None)
            merged.setdefault('claimed_at', None)
        return merged

    @staticmethod
    def _matches(row: dict[str, Any], search: str) -> bool:
        if not search:
            return True
        haystack = ' '.join(
            str(row.get(field) or '')
            for field in ('id', 'service_type', 'service_area', 'status')
        ).lower()
        return search in haystack
