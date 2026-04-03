from __future__ import annotations

from citation_graphs.author_index import suggest_authors
from citation_graphs.search import search_author_records_multi


def test_search_author_records_multi_or(mini_parquet) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice", "bob"],
        limit=50,
        match_mode="or",
    )
    assert len(rows) == 3


def test_search_author_records_multi_and(mini_parquet) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice", "bob"],
        limit=50,
        match_mode="and",
    )
    assert len(rows) == 1
    assert rows[0]["title"] == "Graph Analytics for Science"


def test_search_author_records_multi_and_second_pair(mini_parquet) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice", "charlie"],
        limit=50,
        match_mode="and",
    )
    assert len(rows) == 1
    assert rows[0]["title"] == "Applied Collaboration Networks"


def test_suggest_authors() -> None:
    authors = [
        "Alice Doe",
        "Bob Ray",
        "Charlie Lin",
        "Ian McCulloh",
        "Ian Goodfellow",
    ]
    suggestions = suggest_authors(authors, "ian", limit=10)
    assert "Ian McCulloh" in suggestions
    assert "Ian Goodfellow" in suggestions
