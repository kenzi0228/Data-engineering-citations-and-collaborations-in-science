$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "src\citation_graphs" | Out-Null

@'
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import community as community_louvain
import networkx as nx

from citation_graphs.exceptions import MissingInputError


def load_graph(file_path: str | Path) -> nx.Graph:
    file_path = Path(file_path)
    if not file_path.exists():
        raise MissingInputError(f"Graph file not found: {file_path}")
    return nx.read_gexf(file_path)


def get_largest_component(graph: nx.Graph) -> nx.Graph:
    undirected = graph.to_undirected()

    if undirected.number_of_nodes() == 0:
        return undirected.copy()

    components = list(nx.connected_components(undirected))
    if not components:
        return undirected.copy()

    largest_nodes = max(components, key=len)
    return undirected.subgraph(largest_nodes).copy()


def approximate_diameter(graph: nx.Graph, sample_size: int = 25, seed: int = 42) -> int | None:
    if graph.number_of_nodes() == 0:
        return None
    if graph.number_of_nodes() == 1:
        return 0

    rng = random.Random(seed)
    nodes = list(graph.nodes())
    sampled_nodes = nodes if len(nodes) <= sample_size else rng.sample(nodes, sample_size)

    max_distance = 0
    for node in sampled_nodes:
        lengths = nx.single_source_shortest_path_length(graph, node)
        if lengths:
            local_max = max(lengths.values())
            if local_max > max_distance:
                max_distance = local_max

    return max_distance


def get_graph_summary(
    graph: nx.Graph,
    exact_diameter_max_nodes: int = 5000,
    approximate_diameter_sample_size: int = 25,
) -> dict[str, Any]:
    largest_component = get_largest_component(graph)

    summary = {
        "is_directed": graph.is_directed(),
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "largest_component_nodes": largest_component.number_of_nodes(),
        "largest_component_edges": largest_component.number_of_edges(),
    }

    if largest_component.number_of_nodes() > 1:
        summary["largest_component_average_clustering"] = nx.average_clustering(largest_component)

        if largest_component.number_of_nodes() <= exact_diameter_max_nodes:
            summary["largest_component_diameter"] = nx.diameter(largest_component)
            summary["largest_component_diameter_mode"] = "exact"
        else:
            summary["largest_component_diameter"] = approximate_diameter(
                largest_component,
                sample_size=approximate_diameter_sample_size,
            )
            summary["largest_component_diameter_mode"] = "approximate"
    else:
        summary["largest_component_diameter"] = 0
        summary["largest_component_diameter_mode"] = "exact"
        summary["largest_component_average_clustering"] = 0.0

    return summary


def _clean_candidate(value: Any) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    if not value:
        return ""
    if value.lower() in {"none", "nan", "null"}:
        return ""
    return value


def _looks_like_placeholder(value: str, node_id: str) -> bool:
    value_lower = value.lower().strip()
    node_id = str(node_id).strip()

    if value == node_id:
        return True

    placeholder_prefixes = (
        "paper ",
        "author ",
        "reference ",
    )

    if value_lower.startswith(placeholder_prefixes):
        return True

    return False


def _resolve_display_name(node_id: Any, attrs: dict[str, Any]) -> str:
    node_id_str = str(node_id).strip()

    title = _clean_candidate(attrs.get("title"))
    name = _clean_candidate(attrs.get("name"))
    display_name = _clean_candidate(attrs.get("display_name"))

    # Priorité métier absolue
    if title and not _looks_like_placeholder(title, node_id_str):
        return title

    if name and not _looks_like_placeholder(name, node_id_str):
        return name

    if display_name and not _looks_like_placeholder(display_name, node_id_str):
        return display_name

    return node_id_str


def _node_context(graph: nx.Graph, node_id: Any) -> dict[str, Any]:
    attrs = dict(graph.nodes[node_id])
    return {
        "node_id": str(node_id),
        "display_name": _resolve_display_name(node_id, attrs),
        "details": attrs,
    }


def _top_scores(scores: dict[Any, float], graph: nx.Graph, top_n: int) -> list[dict[str, Any]]:
    rows = []
    for node_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]:
        node_info = _node_context(graph, node_id)
        rows.append(
            {
                "node_id": str(node_id),
                "display_name": node_info["display_name"],
                "score": float(score),
                "details": node_info["details"],
            }
        )
    return rows


def get_top_degree_centrality(graph: nx.Graph, top_n: int = 10) -> list[dict[str, Any]]:
    scores = nx.degree_centrality(graph)
    return _top_scores(scores, graph, top_n)


def get_top_closeness_centrality(graph: nx.Graph, top_n: int = 10) -> list[dict[str, Any]]:
    scores = nx.closeness_centrality(graph)
    return _top_scores(scores, graph, top_n)


def get_top_betweenness_centrality(
    graph: nx.Graph,
    top_n: int = 10,
    approximate: bool = True,
    sample_k: int = 200,
) -> list[dict[str, Any]]:
    if graph.number_of_nodes() == 0:
        return []

    if approximate and graph.number_of_nodes() > sample_k:
        scores = nx.betweenness_centrality(graph, k=sample_k, seed=42)
    else:
        scores = nx.betweenness_centrality(graph)

    return _top_scores(scores, graph, top_n)


def pagerank_power_iteration(
    graph: nx.Graph,
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1.0e-6,
) -> dict[Any, float]:
    if graph.number_of_nodes() == 0:
        return {}

    directed = graph if graph.is_directed() else graph.to_directed()
    nodes = list(directed.nodes())
    n = len(nodes)

    ranks = {node: 1.0 / n for node in nodes}
    out_degree = {node: directed.out_degree(node) for node in nodes}

    for _ in range(max_iter):
        new_ranks = {node: (1.0 - alpha) / n for node in nodes}
        dangling_sum = alpha * sum(ranks[node] for node in nodes if out_degree[node] == 0) / n

        for node in nodes:
            new_ranks[node] += dangling_sum

        for node in nodes:
            if out_degree[node] == 0:
                continue

            contribution = alpha * ranks[node] / out_degree[node]
            for neighbor in directed.successors(node):
                new_ranks[neighbor] += contribution

        error = sum(abs(new_ranks[node] - ranks[node]) for node in nodes)
        ranks = new_ranks

        if error < n * tol:
            break

    return ranks


def get_top_pagerank(graph: nx.Graph, top_n: int = 10) -> list[dict[str, Any]]:
    if graph.number_of_nodes() == 0:
        return []

    scores = pagerank_power_iteration(graph)
    return _top_scores(scores, graph, top_n)


def detect_communities(graph: nx.Graph, top_n: int = 10) -> dict[str, Any]:
    undirected = graph.to_undirected()

    if undirected.number_of_nodes() == 0:
        return {
            "num_communities": 0,
            "largest_communities": [],
            "sample_partition": [],
        }

    partition = community_louvain.best_partition(undirected)

    community_sizes: dict[int, int] = {}
    for _, community_id in partition.items():
        community_sizes[community_id] = community_sizes.get(community_id, 0) + 1

    largest_communities = sorted(community_sizes.items(), key=lambda item: item[1], reverse=True)[:top_n]

    return {
        "num_communities": len(community_sizes),
        "largest_communities": [
            {"community_id": int(community_id), "size": int(size)}
            for community_id, size in largest_communities
        ],
        "sample_partition": [
            {"node_id": str(node_id), "community_id": int(community_id)}
            for node_id, community_id in list(partition.items())[:20]
        ],
    }


def analyze_graph(
    graph: nx.Graph,
    top_n: int = 10,
    approximate_betweenness: bool = True,
    betweenness_sample_k: int = 200,
    exact_diameter_max_nodes: int = 5000,
    approximate_diameter_sample_size: int = 25,
) -> dict[str, Any]:
    return {
        "summary": get_graph_summary(
            graph,
            exact_diameter_max_nodes=exact_diameter_max_nodes,
            approximate_diameter_sample_size=approximate_diameter_sample_size,
        ),
        "centralities": {
            "degree": get_top_degree_centrality(graph, top_n=top_n),
            "closeness": get_top_closeness_centrality(graph, top_n=top_n),
            "betweenness": get_top_betweenness_centrality(
                graph,
                top_n=top_n,
                approximate=approximate_betweenness,
                sample_k=betweenness_sample_k,
            ),
        },
        "pagerank": get_top_pagerank(graph, top_n=top_n),
        "communities": detect_communities(graph, top_n=top_n),
        "node_details_index": {
            str(node_id): {
                "display_name": _resolve_display_name(node_id, dict(attrs)),
                "details": dict(attrs),
            }
            for node_id, attrs in graph.nodes(data=True)
        },
    }


def save_analysis_results(results: dict[str, Any], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)
'@ | Set-Content "src\citation_graphs\graph_analysis.py" -Encoding UTF8

Write-Host "V8.2 label repair patch applied."
Write-Host "Updated: src\citation_graphs\graph_analysis.py"