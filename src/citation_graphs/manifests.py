from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_pipeline_run(
    manifest_path: str | Path,
    stage: str,
    status: str,
    parameters: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "status": status,
        "parameters": parameters or {},
        "outputs": outputs or {},
        "message": message or "",
    }

    with manifest_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def read_pipeline_runs(manifest_path: str | Path) -> list[dict[str, Any]]:
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with manifest_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return rows
