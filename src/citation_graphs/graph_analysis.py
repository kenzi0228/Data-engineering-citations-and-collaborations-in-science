from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import community as community_louvain
import networkx as nx


def load_graph(file_path: str | Path) -> nx.Graph:
    return nx.read_gexf(file_path)


def save_json(data: dict[str, Any], file_path: str | Path) -> None:
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_graph_summary(graph: nx.Graph) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "is_directed": graph.is_directed(),
    }

    if graph.number_of_nodes() == 0:
        summary["clustering_coefficient"] = None
        summary["largest_component_size"] = 0
        summary["diameter"] = None
        return summary

    undirected_graph = graph.to_undirected()
    summary["clustering_coefficient"] = nx.average_clustering(undirected_graph)

    connected_components = list(nx.connected_components(undirected_graph))
    if connected_components:
        largest_component_nodes = max(connected_components, key=len)
        largest_component = undirected_graph.subgraph(largest_component_nodes).copy()
        summary["largest_component_size"] = largest_component.number_of_nodes()
        summary["diameter"] = (
            nx.diameter(largest_component)
            if largest_component.number_of_nodes() > 1
            else 0
        )
    else:
        summary["largest_component_size"] = 0
        summary["diameter"] = None

    return summary


def _sort_top_scores(scores: dict[str, float], top_n: int) -> list[dict[str, Any]]:
    return [
        {"node_id": node_id, "score": score}
        for node_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]
    ]


def get_top_centralities(graph: nx.Graph, top_n: int = 5) -> dict[str, list[dict[str, Any]]]:
    degree_scores = nx.degree_centrality(graph)
    closeness_scores = nx.closeness_centrality(graph)
    betweenness_scores = nx.betweenness_centrality(graph)

    return {
        "degree": _sort_top_scores(degree_scores, top_n),
        "closeness": _sort_top_scores(closeness_scores, top_n),
        "betweenness": _sort_top_scores(betweenness_scores, top_n),
    }


def get_top_pagerank(graph: nx.Graph, top_n: int = 5) -> list[dict[str, Any]]:
    pagerank_scores = nx.pagerank(graph)
    return _sort_top_scores(pagerank_scores, top_n)


def detect_communities(graph: nx.Graph) -> dict[str, Any]:
    if graph.number_of_nodes() == 0:
        return {"num_communities": 0, "sample_partition": []}

    undirected_graph = graph.to_undirected()
    partition = community_louvain.best_partition(undirected_graph)

    return {
        "num_communities": len(set(partition.values())),
        "sample_partition": [
            {"node_id": node_id, "community_id": community_id}
            for node_id, community_id in list(partition.items())[:10]
        ],
    }


def get_node_details(graph: nx.Graph, node_id: str) -> dict[str, Any] | None:
    if node_id not in graph.nodes:
        return None
    return dict(graph.nodes[node_id])


def get_shortest_path(graph: nx.Graph, source: str, target: str) -> list[str] | None:
    try:
        return nx.shortest_path(graph, source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def analyze_graph(graph: nx.Graph, top_n: int = 5) -> dict[str, Any]:
    return {
        "summary": get_graph_summary(graph),
        "centralities": get_top_centralities(graph, top_n=top_n),
        "pagerank": get_top_pagerank(graph, top_n=top_n),
        "communities": detect_communities(graph),
    }