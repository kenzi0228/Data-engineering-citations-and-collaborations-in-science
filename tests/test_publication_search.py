from __future__ import annotations

from pathlib import Path

import networkx as nx

from citation_graphs.publication_graphs import (
    build_publication_neighborhood_graph_from_input,
    build_publication_neighborhood_graph_from_rows,
    create_publication_subset_from_input,
    filter_rows_for_publications,
)
from citation_graphs.publication_profile import build_publication_profile
from citation_graphs.publication_search import search_publication_records


def test_search_publication_records_case_insensitive(mini_parquet: Path) -> None:
    rows = search_publication_records(mini_parquet, title_query="graph analytics", limit=50)
    assert len(rows) == 1
    assert rows[0]["title"] == "Graph Analytics for Science"


def test_search_publication_records_partial_match(mini_parquet: Path) -> None:
    rows = search_publication_records(mini_parquet, title_query="collaboration", limit=50)
    assert len(rows) == 1
    assert rows[0]["title"] == "Applied Collaboration Networks"


def test_filter_rows_for_publications(mini_parquet: Path) -> None:
    rows = search_publication_records(mini_parquet, title_query="science", limit=50)
    filtered = filter_rows_for_publications(rows, title_query="science")
    assert len(filtered) == 1


def test_build_publication_profile(mini_parquet: Path) -> None:
    rows = search_publication_records(mini_parquet, title_query="graph", limit=50)
    profile = build_publication_profile(rows, title_query="graph")
    assert profile["publication_count"] == 1
    assert profile["total_citations"] == 12
    assert profile["min_year"] == 2020
    assert profile["max_year"] == 2020


def test_create_publication_subset_from_input(tmp_path: Path, mini_parquet: Path) -> None:
    output_dir = tmp_path / "publication_graph_analytics_for_science"
    result = create_publication_subset_from_input(
        input_path=mini_parquet,
        title_query="Graph Analytics for Science",
        output_dir=output_dir,
    )
    assert result["row_count"] == 1
    assert (output_dir / "data.parquet").exists()
    assert (output_dir / "_subset_summary.json").exists()


def test_build_publication_neighborhood_graph_from_rows(mini_parquet: Path) -> None:
    rows = search_publication_records(mini_parquet, title_query="graph", limit=50)
    graph = build_publication_neighborhood_graph_from_rows(rows)
    assert isinstance(graph, nx.DiGraph)
    assert graph.number_of_nodes() >= 1


def test_build_publication_neighborhood_graph_from_input(tmp_path: Path, mini_parquet: Path) -> None:
    result = build_publication_neighborhood_graph_from_input(
        input_path=mini_parquet,
        title_query="Graph Analytics for Science",
        output_dir=tmp_path,
        graph_name="publication_graph_analytics_for_science_citation",
    )
    assert result["num_nodes"] >= 1
    assert (tmp_path / "publication_graph_analytics_for_science_citation.gexf").exists()
    assert (tmp_path / "publication_graph_analytics_for_science_citation_summary.json").exists()
