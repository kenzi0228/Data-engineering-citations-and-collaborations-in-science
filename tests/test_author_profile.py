from __future__ import annotations

from citation_graphs.author_profile import (
    build_author_profile,
    extract_top_collaborators,
    extract_top_fos,
    extract_top_venues,
)
from citation_graphs.search import search_author_records


def test_extract_top_collaborators(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="alice", limit=50)
    collaborators = extract_top_collaborators(rows, author_query="alice", top_n=10)

    names = [row["collaborator_name"] for row in collaborators]
    assert "Bob Ray" in names
    assert "Charlie Lin" in names


def test_extract_top_venues(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="alice", limit=50)
    venues = extract_top_venues(rows, top_n=10)

    assert venues[0]["venue_name"] in {"Journal A", "Workshop C"}


def test_extract_top_fos(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="alice", limit=50)
    fos = extract_top_fos(rows, top_n=10)

    names = [row["fos_name"] for row in fos]
    assert "Data Science" in names


def test_build_author_profile(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="alice", limit=50)
    profile = build_author_profile(rows, author_query="alice")

    assert profile["author_query"] == "alice"
    assert profile["publication_count"] == 2
    assert profile["min_year"] == 2020
    assert profile["max_year"] == 2020
    assert profile["total_citations"] == 17
    assert "Alice Doe" in profile["matched_author_names"]
    assert len(profile["top_collaborators"]) >= 2
