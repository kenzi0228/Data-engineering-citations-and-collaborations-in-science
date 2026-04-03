from __future__ import annotations

from collections import Counter
from typing import Any


def _normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def build_publication_profile(rows: list[dict[str, Any]], title_query: str) -> dict[str, Any]:
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

    venue_counter: Counter[str] = Counter()
    fos_counter: Counter[str] = Counter()
    author_counter: Counter[str] = Counter()

    for row in rows:
        venue = row.get("venue_name")
        if venue:
            venue_counter[str(venue)] += 1

        for fos in _normalize_list(row.get("fos")):
            fos = str(fos).strip()
            if fos:
                fos_counter[fos] += 1

        for author in _normalize_list(row.get("author_names")):
            author = str(author).strip()
            if author:
                author_counter[author] += 1

    return {
        "title_query": title_query,
        "publication_count": len(rows),
        "min_year": min(years) if years else None,
        "max_year": max(years) if years else None,
        "total_citations": total_citations,
        "top_venues": [
            {"venue_name": name, "publication_count": count}
            for name, count in venue_counter.most_common(10)
        ],
        "top_fos": [
            {"fos_name": name, "publication_count": count}
            for name, count in fos_counter.most_common(10)
        ],
        "top_authors": [
            {"author_name": name, "publication_count": count}
            for name, count in author_counter.most_common(10)
        ],
    }
