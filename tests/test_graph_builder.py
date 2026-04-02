from __future__ import annotations

from citation_graphs.graph_builder import build_citation_graph, build_collaboration_graph


def test_build_citation_graph(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    assert graph.number_of_nodes() >= 3
    assert graph.number_of_edges() >= 2


def test_build_collaboration_graph(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() >= 2


def test_citation_graph_has_title_label(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    assert graph.nodes["paper_1"]["title"] == "Graph Analytics for Science"
    assert graph.nodes["paper_1"]["display_name"] == "Graph Analytics for Science"


def test_collaboration_graph_has_name_label(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    assert graph.nodes["author_1"]["name"] == "Alice Doe"
    assert graph.nodes["author_1"]["display_name"] == "Alice Doe"
