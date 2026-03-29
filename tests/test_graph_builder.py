import networkx as nx

from citation_graphs.graph_builder import (
    append_records_to_graph,
    build_collaboration_graph,
    build_citation_graph,
)


def test_build_citation_graph_adds_nodes_and_edges() -> None:
    records = [
        {
            "_id": "paper_a",
            "title": "Paper A",
            "year": 2020,
            "fos": ["Computer Science"],
            "references": ["paper_b"],
        },
        {
            "_id": "paper_b",
            "title": "Paper B",
            "year": 2019,
            "fos": ["Mathematics"],
            "references": [],
        },
    ]

    graph = build_citation_graph(records)

    assert isinstance(graph, nx.DiGraph)
    assert "paper_a" in graph.nodes
    assert "paper_b" in graph.nodes
    assert graph.has_edge("paper_b", "paper_a")


def test_build_collaboration_graph_creates_weighted_edges() -> None:
    records = [
        {
            "_id": "paper_1",
            "title": "Paper 1",
            "year": 2022,
            "fos": ["AI"],
            "references": [],
            "authors": [
                {"_id": "author_1", "name": "Alice"},
                {"_id": "author_2", "name": "Bob"},
            ],
        },
        {
            "_id": "paper_2",
            "title": "Paper 2",
            "year": 2023,
            "fos": ["AI"],
            "references": [],
            "authors": [
                {"_id": "author_1", "name": "Alice"},
                {"_id": "author_2", "name": "Bob"},
            ],
        },
    ]

    graph = build_collaboration_graph(records)

    assert isinstance(graph, nx.Graph)
    assert graph.has_edge("author_1", "author_2")
    assert graph["author_1"]["author_2"]["weight"] == 2


def test_append_records_to_graph_merges_graphs() -> None:
    initial_graph = nx.DiGraph()
    initial_graph.add_node("paper_x")

    records = [
        {
            "_id": "paper_y",
            "title": "Paper Y",
            "year": 2021,
            "fos": ["Physics"],
            "references": ["paper_x"],
        }
    ]

    merged_graph = append_records_to_graph(initial_graph, records, "citation")

    assert "paper_x" in merged_graph.nodes
    assert "paper_y" in merged_graph.nodes
    assert merged_graph.has_edge("paper_x", "paper_y")