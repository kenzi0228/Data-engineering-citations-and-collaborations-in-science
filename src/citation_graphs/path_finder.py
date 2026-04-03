from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx


class PathFinderError(Exception):
    pass


class NodeNotFoundError(PathFinderError):
    pass


def load_graph(file_path: str | Path):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Graph file not found: {file_path}")
    return nx.read_gexf(file_path)


def get_node_display_name(graph, node_id: str) -> str:
    if node_id not in graph:
        raise NodeNotFoundError(f"Node not found: {node_id}")

    attrs = graph.nodes[node_id]
    display_name = (
        attrs.get("display_name")
        or attrs.get("title")
        or attrs.get("name")
        or attrs.get("label")
        or node_id
    )
    return str(display_name)


def validate_nodes_exist(graph, source_node_id: str, target_node_id: str) -> None:
    missing = []
    if source_node_id not in graph:
        missing.append(source_node_id)
    if target_node_id not in graph:
        missing.append(target_node_id)
    if missing:
        raise NodeNotFoundError(f"Missing node(s): {', '.join(missing)}")


def nodes_are_connected(graph, source_node_id: str, target_node_id: str) -> bool:
    validate_nodes_exist(graph, source_node_id, target_node_id)

    if source_node_id == target_node_id:
        return True

    try:
        return nx.has_path(graph, source_node_id, target_node_id)
    except Exception:
        return False


def shortest_path_length_between(graph, source_node_id: str, target_node_id: str) -> int | None:
    validate_nodes_exist(graph, source_node_id, target_node_id)

    if source_node_id == target_node_id:
        return 0

    try:
        return int(nx.shortest_path_length(graph, source_node_id, target_node_id))
    except nx.NetworkXNoPath:
        return None


def shortest_path_between(graph, source_node_id: str, target_node_id: str) -> list[str] | None:
    validate_nodes_exist(graph, source_node_id, target_node_id)

    if source_node_id == target_node_id:
        return [source_node_id]

    try:
        return list(nx.shortest_path(graph, source_node_id, target_node_id))
    except nx.NetworkXNoPath:
        return None


def all_shortest_paths_between(
    graph,
    source_node_id: str,
    target_node_id: str,
    max_paths: int = 10,
) -> list[list[str]]:
    validate_nodes_exist(graph, source_node_id, target_node_id)

    if source_node_id == target_node_id:
        return [[source_node_id]]

    try:
        paths_iter = nx.all_shortest_paths(graph, source_node_id, target_node_id)
        paths: list[list[str]] = []
        for idx, path in enumerate(paths_iter):
            if idx >= max_paths:
                break
            paths.append(list(path))
        return paths
    except nx.NetworkXNoPath:
        return []


def render_readable_path(graph, path: list[str]) -> list[dict[str, Any]]:
    rendered = []
    for node_id in path:
        if node_id not in graph:
            rendered.append(
                {
                    "node_id": node_id,
                    "display_name": node_id,
                    "node_type": None,
                }
            )
            continue

        attrs = graph.nodes[node_id]
        rendered.append(
            {
                "node_id": node_id,
                "display_name": get_node_display_name(graph, node_id),
                "node_type": attrs.get("node_type"),
            }
        )
    return rendered


def investigate_path_between_nodes(
    graph,
    source_node_id: str,
    target_node_id: str,
    max_paths: int = 5,
) -> dict[str, Any]:
    validate_nodes_exist(graph, source_node_id, target_node_id)

    source_display_name = get_node_display_name(graph, source_node_id)
    target_display_name = get_node_display_name(graph, target_node_id)

    connected = nodes_are_connected(graph, source_node_id, target_node_id)
    shortest_length = shortest_path_length_between(graph, source_node_id, target_node_id)
    shortest_path = shortest_path_between(graph, source_node_id, target_node_id)
    all_paths = all_shortest_paths_between(graph, source_node_id, target_node_id, max_paths=max_paths)

    return {
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "source_display_name": source_display_name,
        "target_display_name": target_display_name,
        "connected": connected,
        "shortest_path_length": shortest_length,
        "shortest_path_node_ids": shortest_path,
        "shortest_path_readable": render_readable_path(graph, shortest_path) if shortest_path else [],
        "all_shortest_paths_readable": [render_readable_path(graph, path) for path in all_paths],
        "graph_is_directed": bool(graph.is_directed()),
        "max_paths_requested": max_paths,
    }


def save_path_investigation(result: dict[str, Any], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=4, ensure_ascii=False), encoding="utf-8")
    return output_path
