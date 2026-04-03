from __future__ import annotations

import networkx as nx

from citation_graphs.graph_investigation import (
    get_component_summary,
    get_graph_cut_structure,
    get_neighbors_overlap,
    investigate_graph_relationship,
)


def build_undirected_fixture() -> nx.Graph:
    graph = nx.Graph()
    graph.add_node("a", display_name="Alice", node_type="author")
    graph.add_node("b", display_name="Bob", node_type="author")
    graph.add_node("c", display_name="Charlie", node_type="author")
    graph.add_node("d", display_name="Diane", node_type="author")
    graph.add_node("e", display_name="Eve", node_type="author")
    graph.add_edges_from([("a", "b"), ("b", "c"), ("c", "d"), ("b", "d")])
    return graph


def build_directed_fixture() -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_node("p1", display_name="Paper 1", node_type="publication")
    graph.add_node("p2", display_name="Paper 2", node_type="publication")
    graph.add_node("p3", display_name="Paper 3", node_type="publication")
    graph.add_edges_from([("p1", "p2"), ("p2", "p3")])
    return graph


def test_component_summary_undirected() -> None:
    graph = build_undirected_fixture()
    result = get_component_summary(graph, "a", "d")
    assert result["component_type"] == "connected_components"
    assert result["same_component"] is True


def test_component_summary_directed() -> None:
    graph = build_directed_fixture()
    result = get_component_summary(graph, "p1", "p3")
    assert result["component_type"] == "weakly_connected_components"
    assert result["same_component"] is True


def test_neighbors_overlap() -> None:
    graph = build_undirected_fixture()
    result = get_neighbors_overlap(graph, "c", "d")
    assert result["shared_neighbor_count"] >= 1


def test_cut_structure_undirected() -> None:
    graph = build_undirected_fixture()
    result = get_graph_cut_structure(graph)
    assert result["supports_articulation_points"] is True
    assert isinstance(result["articulation_points"], list)


def test_cut_structure_directed() -> None:
    graph = build_directed_fixture()
    result = get_graph_cut_structure(graph)
    assert result["supports_articulation_points"] is False
    assert result["articulation_points"] == []


def test_investigate_graph_relationship() -> None:
    graph = build_undirected_fixture()
    result = investigate_graph_relationship(graph, "c", "d")
    assert "component_summary" in result
    assert "neighbors_overlap" in result
    assert "cut_structure" in result
