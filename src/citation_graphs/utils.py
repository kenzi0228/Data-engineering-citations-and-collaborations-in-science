from __future__ import annotations

from pathlib import Path
from typing import Any


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def normalize_network_type(value: str) -> str:
    normalized = value.strip().lower()

    mapping = {
        "1": "citation",
        "2": "collaboration",
        "citation": "citation",
        "collaboration": "collaboration",
    }

    if normalized not in mapping:
        raise ValueError("network_type must be 'citation', 'collaboration', '1', or '2'")

    return mapping[normalized]


def safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default