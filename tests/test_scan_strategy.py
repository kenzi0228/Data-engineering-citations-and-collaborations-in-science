from __future__ import annotations

from pathlib import Path

from citation_graphs.scan_strategy import build_duckdb_read_expression, resolve_partition_sources


def test_resolve_partition_sources_file(mini_parquet: Path) -> None:
    result = resolve_partition_sources(mini_parquet)
    assert result["mode"] == "file"
    assert result["files_scanned"] == 1
    assert len(result["sources"]) == 1


def test_build_duckdb_read_expression_file(mini_parquet: Path) -> None:
    result = resolve_partition_sources(mini_parquet)
    expr = build_duckdb_read_expression(result)
    assert "read_parquet" in expr
    assert str(mini_parquet) in expr
