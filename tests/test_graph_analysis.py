from __future__ import annotations

from citation_graphs.graph_analysis import analyze_graph
from citation_graphs.graph_builder import build_citation_graph, build_collaboration_graph


def test_analyze_citation_graph_structure(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)

    assert "summary" in result
    assert "centralities" in result
    assert "pagerank" in result
    assert "communities" in result
    assert "node_details_index" in result


def test_analyze_collaboration_graph_structure(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)

    assert isinstance(result["pagerank"], list)
    assert isinstance(result["centralities"]["degree"], list)
    assert isinstance(result["communities"]["largest_communities"], list)


def test_display_name_priority_for_citation(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)
    details = result["node_details_index"]["paper_1"]
    assert details["display_name"] == "Graph Analytics for Science"


def test_display_name_priority_for_collaboration(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)
    details = result["node_details_index"]["author_1"]
    assert details["display_name"] == "Alice Doe"
