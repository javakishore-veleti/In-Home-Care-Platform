from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Mapping

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv('IHCP_JWT_SECRET', 'in-home-care-local-secret')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('IHCP_ACCESS_TOKEN_EXPIRE_MINUTES', '720'))
_pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(password, hashed_password)


def create_access_token(user: Mapping[str, Any], expires_minutes: int | None = None) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    payload = {
        'sub': str(user['id']),
        'email': user['email'],
        'role': user.get('role', 'member'),
        'exp': expires_at,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError('Invalid or expired access token.') from exc

    try:
        payload['sub'] = int(payload['sub'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Token subject is invalid.') from exc
    return payload


def hash_token(token: str) -> str:
    return sha256(token.encode('utf-8')).hexdigest()
