"""Read system-vector-dbs.json to determine which vector DBs are enabled."""
from __future__ import annotations

import json
import os
from typing import Any

from ..common.exceptions import VectorDbConfigError

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "system-vector-dbs.json",
)


def load_vector_db_config(path: str | None = None) -> dict[str, Any]:
    config_path = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(config_path):
        raise VectorDbConfigError(f"Config not found: {config_path}")
    with open(config_path) as f:
        return json.load(f)


def get_enabled_vector_dbs(path: str | None = None) -> list[str]:
    config = load_vector_db_config(path)
    return [
        name for name, settings in config.get("vector_dbs", {}).items()
        if settings.get("enabled", False)
    ]
