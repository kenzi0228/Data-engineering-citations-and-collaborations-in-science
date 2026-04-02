from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb


def build_fos_index(input_dir: str | Path, output_path: str | Path) -> dict[str, Any]:
    input_glob = str(Path(input_dir) / "**" / "*.parquet")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=":memory:")
    query = f"""
        SELECT DISTINCT TRIM(f) AS fos_value
        FROM read_parquet('{input_glob}', hive_partitioning=true),
             UNNEST(fos) AS t(f)
        WHERE f IS NOT NULL
          AND TRIM(f) <> ''
        ORDER BY fos_value
    """
    rows = con.execute(query).fetchall()
    con.close()

    fos_values = [row[0] for row in rows if row[0]]

    payload = {
        "count": len(fos_values),
        "values": fos_values,
        "source": str(Path(input_dir).resolve()),
        "output": str(output_path.resolve()),
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4, ensure_ascii=False)

    return payload


def load_fos_index(index_path: str | Path) -> list[str]:
    index_path = Path(index_path)
    if not index_path.exists():
        return []

    with index_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict):
        values = payload.get("values", [])
        if isinstance(values, list):
            return [str(v) for v in values]

    return []
