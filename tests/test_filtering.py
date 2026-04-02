from __future__ import annotations

import duckdb

from citation_graphs.filtering import build_where_clause


def test_build_where_clause_year() -> None:
    clause = build_where_clause(mode="year", year=2020)
    assert clause == "year_clean = 2020"


def test_build_where_clause_range() -> None:
    clause = build_where_clause(mode="range", start_year=2018, end_year=2020)
    assert clause == "year_clean BETWEEN 2018 AND 2020"


def test_build_where_clause_fos() -> None:
    clause = build_where_clause(mode="fos", fos_values=["Data Science", "Graph Theory"])
    assert "lower(f) = 'data science'" in clause
    assert "lower(f) = 'graph theory'" in clause


def test_filter_query_on_fixture(mini_parquet) -> None:
    con = duckdb.connect(database=":memory:")
    rows = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{mini_parquet}')
        WHERE year_clean = 2020
        """
    ).fetchone()[0]
    con.close()

    assert rows == 2
