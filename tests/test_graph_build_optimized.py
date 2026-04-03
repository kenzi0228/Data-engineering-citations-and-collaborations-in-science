from __future__ import annotations

from pathlib import Path

import networkx as nx

from citation_graphs.graph_build_optimized import (
    build_citation_graph,
    build_collaboration_graph,
    load_graph_build_rows,
    save_graph_and_summary,
)


def test_load_graph_build_rows(mini_parquet: Path) -> None:
    rows, meta = load_graph_build_rows(mini_parquet)
    assert len(rows) >= 1
    assert "load_seconds" in meta
    assert meta["row_count"] >= 1


def test_build_citation_graph_optimized(mini_parquet: Path) -> None:
    rows, load_meta = load_graph_build_rows(mini_parquet)
    graph, build_meta = build_citation_graph(rows)
    assert isinstance(graph, nx.DiGraph)
    assert "build_seconds" in build_meta
    assert graph.number_of_nodes() >= 1


def test_build_collaboration_graph_optimized(mini_parquet: Path) -> None:
    rows, load_meta = load_graph_build_rows(mini_parquet)
    graph, build_meta = build_collaboration_graph(rows)
    assert isinstance(graph, nx.Graph)
    assert "build_seconds" in build_meta
    assert graph.number_of_nodes() >= 1


def test_save_graph_and_summary(tmp_path: Path, mini_parquet: Path) -> None:
    rows, load_meta = load_graph_build_rows(mini_parquet)
    graph, build_meta = build_citation_graph(rows)
    summary = save_graph_and_summary(
        graph,
        output_dir=tmp_path,
        graph_name="optimized_test_graph",
        graph_type="optimized_citation",
        source_parquet=mini_parquet,
        load_meta=load_meta,
        build_meta=build_meta,
    )
    assert (tmp_path / "optimized_test_graph.gexf").exists()
    assert (tmp_path / "optimized_test_graph_summary.json").exists()
    assert "total_seconds" in summary
