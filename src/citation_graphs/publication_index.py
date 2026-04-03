from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path

import duckdb


def _readable_input(path: Path) -> str:
    path = Path(path)
    if path.is_dir():
        return str(path / "**" / "*.parquet")
    return str(path)


def _clean_title(title: str) -> str:
    value = html.unescape(str(title))
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\uFFFD", "")
    value = " ".join(value.split())
    return value.strip()


def extract_publication_index(input_path: str | Path) -> list[str]:
    input_path = Path(input_path)
    source = _readable_input(input_path)

    query = f"""
    SELECT DISTINCT title
    FROM read_parquet('{source}')
    WHERE title IS NOT NULL
      AND trim(title) <> ''
      AND lower(trim(title)) <> 'nan'
    ORDER BY title
    """

    con = duckdb.connect(database=":memory:")
    try:
        rows = con.execute(query).fetchall()
    finally:
        con.close()

    titles = []
    for row in rows:
        if not row or row[0] is None:
            continue
        cleaned = _clean_title(row[0])
        if cleaned:
            titles.append(cleaned)

    return sorted(set(titles))


def save_publication_index(titles: list[str], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = sorted(set(_clean_title(title) for title in titles if str(title).strip()))
    output_path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def load_publication_index(index_path: str | Path) -> list[str]:
    index_path = Path(index_path)
    if not index_path.exists():
        return []
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [_clean_title(item) for item in data if _clean_title(item)]


def suggest_publications(titles: list[str], query: str, limit: int = 20) -> list[str]:
    query = _clean_title(query).lower()
    if not query:
        return []

    starts = []
    word_match = []
    contains = []

    for title in titles:
        lowered = _clean_title(title).lower()

        if lowered.startswith(query):
            starts.append(title)
            continue

        words = re.split(r"[\s\-_:/()]+", lowered)
        if any(word.startswith(query) for word in words if word):
            word_match.append(title)
            continue

        if query in lowered:
            contains.append(title)

    starts = sorted(set(starts))
    word_match = sorted(set(word_match) - set(starts))
    contains = sorted(set(contains) - set(starts) - set(word_match))

    return (starts + word_match + contains)[:limit]
