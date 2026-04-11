"""File discovery and counting utilities for the collections directory."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator


SUPPORTED_EXTENSIONS = {
    "pdf": [".pdf"],
    "docs": [".doc", ".docx", ".odt", ".rtf"],
    "excel": [".xls", ".xlsx", ".ods"],
    "images": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"],
    "csv": [".csv", ".tsv"],
}

ALL_EXTENSIONS = {ext for exts in SUPPORTED_EXTENSIONS.values() for ext in exts}


def discover_files(base_path: str) -> Iterator[tuple[str, str, Path]]:
    """Yield (category, format, file_path) for every ingestable file."""
    base = Path(base_path)
    if not base.exists():
        return
    for category_dir in sorted(base.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        for format_dir in sorted(category_dir.iterdir()):
            if not format_dir.is_dir():
                continue
            fmt = format_dir.name
            for file_path in sorted(format_dir.iterdir()):
                if file_path.is_file() and file_path.suffix.lower() in ALL_EXTENSIONS:
                    yield category, fmt, file_path


def count_files(base_path: str) -> int:
    return sum(1 for _ in discover_files(base_path))
