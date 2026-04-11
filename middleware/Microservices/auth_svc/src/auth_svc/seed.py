"""Seed internal-staff users on auth_svc startup.

These users represent the platform's *employees* (not members):
admin, support, field officer, care planner, auditor. They never have a
member record. Sign-up is intentionally not exposed for these accounts —
they exist only because this seeding step inserts them on first run.

The seeding is idempotent: a row is created only if no user with the same
email already exists, so re-running the service does not clobber a
manually-rotated password.

Local-development credentials below are intentionally weak so they can be
typed in by hand. They MUST be overridden in any non-local environment via
the IHCP_INTERNAL_USERS_SEED_OVERRIDE env var (a JSON list with the same
shape as INTERNAL_USERS).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from .store import AuthStore

log = logging.getLogger(__name__)

INTERNAL_USERS: list[dict[str, str]] = [
    {
        'email': 'admin01@inhomecare.local',
        'password': 'Admin@123',
        'role': 'admin',
    },
    {
        'email': 'supportuser01@inhomecare.local',
        'password': 'Support@123',
        'role': 'support',
    },
    {
        'email': 'fieldofficer01@inhomecare.local',
        'password': 'Field@123',
        'role': 'field_officer',
    },
    {
        'email': 'careplanner01@inhomecare.local',
        'password': 'Plan@123',
        'role': 'care_planner',
    },
    {
        'email': 'auditor01@inhomecare.local',
        'password': 'Audit@123',
        'role': 'auditor',
    },
]


def _resolve_seed_specs() -> list[dict[str, str]]:
    override = os.getenv('IHCP_INTERNAL_USERS_SEED_OVERRIDE')
    if not override:
        return INTERNAL_USERS
    try:
        parsed: Any = json.loads(override)
    except json.JSONDecodeError as exc:
        log.warning('seed.override_invalid_json', extra={'error': str(exc)})
        return INTERNAL_USERS
    if not isinstance(parsed, list):
        log.warning('seed.override_invalid_shape')
        return INTERNAL_USERS
    return [spec for spec in parsed if isinstance(spec, dict) and {'email', 'password', 'role'} <= spec.keys()]


def seed_internal_users() -> None:
    store = AuthStore()
    specs = _resolve_seed_specs()
    created = 0
    for spec in specs:
        try:
            user = store.ensure_internal_user(
                email=spec['email'],
                password=spec['password'],
                role=spec['role'],
            )
            log.info('seed.user_ready', extra={'email': user.get('email'), 'role': user.get('role')})
            created += 1
        except Exception as exc:  # pragma: no cover - never break startup on seed failure
            log.warning('seed.user_failed', extra={'email': spec.get('email'), 'error': str(exc)})
    log.info('seed.summary', extra={'requested': len(specs), 'processed': created})
