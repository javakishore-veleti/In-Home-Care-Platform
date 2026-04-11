from __future__ import annotations

import json
import math
from typing import Any

from fastapi import HTTPException, status

from shared.storage import BaseStore, now_utc

from .schemas import AddressCreate, AddressUpdate, MemberCreate, MemberUpdate


class MemberStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('member')

    def create_member(self, payload: MemberCreate) -> dict[str, Any]:
        existing = self.get_member_by_user_id(payload.user_id)
        if existing:
            return existing
        if self.using_db:
            return self.fetch_one(
                '''
                INSERT INTO member_schema.members (
                    user_id, tenant_id, first_name, last_name, email, phone, dob, address,
                    insurance_id, preferences, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CAST(%s AS JSONB), %s, %s)
                RETURNING id, user_id, tenant_id, first_name, last_name, email, phone, dob,
                          insurance_id, preferences, created_at, updated_at
                ''',
                (
                    payload.user_id,
                    payload.tenant_id,
                    payload.first_name,
                    payload.last_name,
                    str(payload.email),
                    payload.phone,
                    payload.dob,
                    None,
                    payload.insurance_id,
                    json.dumps(payload.preferences),
                    now_utc(),
                    now_utc(),
                ),
            )
        return self.memory.insert(
            self._memory_key('members'),
            {
                'user_id': payload.user_id,
                'tenant_id': payload.tenant_id,
                'first_name': payload.first_name,
                'last_name': payload.last_name,
                'email': str(payload.email),
                'phone': payload.phone,
                'dob': payload.dob,
                'insurance_id': payload.insurance_id,
                'preferences': payload.preferences,
                'created_at': now_utc(),
                'updated_at': now_utc(),
            },
        )

    def get_member(self, member_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, user_id, tenant_id, first_name, last_name, email, phone, dob,
                       insurance_id, preferences, created_at, updated_at
                FROM member_schema.members
                WHERE id = %s
                ''',
                (member_id,),
            )
        else:
            row = self.memory.get(self._memory_key('members'), member_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Member profile not found.')
        row.setdefault('preferences', {})
        return row

    def list_all_members(
        self,
        *,
        query: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Cross-member listing for admin/support views. Paginated, optional search."""
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, 100))
        search = (query or '').strip().lower()
        if self.using_db:
            params: list[Any] = []
            where_sql = ''
            if search:
                where_sql = (
                    "WHERE LOWER(first_name) ILIKE %s OR LOWER(last_name) ILIKE %s "
                    "OR LOWER(email) ILIKE %s OR CAST(id AS TEXT) ILIKE %s"
                )
                match = f'%{search}%'
                params.extend([match, match, match, match])
            total_row = self.fetch_one(
                f'SELECT COUNT(*) AS count FROM member_schema.members {where_sql}',
                tuple(params),
            )
            params.extend([safe_page_size, (safe_page - 1) * safe_page_size])
            items = self.fetch_all(
                f'''
                SELECT id, user_id, tenant_id, first_name, last_name, email, phone, dob,
                       insurance_id, preferences, created_at, updated_at
                FROM member_schema.members
                {where_sql}
                ORDER BY id DESC
                LIMIT %s OFFSET %s
                ''',
                tuple(params),
            )
            for row in items:
                row.setdefault('preferences', {})
            total = int(total_row['count']) if total_row else 0
        else:
            rows = self.memory.list(self._memory_key('members'))
            if search:
                def _match(row: dict[str, Any]) -> bool:
                    haystack = ' '.join(
                        str(row.get(field) or '') for field in ('id', 'first_name', 'last_name', 'email')
                    ).lower()
                    return search in haystack
                rows = [row for row in rows if _match(row)]
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

    def get_member_by_user_id(self, user_id: int) -> dict[str, Any] | None:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, user_id, tenant_id, first_name, last_name, email, phone, dob,
                       insurance_id, preferences, created_at, updated_at
                FROM member_schema.members
                WHERE user_id = %s
                ''',
                (user_id,),
            )
            if row:
                row.setdefault('preferences', {})
            return row
        return next(
            (row for row in self.memory.list(self._memory_key('members')) if row['user_id'] == user_id),
            None,
        )

    def update_member(self, member_id: int, payload: MemberUpdate) -> dict[str, Any]:
        member = self.get_member(member_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return member
        if self.using_db:
            assignments: list[str] = []
            values: list[Any] = []
            for field, value in updates.items():
                if field == 'preferences':
                    assignments.append('preferences = CAST(%s AS JSONB)')
                    values.append(json.dumps(value))
                else:
                    assignments.append(f'{field} = %s')
                    values.append(value)
            assignments.append('updated_at = %s')
            values.append(now_utc())
            values.append(member_id)
            return self.fetch_one(
                f'''
                UPDATE member_schema.members
                SET {', '.join(assignments)}
                WHERE id = %s
                RETURNING id, user_id, tenant_id, first_name, last_name, email, phone, dob,
                          insurance_id, preferences, created_at, updated_at
                ''',
                tuple(values),
            )
        updates['updated_at'] = now_utc()
        updated = self.memory.update(self._memory_key('members'), member_id, updates)
        assert updated is not None
        return updated

    def list_addresses(self, member_id: int) -> list[dict[str, Any]]:
        self.get_member(member_id)
        if self.using_db:
            return self.fetch_all(
                '''
                SELECT id, member_id, label, line1, line2, city, state, postal_code,
                       instructions, is_default, created_at, updated_at
                FROM member_schema.member_addresses
                WHERE member_id = %s
                ORDER BY is_default DESC, id ASC
                ''',
                (member_id,),
            )
        return self.memory.list(
            self._memory_key('addresses'),
            predicate=lambda row: row['member_id'] == member_id,
            sort_key=lambda row: (not row.get('is_default', False), row['id']),
        )

    def search_addresses(
        self,
        *,
        member_id: int,
        query: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        self.get_member(member_id)
        safe_page = max(1, page)
        safe_page_size = max(1, min(page_size, 50))
        search = (query or '').strip().lower()
        if self.using_db:
            params: list[Any] = [member_id]
            where = ['member_id = %s']
            if search:
                where.append(
                    "(CAST(id AS TEXT) ILIKE %s OR label ILIKE %s OR line1 ILIKE %s OR "
                    "COALESCE(line2, '') ILIKE %s OR city ILIKE %s OR state ILIKE %s OR "
                    "postal_code ILIKE %s OR COALESCE(instructions, '') ILIKE %s)"
                )
                match = f'%{search}%'
                params.extend([match, match, match, match, match, match, match, match])
            where_sql = ' AND '.join(where)
            total_row = self.fetch_one(
                f'SELECT COUNT(*) AS count FROM member_schema.member_addresses WHERE {where_sql}',
                tuple(params),
            )
            total = int(total_row['count']) if total_row else 0
            total_pages = max(1, math.ceil(total / safe_page_size))
            current_page = min(safe_page, total_pages)
            items = self.fetch_all(
                f'''
                SELECT id, member_id, label, line1, line2, city, state, postal_code,
                       instructions, is_default, created_at, updated_at
                FROM member_schema.member_addresses
                WHERE {where_sql}
                ORDER BY is_default DESC, id DESC
                LIMIT %s OFFSET %s
                ''',
                tuple([*params, safe_page_size, (current_page - 1) * safe_page_size]),
            )
        else:
            items = self.memory.list(
                self._memory_key('addresses'),
                predicate=lambda row: row['member_id'] == member_id and self._address_matches(row, search),
                sort_key=lambda row: (row.get('is_default', False), row['id']),
                reverse=True,
            )
            total = len(items)
            total_pages = max(1, math.ceil(total / safe_page_size))
            current_page = min(safe_page, total_pages)
            start = (current_page - 1) * safe_page_size
            items = items[start:start + safe_page_size]
        return {
            'items': items,
            'page': current_page,
            'page_size': safe_page_size,
            'total': total,
            'total_pages': total_pages,
        }

    def create_address(self, member_id: int, payload: AddressCreate) -> dict[str, Any]:
        self.get_member(member_id)
        existing = self.list_addresses(member_id)
        is_default = payload.is_default or not existing
        if is_default:
            self._clear_default_addresses(member_id)
        record = {
            'member_id': member_id,
            'label': payload.label,
            'line1': payload.line1,
            'line2': payload.line2,
            'city': payload.city,
            'state': payload.state,
            'postal_code': payload.postal_code,
            'instructions': payload.instructions,
            'is_default': is_default,
            'created_at': now_utc(),
            'updated_at': now_utc(),
        }
        if self.using_db:
            return self.fetch_one(
                '''
                INSERT INTO member_schema.member_addresses (
                    member_id, label, line1, line2, city, state, postal_code,
                    instructions, is_default, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, member_id, label, line1, line2, city, state, postal_code,
                          instructions, is_default, created_at, updated_at
                ''',
                (
                    member_id,
                    record['label'],
                    record['line1'],
                    record['line2'],
                    record['city'],
                    record['state'],
                    record['postal_code'],
                    record['instructions'],
                    record['is_default'],
                    record['created_at'],
                    record['updated_at'],
                ),
            )
        return self.memory.insert(self._memory_key('addresses'), record)

    def update_address(self, member_id: int, address_id: int, payload: AddressUpdate) -> dict[str, Any]:
        address = self._get_address(member_id, address_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return address
        if updates.get('is_default'):
            self._clear_default_addresses(member_id)
        if self.using_db:
            assignments: list[str] = []
            values: list[Any] = []
            for field, value in updates.items():
                assignments.append(f'{field} = %s')
                values.append(value)
            assignments.append('updated_at = %s')
            values.append(now_utc())
            values.extend([address_id, member_id])
            row = self.fetch_one(
                f'''
                UPDATE member_schema.member_addresses
                SET {', '.join(assignments)}
                WHERE id = %s AND member_id = %s
                RETURNING id, member_id, label, line1, line2, city, state, postal_code,
                          instructions, is_default, created_at, updated_at
                ''',
                tuple(values),
            )
            assert row is not None
            return row
        updates['updated_at'] = now_utc()
        updated = self.memory.update(self._memory_key('addresses'), address_id, updates)
        assert updated is not None
        return updated

    def delete_address(self, member_id: int, address_id: int) -> None:
        address = self._get_address(member_id, address_id)
        if self.using_db:
            self.execute(
                'DELETE FROM member_schema.member_addresses WHERE id = %s AND member_id = %s',
                (address_id, member_id),
            )
        else:
            self.memory.delete(self._memory_key('addresses'), address_id)
        if address.get('is_default'):
            remaining = self.list_addresses(member_id)
            if remaining:
                self.set_default_address(member_id, remaining[0]['id'])

    def set_default_address(self, member_id: int, address_id: int) -> dict[str, Any]:
        self._get_address(member_id, address_id)
        self._clear_default_addresses(member_id)
        if self.using_db:
            row = self.fetch_one(
                '''
                UPDATE member_schema.member_addresses
                SET is_default = TRUE, updated_at = %s
                WHERE id = %s AND member_id = %s
                RETURNING id, member_id, label, line1, line2, city, state, postal_code,
                          instructions, is_default, created_at, updated_at
                ''',
                (now_utc(), address_id, member_id),
            )
            assert row is not None
            return row
        updated = self.memory.update(
            self._memory_key('addresses'),
            address_id,
            {'is_default': True, 'updated_at': now_utc()},
        )
        assert updated is not None
        return updated

    def _clear_default_addresses(self, member_id: int) -> None:
        if self.using_db:
            self.execute(
                'UPDATE member_schema.member_addresses SET is_default = FALSE WHERE member_id = %s',
                (member_id,),
            )
            return
        for address in self.list_addresses(member_id):
            if address.get('is_default'):
                self.memory.update(
                    self._memory_key('addresses'),
                    address['id'],
                    {'is_default': False, 'updated_at': now_utc()},
                )

    def _get_address(self, member_id: int, address_id: int) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                SELECT id, member_id, label, line1, line2, city, state, postal_code,
                       instructions, is_default, created_at, updated_at
                FROM member_schema.member_addresses
                WHERE id = %s AND member_id = %s
                ''',
                (address_id, member_id),
            )
        else:
            row = self.memory.get(self._memory_key('addresses'), address_id)
            if row and row['member_id'] != member_id:
                row = None
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Address not found.')
        return row

    def _address_matches(self, row: dict[str, Any], search: str) -> bool:
        if not search:
            return True
        values = [
            row.get('id'),
            row.get('label'),
            row.get('line1'),
            row.get('line2'),
            row.get('city'),
            row.get('state'),
            row.get('postal_code'),
            row.get('instructions'),
        ]
        return any(search in str(value).lower() for value in values if value is not None)
