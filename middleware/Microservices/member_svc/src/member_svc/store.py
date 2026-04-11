from __future__ import annotations

import json
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
