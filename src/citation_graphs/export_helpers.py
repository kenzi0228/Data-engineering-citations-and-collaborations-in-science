from __future__ import annotations

from typing import Any


def _line(label: str, value: Any) -> str:
    return f"- **{label}**: {value}"


def build_compare_markdown_summary(result: dict[str, Any]) -> str:
    lines = [
        "# Comparison Summary",
        "",
        _line("Mode", result.get("comparison_mode")),
        _line("Source", result.get("source_display_name")),
        _line("Target", result.get("target_display_name")),
        _line("Connected", result.get("connected")),
        _line("Shortest path length", result.get("shortest_path_length")),
        _line("Graph base", result.get("graph_base_name")),
        _line("Graph path", result.get("graph_path")),
        "",
    ]

    shortest_path = result.get("shortest_path_readable", []) or []
    if shortest_path:
        lines.append("## Main Path")
        lines.append("")
        labels = [step.get("display_name") or step.get("node_id") for step in shortest_path]
        lines.append(" -> ".join(str(x) for x in labels))
        lines.append("")

    return "\n".join(lines)


def build_pathfinder_markdown_summary(result: dict[str, Any], graph_investigation: dict[str, Any] | None = None) -> str:
    lines = [
        "# Path Finder Summary",
        "",
        _line("Source", result.get("source_display_name")),
        _line("Target", result.get("target_display_name")),
        _line("Connected", result.get("connected")),
        _line("Shortest path length", result.get("shortest_path_length")),
        _line("Directed graph", result.get("graph_is_directed")),
        _line("Graph path", result.get("graph_path")),
        "",
    ]

    shortest_path = result.get("shortest_path_readable", []) or []
    if shortest_path:
        lines.append("## Main Path")
        lines.append("")
        labels = [step.get("display_name") or step.get("node_id") for step in shortest_path]
        lines.append(" -> ".join(str(x) for x in labels))
        lines.append("")

    if isinstance(graph_investigation, dict):
        component_summary = graph_investigation.get("component_summary", {}) or {}
        overlap = graph_investigation.get("neighbors_overlap", {}) or {}

        lines.append("## Graph Investigation")
        lines.append("")
        lines.append(_line("Component type", component_summary.get("component_type")))
        lines.append(_line("Number of components", component_summary.get("num_components")))
        lines.append(_line("Same component", component_summary.get("same_component")))
        lines.append(_line("Shared neighbor count", overlap.get("shared_neighbor_count")))
        lines.append("")

    return "\n".join(lines)


def build_insights_markdown_summary(selected_base: str, graph_type: str, health: dict[str, Any], narrative: list[str]) -> str:
    lines = [
        "# Graph Insights Summary",
        "",
        _line("Analysis base", selected_base),
        _line("Graph type", graph_type),
        _line("Directed", health.get("directed")),
        _line("Nodes", health.get("num_nodes")),
        _line("Edges", health.get("num_edges")),
        _line("Density", health.get("density")),
        _line("Largest component nodes", health.get("largest_component_nodes")),
        _line("Largest component edges", health.get("largest_component_edges")),
        _line("Diameter", health.get("largest_component_diameter")),
        _line("Communities", health.get("num_communities")),
        _line("Build total seconds", health.get("build_total_seconds")),
        "",
    ]

    if narrative:
        lines.append("## Narrative Insights")
        lines.append("")
        for item in narrative:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)
