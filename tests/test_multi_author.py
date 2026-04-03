from __future__ import annotations

from pathlib import Path

import networkx as nx

from citation_graphs.multi_author import (
    build_multi_author_collaboration_graph,
    build_multi_author_graph_from_input,
    build_multi_author_slug,
    create_multi_author_subset_from_input,
    filter_rows_for_authors,
)
from citation_graphs.search import search_author_records_multi


def test_build_multi_author_slug() -> None:
    slug = build_multi_author_slug(["Alice Doe", "Bob Ray"], "and")
    assert slug == "authors_alice_doe_bob_ray_and"


def test_filter_rows_for_authors_or(mini_parquet: Path) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice", "bob"],
        limit=50,
        match_mode="or",
    )
    filtered = filter_rows_for_authors(rows, author_queries=["alice", "bob"], match_mode="or")
    assert len(filtered) == 3


def test_filter_rows_for_authors_and(mini_parquet: Path) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice", "bob"],
        limit=50,
        match_mode="and",
    )
    filtered = filter_rows_for_authors(rows, author_queries=["alice", "bob"], match_mode="and")
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Graph Analytics for Science"


def test_build_multi_author_collaboration_graph_or(mini_parquet: Path) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice", "bob"],
        limit=50,
        match_mode="or",
    )
    graph = build_multi_author_collaboration_graph(rows)

    assert isinstance(graph, nx.Graph)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 2


def test_build_multi_author_collaboration_graph_and(mini_parquet: Path) -> None:
    rows = search_author_records_multi(
        mini_parquet,
        author_queries=["alice", "bob"],
        limit=50,
        match_mode="and",
    )
    graph = build_multi_author_collaboration_graph(rows)

    assert isinstance(graph, nx.Graph)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1


def test_create_multi_author_subset_from_input(tmp_path: Path, mini_parquet: Path) -> None:
    output_dir = tmp_path / "authors_alice_doe_bob_ray_and"
    result = create_multi_author_subset_from_input(
        input_path=mini_parquet,
        author_queries=["alice", "bob"],
        match_mode="and",
        output_dir=output_dir,
    )

    assert result["row_count"] == 1
    assert (output_dir / "data.parquet").exists()
    assert (output_dir / "_subset_summary.json").exists()


def test_build_multi_author_graph_from_input(tmp_path: Path, mini_parquet: Path) -> None:
    result = build_multi_author_graph_from_input(
        input_path=mini_parquet,
        author_queries=["alice", "bob"],
        match_mode="or",
        output_dir=tmp_path,
        graph_name="authors_alice_doe_bob_ray_or_collaboration",
    )

    assert result["num_nodes"] == 3
    assert result["num_edges"] == 2
    assert (tmp_path / "authors_alice_doe_bob_ray_or_collaboration.gexf").exists()
    assert (tmp_path / "authors_alice_doe_bob_ray_or_collaboration_summary.json").exists()
