from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any


def _safe_json_loads(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except Exception:
            return value
    return value


def _parse_duckdb_list_string(text: str) -> list[str]:
    text = text.strip()
    if not (text.startswith("[") and text.endswith("]")):
        return [text] if text else []

    inner = text[1:-1].strip()
    if not inner:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass

    quoted_items = re.findall(r"'([^']*)'|\"([^\"]*)\"", inner)
    flattened = []
    for left, right in quoted_items:
        value = (left or right).strip()
        if value:
            flattened.append(value)

    if flattened:
        return flattened

    parts = [part.strip() for part in re.split(r"\s{2,}|\s*,\s*", inner) if part.strip()]
    return parts


def _normalize_list(value: Any) -> list[Any]:
    value = _safe_json_loads(value)

    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)

    # numpy/pandas array-like fallback
    if hasattr(value, "tolist") and not isinstance(value, str):
        converted = value.tolist()
        if isinstance(converted, list):
            return converted
        return [converted]

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("[") and stripped.endswith("]"):
            return _parse_duckdb_list_string(stripped)
        return [stripped]

    return [value]


def _match_author_name(candidate: str, author_query: str) -> bool:
    candidate = (candidate or "").strip().lower()
    author_query = (author_query or "").strip().lower()
    return bool(candidate) and bool(author_query) and author_query in candidate


def _extract_matched_author_names(rows: list[dict[str, Any]], author_query: str) -> list[str]:
    matched = set()
    for row in rows:
        for name in _normalize_list(row.get("author_names")):
            name = str(name).strip()
            if _match_author_name(name, author_query):
                matched.add(name)
    return sorted(matched)


def extract_top_collaborators(
    rows: list[dict[str, Any]],
    author_query: str,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    collaborator_counter: Counter[str] = Counter()

    for row in rows:
        names = []
        seen_local = set()

        for name in _normalize_list(row.get("author_names")):
            name = str(name).strip()
            if not name or name in seen_local:
                continue
            seen_local.add(name)
            names.append(name)

        for name in names:
            if _match_author_name(name, author_query):
                continue
            collaborator_counter[name] += 1

    return [
        {"collaborator_name": name, "publication_count": count}
        for name, count in collaborator_counter.most_common(top_n)
    ]


def extract_top_venues(
    rows: list[dict[str, Any]],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        venue = row.get("venue_name")
        if venue:
            venue_str = str(venue).strip()
            if venue_str and venue_str.lower() != "nan":
                counter[venue_str] += 1
    return [{"venue_name": name, "publication_count": count} for name, count in counter.most_common(top_n)]


def extract_top_fos(
    rows: list[dict[str, Any]],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        for fos in _normalize_list(row.get("fos")):
            fos = str(fos).strip()
            if fos:
                counter[fos] += 1
    return [{"fos_name": name, "publication_count": count} for name, count in counter.most_common(top_n)]


def build_author_profile(
    rows: list[dict[str, Any]],
    author_query: str,
) -> dict[str, Any]:
    matched_author_names = _extract_matched_author_names(rows, author_query)

    years = [
        int(row["year_clean"])
        for row in rows
        if row.get("year_clean") is not None and str(row.get("year_clean")).strip() != ""
    ]
    total_citations = sum(
        int(row.get("n_citation") or 0)
        for row in rows
        if row.get("n_citation") is not None and str(row.get("n_citation")).strip() != ""
    )

    return {
        "author_query": author_query,
        "matched_author_names": matched_author_names,
        "publication_count": len(rows),
        "min_year": min(years) if years else None,
        "max_year": max(years) if years else None,
        "total_citations": total_citations,
        "top_venues": extract_top_venues(rows, top_n=10),
        "top_fos": extract_top_fos(rows, top_n=10),
        "top_collaborators": extract_top_collaborators(rows, author_query=author_query, top_n=10),
    }
