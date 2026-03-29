import networkx as nx

from citation_graphs.graph_analysis import (
    analyze_graph,
    get_graph_summary,
    get_node_details,
    get_shortest_path,
)


def test_get_graph_summary_on_small_graph() -> None:
    graph = nx.DiGraph()
    graph.add_edge("a", "b")
    graph.add_edge("b", "c")

    summary = get_graph_summary(graph)

    assert summary["num_nodes"] == 3
    assert summary["num_edges"] == 2
    assert summary["is_directed"] is True
    assert summary["largest_component_size"] == 3


def test_get_node_details_returns_attributes() -> None:
    graph = nx.Graph()
    graph.add_node("node_1", title="Example", year="2024")

    details = get_node_details(graph, "node_1")

    assert details is not None
    assert details["title"] == "Example"
    assert details["year"] == "2024"


def test_get_shortest_path_returns_valid_path() -> None:
    graph = nx.Graph()
    graph.add_edge("a", "b")
    graph.add_edge("b", "c")

    path = get_shortest_path(graph, "a", "c")

    assert path == ["a", "b", "c"]


def test_analyze_graph_contains_expected_sections() -> None:
    graph = nx.Graph()
    graph.add_edge("a", "b")
    graph.add_edge("b", "c")

    results = analyze_graph(graph, top_n=2)

    assert "summary" in results
    assert "centralities" in results
    assert "pagerank" in results
    assert "communities" in results