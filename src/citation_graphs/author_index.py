from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb


def _readable_input(path: Path) -> str:
    path = Path(path)
    if path.is_dir():
        return str(path / "**" / "*.parquet")
    return str(path)


def extract_author_index(input_path: str | Path) -> list[str]:
    input_path = Path(input_path)
    source = _readable_input(input_path)

    query = f"""
    SELECT DISTINCT author_name
    FROM (
        SELECT UNNEST(author_names) AS author_name
        FROM read_parquet('{source}')
    )
    WHERE author_name IS NOT NULL
      AND trim(author_name) <> ''
      AND lower(trim(author_name)) <> 'nan'
    ORDER BY author_name
    """

    con = duckdb.connect(database=":memory:")
    try:
        rows = con.execute(query).fetchall()
    finally:
        con.close()

    authors = [str(row[0]).strip() for row in rows if row and row[0] is not None and str(row[0]).strip()]
    return authors


def save_author_index(authors: list[str], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(sorted(set(authors)), indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def load_author_index(index_path: str | Path) -> list[str]:
    index_path = Path(index_path)
    if not index_path.exists():
        return []
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [str(item).strip() for item in data if str(item).strip()]


def suggest_authors(authors: list[str], query: str, limit: int = 20) -> list[str]:
    query = (query or "").strip().lower()
    if not query:
        return authors[:limit]

    starts = [name for name in authors if name.lower().startswith(query)]
    contains = [name for name in authors if query in name.lower() and name not in starts]
    return (starts + contains)[:limit]
