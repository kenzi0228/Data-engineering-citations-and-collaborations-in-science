from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def _format_metric(label: str, value: Any) -> str:
    return f"- **{label}**: {value}"


def _table_from_rows(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No data available._"

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body_lines = []

    for row in rows:
        values = []
        for col in columns:
            value = row.get(col, "")
            values.append(str(value).replace("\n", " ").strip())
        body_lines.append("| " + " | ".join(values) + " |")

    return "\n".join([header, separator, *body_lines])


def build_analysis_markdown_report(
    analysis_name: str,
    analysis: dict[str, Any],
) -> str:
    summary = analysis.get("summary", {})
    centralities = analysis.get("centralities", {})
    pagerank = analysis.get("pagerank", [])
    communities = analysis.get("communities", {})

    lines: list[str] = []
    lines.append(f"# Graph Analysis Report â€” {analysis_name}")
    lines.append("")
    lines.append(f"_Generated on {datetime.utcnow().isoformat()} UTC_")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(_format_metric("Directed", summary.get("is_directed", "")))
    lines.append(_format_metric("Nodes", summary.get("num_nodes", "")))
    lines.append(_format_metric("Edges", summary.get("num_edges", "")))
    lines.append(_format_metric("Density", summary.get("density", "")))
    lines.append(_format_metric("Largest component nodes", summary.get("largest_component_nodes", "")))
    lines.append(_format_metric("Largest component edges", summary.get("largest_component_edges", "")))
    lines.append(_format_metric("Largest component diameter", summary.get("largest_component_diameter", "")))
    lines.append(_format_metric("Diameter mode", summary.get("largest_component_diameter_mode", "")))
    lines.append(_format_metric("Largest component average clustering", summary.get("largest_component_average_clustering", "")))
    lines.append(_format_metric("Communities detected", communities.get("num_communities", "")))
    lines.append("")

    lines.append("## Top PageRank")
    lines.append("")
    lines.append(_table_from_rows(pagerank[:10], ["node_id", "display_name", "score"]))
    lines.append("")

    lines.append("## Top Degree Centrality")
    lines.append("")
    lines.append(_table_from_rows(centralities.get("degree", [])[:10], ["node_id", "display_name", "score"]))
    lines.append("")

    lines.append("## Top Closeness Centrality")
    lines.append("")
    lines.append(_table_from_rows(centralities.get("closeness", [])[:10], ["node_id", "display_name", "score"]))
    lines.append("")

    lines.append("## Top Betweenness Centrality")
    lines.append("")
    lines.append(_table_from_rows(centralities.get("betweenness", [])[:10], ["node_id", "display_name", "score"]))
    lines.append("")

    lines.append("## Largest Communities")
    lines.append("")
    lines.append(_table_from_rows(communities.get("largest_communities", [])[:10], ["community_id", "size"]))
    lines.append("")

    return "\n".join(lines)


def export_analysis_markdown_report(
    analysis_path: str | Path,
    output_path: str | Path,
    analysis_name: str | None = None,
) -> dict[str, str]:
    analysis_path = Path(analysis_path)
    output_path = Path(output_path)

    analysis = __import__("json").loads(analysis_path.read_text(encoding="utf-8"))
    resolved_name = analysis_name or analysis_path.stem.replace("_analysis", "")
    markdown = build_analysis_markdown_report(resolved_name, analysis)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    return {
        "analysis_path": str(analysis_path.resolve()),
        "report_path": str(output_path.resolve()),
        "analysis_name": resolved_name,
    }
