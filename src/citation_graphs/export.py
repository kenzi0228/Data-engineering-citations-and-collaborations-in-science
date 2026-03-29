from __future__ import annotations

from typing import Any

import networkx as nx


def extract_top_nodes_from_graph(
    graph: nx.Graph, metric: str = "degree", top_n: int = 100
) -> list[dict[str, Any]]:
    if metric == "degree":
        scores = dict(graph.degree())
    elif metric == "pagerank":
        scores = nx.pagerank(graph)
    elif metric == "betweenness":
        scores = nx.betweenness_centrality(graph)
    else:
        raise ValueError("metric must be one of: degree, pagerank, betweenness")

    top_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]

    results: list[dict[str, Any]] = []
    for node_id, score in top_items:
        node_data = dict(graph.nodes[node_id])
        results.append(
            {
                "node_id": node_id,
                "score": score,
                **node_data,
            }
        )

    return results