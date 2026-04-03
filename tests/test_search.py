from __future__ import annotations

from citation_graphs.search import resolve_search_input, search_author_records, slugify


def test_slugify() -> None:
    assert slugify("Ian McCulloh") == "ian_mcculloh"
    assert slugify("Jean-Pierre LÃ©vy") == "jean_pierre_l_vy"


def test_resolve_search_input_sample(mini_parquet) -> None:
    resolved = resolve_search_input(source_mode="sample", sample_path=mini_parquet)
    assert resolved == mini_parquet


def test_search_author_records_case_insensitive(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="alice", limit=50)
    assert len(rows) == 2
    assert any(row["title"] == "Graph Analytics for Science" for row in rows)


def test_search_author_records_partial_match(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="char", limit=50)
    assert len(rows) == 1
    assert rows[0]["title"] == "Applied Collaboration Networks"


def test_search_author_records_no_match(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="zzz", limit=50)
    assert rows == []


def test_search_author_records_limit(mini_parquet) -> None:
    rows = search_author_records(mini_parquet, author_query="bob", limit=1)
    assert len(rows) == 1
