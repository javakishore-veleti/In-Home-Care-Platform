from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from shared.auth import create_access_token, decode_access_token, hash_password, hash_token, verify_password
from shared.storage import BaseStore, now_utc

from .schemas import SigninRequest, SignupRequest


class AuthStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('auth')

    def create_user(self, payload: SignupRequest) -> dict[str, Any]:
        email = payload.email.lower()
        if self.using_db:
            existing = self.fetch_one(
                'SELECT id FROM auth_schema.users WHERE LOWER(email) = LOWER(%s)',
                (email,),
            )
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='An account with this email already exists.')
            row = self.fetch_one(
                '''
                INSERT INTO auth_schema.users (email, hashed_password, role, is_active, created_at)
                VALUES (%s, %s, 'member', TRUE, %s)
                RETURNING id, email, role, is_active, created_at
                ''',
                (email, hash_password(payload.password), now_utc()),
            )
            return row

        existing = next(
            (row for row in self.memory.list(self._memory_key('users')) if row['email'].lower() == email),
            None,
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='An account with this email already exists.')
        return self.memory.insert(
            self._memory_key('users'),
            {
                'email': email,
                'hashed_password': hash_password(payload.password),
                'role': 'member',
                'is_active': True,
                'created_at': now_utc(),
            },
        )

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        if self.using_db:
            return self.fetch_one(
                '''
                SELECT id, email, hashed_password, role, is_active, created_at
                FROM auth_schema.users
                WHERE LOWER(email) = LOWER(%s)
                ''',
                (email.lower(),),
            )
        return next(
            (row for row in self.memory.list(self._memory_key('users')) if row['email'].lower() == email.lower()),
            None,
        )

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        if self.using_db:
            return self.fetch_one(
                '''
                SELECT id, email, hashed_password, role, is_active, created_at
                FROM auth_schema.users
                WHERE id = %s
                ''',
                (user_id,),
            )
        return self.memory.get(self._memory_key('users'), user_id)

    def signin(self, payload: SigninRequest) -> dict[str, Any]:
        user = self.get_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user['hashed_password']):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password.')
        if not user.get('is_active', True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='This account is inactive.')

        token, expires_at = create_access_token(user)
        session_record = {
            'user_id': user['id'],
            'token_hash': hash_token(token),
            'expires_at': expires_at,
            'created_at': now_utc(),
        }
        if self.using_db:
            self.fetch_one(
                '''
                INSERT INTO auth_schema.sessions (user_id, token_hash, expires_at, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                ''',
                (
                    session_record['user_id'],
                    session_record['token_hash'],
                    session_record['expires_at'],
                    session_record['created_at'],
                ),
            )
        else:
            self.memory.insert(self._memory_key('sessions'), session_record)
        return {
            'access_token': token,
            'token_type': 'bearer',
            'expires_at': expires_at,
            'user': self._public_user(user),
        }

    def get_current_user(self, token: str) -> dict[str, Any]:
        payload = decode_access_token(token)
        user = self.get_user_by_id(int(payload['sub']))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found for token.')
        return self._public_user(user)

    @staticmethod
    def _public_user(user: dict[str, Any]) -> dict[str, Any]:
        return {
            'id': user['id'],
            'email': user['email'],
            'role': user.get('role', 'member'),
            'is_active': user.get('is_active', True),
            'created_at': user.get('created_at'),
        }
