from __future__ import annotations

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


def test_search_author_records_multi_year_filter_file(mini_parquet) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice"],
        limit=50,
        match_mode="or",
        start_year=2020,
        end_year=2020,
    )
    assert len(rows) == 2


def test_search_author_records_multi_year_filter_empty(mini_parquet) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice"],
        limit=50,
        match_mode="or",
        start_year=2021,
        end_year=2021,
    )
    assert len(rows) == 0
