from __future__ import annotations

import html
import json
import unicodedata
from pathlib import Path

import duckdb


def _readable_input(path: Path) -> str:
    path = Path(path)
    if path.is_dir():
        return str(path / "**" / "*.parquet")
    return str(path)


def _clean_author_name(name: str) -> str:
    value = html.unescape(str(name))
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\uFFFD", "")
    value = " ".join(value.split())
    return value.strip()


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

    authors = []
    for row in rows:
        if not row or row[0] is None:
            continue
        cleaned = _clean_author_name(row[0])
        if cleaned:
            authors.append(cleaned)

    return sorted(set(authors))


def save_author_index(authors: list[str], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = sorted(set(_clean_author_name(author) for author in authors if str(author).strip()))
    output_path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def load_author_index(index_path: str | Path) -> list[str]:
    index_path = Path(index_path)
    if not index_path.exists():
        return []
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [_clean_author_name(item) for item in data if _clean_author_name(item)]


def suggest_authors(authors: list[str], query: str, limit: int = 20) -> list[str]:
    query = _clean_author_name(query).lower()
    if not query:
        return []

    starts = []
    word_match = []
    contains = []

    for name in authors:
        lowered = _clean_author_name(name).lower()

        if lowered.startswith(query):
            starts.append(name)
            continue

        words = lowered.replace("-", " ").replace("_", " ").split()
        if any(word.startswith(query) for word in words):
            word_match.append(name)
            continue

        if query in lowered:
            contains.append(name)

    starts = sorted(set(starts))
    word_match = sorted(set(word_match) - set(starts))
    contains = sorted(set(contains) - set(starts) - set(word_match))

    return (starts + word_match + contains)[:limit]
