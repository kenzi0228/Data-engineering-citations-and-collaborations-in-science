from __future__ import annotations

from pathlib import Path

import networkx as nx

from citation_graphs.ego_graphs import (
    build_author_ego_collaboration_graph,
    build_author_ego_graph_from_input,
    create_author_subset_from_input,
    filter_rows_for_author,
)
from citation_graphs.search import search_author_records


def test_filter_rows_for_author(mini_parquet: Path) -> None:
    rows = search_author_records(mini_parquet, author_query="alice", limit=50)
    filtered = filter_rows_for_author(rows, author_query="alice")
    assert len(filtered) == 2


def test_build_author_ego_collaboration_graph(mini_parquet: Path) -> None:
    rows = search_author_records(mini_parquet, author_query="alice", limit=50)
    graph = build_author_ego_collaboration_graph(rows, author_query="alice")

    assert isinstance(graph, nx.Graph)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 2

    names = [attrs.get("display_name") for _, attrs in graph.nodes(data=True)]
    assert "Alice Doe" in names
    assert "Bob Ray" in names
    assert "Charlie Lin" in names


def test_create_author_subset_from_input(tmp_path: Path, mini_parquet: Path) -> None:
    output_dir = tmp_path / "author_alice_doe"
    result = create_author_subset_from_input(
        input_path=mini_parquet,
        author_query="alice",
        output_dir=output_dir,
    )

    assert result["row_count"] == 2
    assert (output_dir / "data.parquet").exists()
    assert (output_dir / "_subset_summary.json").exists()


def test_build_author_ego_graph_from_input(tmp_path: Path, mini_parquet: Path) -> None:
    result = build_author_ego_graph_from_input(
        input_path=mini_parquet,
        author_query="alice",
        output_dir=tmp_path,
        graph_name="author_alice_doe_ego_collaboration",
    )

    assert result["num_nodes"] == 3
    assert result["num_edges"] == 2
    assert (tmp_path / "author_alice_doe_ego_collaboration.gexf").exists()
    assert (tmp_path / "author_alice_doe_ego_collaboration_summary.json").exists()
