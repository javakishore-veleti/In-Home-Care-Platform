from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault('IHCP_FORCE_MEMORY_STORAGE', '1')

for relative in [
    'middleware',
    'middleware/Microservices/auth_svc/src',
    'middleware/Microservices/member_svc/src',
    'middleware/Microservices/appointment_svc/src',
    'middleware/Microservices/visit_management_svc/src',
    'middleware/Microservices/api_gateway/src',
]:
    path = str(REPO_ROOT / relative)
    if path not in sys.path:
        sys.path.insert(0, path)

from shared.storage import reset_db_availability_cache, reset_memory_backend


@pytest.fixture(autouse=True)
def reset_storage() -> None:
    os.environ['IHCP_FORCE_MEMORY_STORAGE'] = '1'
    reset_db_availability_cache()
    reset_memory_backend()
    yield
    reset_db_availability_cache()
    reset_memory_backend()
