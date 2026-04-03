$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "src\citation_graphs" | Out-Null

@'
from __future__ import annotations

from pathlib import Path


path = Path(r"src/citation_graphs/export_helpers.py")
path.write_text(
'''from __future__ import annotations

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

    return "\\n".join(lines)


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

    return "\\n".join(lines)


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

    return "\\n".join(lines)
''',
    encoding="utf-8",
)
print("Created src/citation_graphs/export_helpers.py")
'@ | Set-Content "._create_v0141_export_helpers.py" -Encoding UTF8

python .\._create_v0141_export_helpers.py
Remove-Item .\._create_v0141_export_helpers.py -Force

@'
from __future__ import annotations

from pathlib import Path


path = Path(r"app/streamlit_app.py")
content = path.read_text(encoding="utf-8")

old_import = """from citation_graphs.graph_investigation import investigate_graph_relationship
from citation_graphs.path_finder import investigate_path_between_nodes, load_graph
from citation_graphs.publication_index import load_publication_index, suggest_publications
"""
new_import = """from citation_graphs.export_helpers import (
    build_compare_markdown_summary,
    build_insights_markdown_summary,
    build_pathfinder_markdown_summary,
)
from citation_graphs.graph_investigation import investigate_graph_relationship
from citation_graphs.path_finder import investigate_path_between_nodes, load_graph
from citation_graphs.publication_index import load_publication_index, suggest_publications
"""
if old_import not in content:
    raise SystemExit("Import block not found in app/streamlit_app.py")
content = content.replace(old_import, new_import)

# Remove Streamlit warning pattern for author multiselect by deleting default=
old_author_multiselect = """        selected_authors = st.multiselect(
            "Indexed author selection",
            options=selection_options,
            default=existing_selected,
            key="search_selected_authors_input",
            help="Selected authors persist even when the filter text changes.",
        )
"""
new_author_multiselect = """        selected_authors = st.multiselect(
            "Indexed author selection",
            options=selection_options,
            key="search_selected_authors_input",
            help="Selected authors persist even when the filter text changes.",
        )
"""
if old_author_multiselect in content:
    content = content.replace(old_author_multiselect, new_author_multiselect)

# Do the same for publication multiselect
old_pub_multiselect = """        selected_publication_titles = st.multiselect(
            "Indexed publication selection",
            options=publication_selection_options,
            default=existing_publication_selected,
            key="publication_selected_titles_input",
            help="Selected publication titles persist even when the filter text changes.",
        )
"""
new_pub_multiselect = """        selected_publication_titles = st.multiselect(
            "Indexed publication selection",
            options=publication_selection_options,
            key="publication_selected_titles_input",
            help="Selected publication titles persist even when the filter text changes.",
        )
"""
if old_pub_multiselect in content:
    content = content.replace(old_pub_multiselect, new_pub_multiselect)

# Add insights markdown download
insights_anchor = """            if report_preview:
                st.markdown("### Report preview")
                st.text_area("Analysis report preview", report_preview[:6000], height=260, key="insights_report_preview")

            st.markdown("### Raw analysis payload")
            st.json(analysis)
"""
insights_replace = """            insights_markdown = build_insights_markdown_summary(selected_base, insights_graph_type, health, narrative)
            st.download_button(
                "Download insights summary (Markdown)",
                data=insights_markdown,
                file_name=f"{selected_base}_{insights_graph_type}_insights_summary.md",
                mime="text/markdown",
                width="stretch",
                key="insights_download_markdown",
            )

            if report_preview:
                st.markdown("### Report preview")
                st.text_area("Analysis report preview", report_preview[:6000], height=260, key="insights_report_preview")

            st.markdown("### Raw analysis payload")
            st.json(analysis)
"""
if insights_anchor not in content:
    raise SystemExit("Insights anchor not found")
content = content.replace(insights_anchor, insights_replace)

# Add compare markdown download
compare_anchor = """        jump_col_1, jump_col_2 = st.columns(2)
        with jump_col_1:
            if st.button("Open this comparison in Path Finder", width="stretch", key="compare_open_in_pathfinder"):
                st.session_state["path_graph_base"] = compare_result.get("graph_base_name")
                st.session_state["path_graph_type"] = "collaboration" if compare_result.get("comparison_mode") == "authors" else "citation"
                source_display = compare_result.get("source_display_name")
                source_id = compare_result.get("source_node_id")
                target_display = compare_result.get("target_display_name")
                target_id = compare_result.get("target_node_id")
                st.session_state["path_source_label"] = f"{source_display} | {source_id}"
                st.session_state["path_target_label"] = f"{target_display} | {target_id}"
                st.success("Path Finder has been prefilled. Open the Path Finder tab to continue.")
        with jump_col_2:
            export_json = json.dumps(compare_result, indent=4, ensure_ascii=False)
            st.download_button(
                "Download comparison JSON",
                data=export_json,
                file_name="comparison_result.json",
                mime="application/json",
                width="stretch",
                key="compare_download_json",
            )
"""
compare_replace = """        jump_col_1, jump_col_2, jump_col_3 = st.columns(3)
        with jump_col_1:
            if st.button("Open this comparison in Path Finder", width="stretch", key="compare_open_in_pathfinder"):
                st.session_state["path_graph_base"] = compare_result.get("graph_base_name")
                st.session_state["path_graph_type"] = "collaboration" if compare_result.get("comparison_mode") == "authors" else "citation"
                source_display = compare_result.get("source_display_name")
                source_id = compare_result.get("source_node_id")
                target_display = compare_result.get("target_display_name")
                target_id = compare_result.get("target_node_id")
                st.session_state["path_source_label"] = f"{source_display} | {source_id}"
                st.session_state["path_target_label"] = f"{target_display} | {target_id}"
                st.success("Path Finder has been prefilled. Open the Path Finder tab to continue.")
        with jump_col_2:
            export_json = json.dumps(compare_result, indent=4, ensure_ascii=False)
            st.download_button(
                "Download comparison JSON",
                data=export_json,
                file_name="comparison_result.json",
                mime="application/json",
                width="stretch",
                key="compare_download_json",
            )
        with jump_col_3:
            compare_markdown = build_compare_markdown_summary(compare_result)
            st.download_button(
                "Download comparison summary (Markdown)",
                data=compare_markdown,
                file_name="comparison_summary.md",
                mime="text/markdown",
                width="stretch",
                key="compare_download_markdown",
            )
"""
if compare_anchor not in content:
    raise SystemExit("Compare anchor not found")
content = content.replace(compare_anchor, compare_replace)

# Add pathfinder markdown download
path_anchor = """        st.markdown("#### Raw investigation payload")
        st.json(result)
"""
path_replace = """        export_cols = st.columns(2)
        with export_cols[0]:
            path_markdown = build_pathfinder_markdown_summary(result, graph_investigation if isinstance(graph_investigation, dict) else None)
            st.download_button(
                "Download path summary (Markdown)",
                data=path_markdown,
                file_name="pathfinder_summary.md",
                mime="text/markdown",
                width="stretch",
                key="path_download_markdown",
            )
        with export_cols[1]:
            export_json = json.dumps(result, indent=4, ensure_ascii=False)
            st.download_button(
                "Download path investigation JSON",
                data=export_json,
                file_name="path_investigation.json",
                mime="application/json",
                width="stretch",
                key="path_download_json",
            )

        st.markdown("#### Raw investigation payload")
        st.json(result)
"""
if path_anchor not in content:
    raise SystemExit("Path anchor not found")
content = content.replace(path_anchor, path_replace)

# Remove older duplicate path JSON button if present
old_dup = """        export_json = json.dumps(result, indent=4, ensure_ascii=False)
        st.download_button(
            "Download path investigation JSON",
            data=export_json,
            file_name="path_investigation.json",
            mime="application/json",
            width="stretch",
            key="path_download_json",
        )
"""
content = content.replace(old_dup, "")

path.write_text(content, encoding="utf-8")
print("Patched app/streamlit_app.py for export / sharing polish")
'@ | Set-Content "._patch_v0141_export_polish.py" -Encoding UTF8

python .\._patch_v0141_export_polish.py
Remove-Item .\._patch_v0141_export_polish.py -Force

Write-Host "V0.14.1 export / sharing polish bootstrap completed."
Write-Host "Created:"
Write-Host " - src\citation_graphs\export_helpers.py"
Write-Host "Updated:"
Write-Host " - app\streamlit_app.py"