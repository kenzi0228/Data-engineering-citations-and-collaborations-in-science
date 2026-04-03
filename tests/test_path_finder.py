from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from citation_graphs.path_finder import (
    NodeNotFoundError,
    all_shortest_paths_between,
    get_node_display_name,
    investigate_path_between_nodes,
    nodes_are_connected,
    render_readable_path,
    shortest_path_between,
    shortest_path_length_between,
)


def build_collaboration_fixture() -> nx.Graph:
    graph = nx.Graph()
    graph.add_node("a", display_name="Alice Doe", name="Alice Doe", node_type="author")
    graph.add_node("b", display_name="Bob Ray", name="Bob Ray", node_type="author")
    graph.add_node("c", display_name="Charlie Lin", name="Charlie Lin", node_type="author")
    graph.add_node("d", display_name="Diane Fox", name="Diane Fox", node_type="author")
    graph.add_edge("a", "b")
    graph.add_edge("b", "c")
    return graph


def build_citation_fixture() -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_node("p1", display_name="Paper A", title="Paper A", node_type="publication")
    graph.add_node("p2", display_name="Paper B", title="Paper B", node_type="publication")
    graph.add_node("p3", display_name="Paper C", title="Paper C", node_type="publication")
    graph.add_edge("p1", "p2")
    graph.add_edge("p2", "p3")
    return graph


def test_get_node_display_name() -> None:
    graph = build_collaboration_fixture()
    assert get_node_display_name(graph, "a") == "Alice Doe"


def test_nodes_are_connected_undirected_true() -> None:
    graph = build_collaboration_fixture()
    assert nodes_are_connected(graph, "a", "c") is True


def test_nodes_are_connected_undirected_false() -> None:
    graph = build_collaboration_fixture()
    assert nodes_are_connected(graph, "a", "d") is False


def test_shortest_path_length_between_undirected() -> None:
    graph = build_collaboration_fixture()
    assert shortest_path_length_between(graph, "a", "c") == 2


def test_shortest_path_between_undirected() -> None:
    graph = build_collaboration_fixture()
    assert shortest_path_between(graph, "a", "c") == ["a", "b", "c"]


def test_all_shortest_paths_between_single() -> None:
    graph = build_collaboration_fixture()
    assert all_shortest_paths_between(graph, "a", "c", max_paths=5) == [["a", "b", "c"]]


def test_render_readable_path() -> None:
    graph = build_collaboration_fixture()
    rendered = render_readable_path(graph, ["a", "b", "c"])
    assert rendered[0]["display_name"] == "Alice Doe"
    assert rendered[1]["display_name"] == "Bob Ray"
    assert rendered[2]["display_name"] == "Charlie Lin"


def test_investigate_path_between_nodes_connected() -> None:
    graph = build_collaboration_fixture()
    result = investigate_path_between_nodes(graph, "a", "c", max_paths=5)

    assert result["connected"] is True
    assert result["shortest_path_length"] == 2
    assert result["shortest_path_node_ids"] == ["a", "b", "c"]
    assert result["shortest_path_readable"][0]["display_name"] == "Alice Doe"
    assert result["shortest_path_readable"][-1]["display_name"] == "Charlie Lin"


def test_investigate_path_between_nodes_disconnected() -> None:
    graph = build_collaboration_fixture()
    result = investigate_path_between_nodes(graph, "a", "d", max_paths=5)

    assert result["connected"] is False
    assert result["shortest_path_length"] is None
    assert result["shortest_path_node_ids"] is None
    assert result["shortest_path_readable"] == []
    assert result["all_shortest_paths_readable"] == []


def test_same_node_path() -> None:
    graph = build_collaboration_fixture()
    result = investigate_path_between_nodes(graph, "a", "a", max_paths=5)

    assert result["connected"] is True
    assert result["shortest_path_length"] == 0
    assert result["shortest_path_node_ids"] == ["a"]


def test_directed_path_forward() -> None:
    graph = build_citation_fixture()
    result = investigate_path_between_nodes(graph, "p1", "p3", max_paths=5)

    assert result["connected"] is True
    assert result["shortest_path_length"] == 2
    assert result["shortest_path_node_ids"] == ["p1", "p2", "p3"]


def test_directed_path_backward_not_connected() -> None:
    graph = build_citation_fixture()
    result = investigate_path_between_nodes(graph, "p3", "p1", max_paths=5)

    assert result["connected"] is False
    assert result["shortest_path_length"] is None
    assert result["shortest_path_node_ids"] is None


def test_missing_node_raises() -> None:
    graph = build_collaboration_fixture()
    with pytest.raises(NodeNotFoundError):
        investigate_path_between_nodes(graph, "a", "z", max_paths=5)
