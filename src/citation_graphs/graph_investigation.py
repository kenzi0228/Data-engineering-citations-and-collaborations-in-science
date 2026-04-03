from __future__ import annotations

from typing import Any

import networkx as nx


def get_component_summary(graph, source_node_id: str, target_node_id: str) -> dict[str, Any]:
    if source_node_id not in graph or target_node_id not in graph:
        raise ValueError("Both source and target nodes must exist in the graph.")

    if graph.is_directed():
        components = list(nx.weakly_connected_components(graph))
        component_type = "weakly_connected_components"
    else:
        components = list(nx.connected_components(graph))
        component_type = "connected_components"

    source_component = None
    target_component = None

    for component in components:
        if source_node_id in component:
            source_component = component
        if target_node_id in component:
            target_component = component

    same_component = source_component == target_component if source_component is not None and target_component is not None else False

    return {
        "component_type": component_type,
        "num_components": len(components),
        "source_component_size": len(source_component) if source_component is not None else None,
        "target_component_size": len(target_component) if target_component is not None else None,
        "same_component": same_component,
    }


def get_neighbors_overlap(graph, source_node_id: str, target_node_id: str) -> dict[str, Any]:
    if source_node_id not in graph or target_node_id not in graph:
        raise ValueError("Both source and target nodes must exist in the graph.")

    source_neighbors = set(graph.neighbors(source_node_id))
    target_neighbors = set(graph.neighbors(target_node_id))

    overlap = sorted(source_neighbors.intersection(target_neighbors))
    source_only = sorted(source_neighbors - target_neighbors)
    target_only = sorted(target_neighbors - source_neighbors)

    return {
        "source_degree": len(source_neighbors),
        "target_degree": len(target_neighbors),
        "shared_neighbor_count": len(overlap),
        "shared_neighbors": overlap,
        "source_only_neighbors": source_only,
        "target_only_neighbors": target_only,
    }


def get_graph_cut_structure(graph) -> dict[str, Any]:
    if graph.is_directed():
        return {
            "supports_articulation_points": False,
            "supports_bridges": False,
            "articulation_points": [],
            "bridges": [],
        }

    articulation_points = sorted(list(nx.articulation_points(graph)))
    bridges = sorted([list(edge) for edge in nx.bridges(graph)])

    return {
        "supports_articulation_points": True,
        "supports_bridges": True,
        "articulation_points": articulation_points,
        "bridges": bridges,
    }


def render_node_labels(graph, node_ids: list[str]) -> list[dict[str, Any]]:
    rendered = []
    for node_id in node_ids:
        attrs = graph.nodes[node_id]
        display_name = (
            attrs.get("display_name")
            or attrs.get("title")
            or attrs.get("name")
            or attrs.get("label")
            or str(node_id)
        )
        rendered.append(
            {
                "node_id": str(node_id),
                "display_name": str(display_name),
                "node_type": attrs.get("node_type"),
            }
        )
    return rendered


def investigate_graph_relationship(graph, source_node_id: str, target_node_id: str) -> dict[str, Any]:
    component_summary = get_component_summary(graph, source_node_id, target_node_id)
    overlap_summary = get_neighbors_overlap(graph, source_node_id, target_node_id)
    cut_summary = get_graph_cut_structure(graph)

    overlap_summary["shared_neighbors_readable"] = render_node_labels(graph, overlap_summary["shared_neighbors"])

    return {
        "component_summary": component_summary,
        "neighbors_overlap": overlap_summary,
        "cut_structure": cut_summary,
    }
