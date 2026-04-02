from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.fos_index import load_fos_index

PYTHON_EXECUTABLE = sys.executable

RAW_DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "dblpv13.json"
INSPECTION_DIR = PROJECT_ROOT / "outputs" / "inspection"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "interim" / "normalized"
SUBSETS_DIR = PROJECT_ROOT / "data" / "processed" / "subsets"
GRAPHS_DIR = PROJECT_ROOT / "outputs" / "graphs"
METRICS_DIR = PROJECT_ROOT / "outputs" / "metrics"
FOS_INDEX_PATH = PROJECT_ROOT / "data" / "reference" / "fos_index.json"
EXPORTS_DIR = PROJECT_ROOT / "outputs" / "exports"


def run_command(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, (result.stdout or "Command completed successfully.").strip()
    except subprocess.CalledProcessError as exc:
        output = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        return False, output or "Command failed with no output."


def read_json_if_exists(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def file_exists(path: Path) -> bool:
    return path.exists()


def list_relative_files(directory: Path, suffix: str | None = None) -> list[Path]:
    if not directory.exists():
        return []
    files = [p for p in directory.rglob("*") if p.is_file()]
    if suffix:
        files = [p for p in files if p.suffix.lower() == suffix.lower()]
    return sorted(files)


def list_subset_dirs() -> list[Path]:
    if not SUBSETS_DIR.exists():
        return []
    return sorted([p for p in SUBSETS_DIR.iterdir() if p.is_dir()])


def list_graph_summaries() -> list[Path]:
    if not GRAPHS_DIR.exists():
        return []
    return sorted(GRAPHS_DIR.glob("*_summary.json"))


def list_metric_jsons() -> list[Path]:
    if not METRICS_DIR.exists():
        return []
    return sorted([p for p in METRICS_DIR.glob("*.json") if p.name != ".gitkeep"])


def extract_graph_base_names() -> list[str]:
    base_names: set[str] = set()
    for summary_path in list_graph_summaries():
        name = summary_path.name
        if name.endswith("_citation_summary.json"):
            base_names.add(name.replace("_citation_summary.json", ""))
        elif name.endswith("_collaboration_summary.json"):
            base_names.add(name.replace("_collaboration_summary.json", ""))
    return sorted(base_names)


def extract_analysis_base_names() -> list[str]:
    base_names: set[str] = set()
    for path in list_metric_jsons():
        name = path.name
        if name.endswith("_citation_analysis.json"):
            base_names.add(name.replace("_citation_analysis.json", ""))
        elif name.endswith("_collaboration_analysis.json"):
            base_names.add(name.replace("_collaboration_analysis.json", ""))
    return sorted(base_names)


@st.cache_data(show_spinner=False)
def get_available_fos_values() -> list[str]:
    return load_fos_index(FOS_INDEX_PATH)


def status_text(ok: bool) -> str:
    return "Ready" if ok else "Missing"


def render_json_card(title: str, data: Any) -> None:
    st.markdown(f"#### {title}")
    if data is None:
        st.info("No data available.")
    else:
        st.json(data)


def render_files_list(title: str, files: list[Path], limit: int = 100) -> None:
    st.markdown(f"#### {title}")
    if not files:
        st.info("No files found.")
        return
    display_lines = [str(p.relative_to(PROJECT_ROOT)) for p in files[:limit]]
    st.code("\n".join(display_lines))
    if len(files) > limit:
        st.caption(f"Showing first {limit} files out of {len(files)}.")


def metric_card(title: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(128,128,128,0.25);
            border-radius:16px;
            padding:16px;
            min-height:120px;
            background: rgba(255,255,255,0.02);
        ">
            <div style="font-size:0.95rem; opacity:0.85;">{title}</div>
            <div style="font-size:1.6rem; font-weight:700; margin-top:8px;">{value}</div>
            <div style="font-size:0.85rem; opacity:0.7; margin-top:8px;">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str = "") -> None:
    st.markdown(f"## {title}")
    if description:
        st.caption(description)


def render_table_from_list(title: str, rows: list[dict[str, Any]]) -> None:
    st.markdown(f"#### {title}")
    if not rows:
        st.info("No rows available.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


st.set_page_config(
    page_title="Citation & Collaboration Graph Pipeline",
    page_icon="ðŸ“Š",
    layout="wide",
)

st.title("Citation & Collaboration Graph Pipeline")
st.caption("AMiner DBLP-Citation-network V13 Â· local data engineering + graph analytics workbench")

with st.sidebar:
    st.header("Workspace")
    st.write(f"**Raw**: `{RAW_DATASET_PATH}`")
    st.write(f"**Normalized**: `{NORMALIZED_DIR}`")
    st.write(f"**Subsets**: `{SUBSETS_DIR}`")
    st.write(f"**Graphs**: `{GRAPHS_DIR}`")
    st.write(f"**Metrics**: `{METRICS_DIR}`")
    st.write(f"**Exports**: `{EXPORTS_DIR}`")
    st.write(f"**FOS index**: `{FOS_INDEX_PATH}`")

    st.markdown("---")
    st.header("Status")
    st.write("Raw dataset:", status_text(file_exists(RAW_DATASET_PATH)))
    st.write("Inspection:", status_text(file_exists(INSPECTION_DIR / "raw_profile.json")))
    st.write("Normalization:", status_text(file_exists(NORMALIZED_DIR / "_normalization_summary.json")))
    st.write("FOS index:", status_text(file_exists(FOS_INDEX_PATH)))
    st.write("Subsets:", status_text(len(list_subset_dirs()) > 0))
    st.write("Graphs:", status_text(len(list_graph_summaries()) > 0))
    st.write("Metrics:", status_text(len(list_metric_jsons()) > 0))

overview_tab, demo_tab, inspect_tab, normalize_tab, filter_tab, graph_tab, analyze_tab, insights_tab, artifacts_tab = st.tabs(
    [
        "Overview",
        "Demo",
        "Inspect Raw",
        "Normalize",
        "Filter Subset",
        "Build Graph",
        "Analyze Graph",
        "Insights",
        "Artifacts",
    ]
)

with overview_tab:
    section_header("Pipeline Overview", "High-level status of each stage and latest outputs.")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        metric_card("Raw dataset", status_text(file_exists(RAW_DATASET_PATH)), f"{round(RAW_DATASET_PATH.stat().st_size / (1024**3), 2)} GB" if RAW_DATASET_PATH.exists() else "Dataset not found")
    with c2:
        metric_card("Inspection", status_text(file_exists(INSPECTION_DIR / "raw_profile.json")), "Raw profile + samples")
    with c3:
        metric_card("Normalization", status_text(file_exists(NORMALIZED_DIR / "_normalization_summary.json")), "Partitioned parquet")
    with c4:
        metric_card("FOS index", status_text(file_exists(FOS_INDEX_PATH)), "Cached exact FOS values")
    with c5:
        subsets = list_subset_dirs()
        metric_card("Subsets", str(len(subsets)), "Filtered datasets available")
    with c6:
        metric_card("Graphs", str(len(list_graph_summaries())), "Graph summary files")

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        render_json_card("Latest inspection profile", read_json_if_exists(INSPECTION_DIR / "raw_profile.json"))
    with right:
        render_json_card("Latest normalization summary", read_json_if_exists(NORMALIZED_DIR / "_normalization_summary.json"))

with demo_tab:
    section_header("Demo Workflow", "Run a short end-to-end demo without typing paths manually.")

    demo_subset_name = st.text_input("Demo subset name", value="year_2020_demo")
    demo_graph_type = st.selectbox("Demo graph type", ["citation", "collaboration"], key="demo_graph_type")
    demo_limit = st.number_input("Demo graph record limit", min_value=100, max_value=50000, value=2000, step=100)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("1. Refresh FOS index", use_container_width=True):
            command = [
                PYTHON_EXECUTABLE,
                "scripts/extract_fos_index.py",
                "--input",
                str(NORMALIZED_DIR),
                "--output",
                str(FOS_INDEX_PATH),
            ]
            success, output = run_command(command)
            st.code(output)
            if success:
                st.cache_data.clear()
                st.success("FOS index refreshed.")
            else:
                st.error("Refresh failed.")

    with c2:
        if st.button("2. Create demo subset", use_container_width=True):
            command = [
                PYTHON_EXECUTABLE,
                "scripts/filter_dataset.py",
                "--input",
                str(NORMALIZED_DIR),
                "--output",
                str(SUBSETS_DIR),
                "--mode",
                "year",
                "--year",
                "2020",
                "--subset-name",
                demo_subset_name,
                "--overwrite",
            ]
            success, output = run_command(command)
            st.code(output)
            if success:
                st.success("Demo subset created.")
            else:
                st.error("Subset creation failed.")

    with c3:
        if st.button("3. Build demo graph", use_container_width=True):
            command = [
                PYTHON_EXECUTABLE,
                "scripts/build_graph.py",
                "--input",
                str(SUBSETS_DIR / demo_subset_name / "data.parquet"),
                "--output",
                str(GRAPHS_DIR),
                "--graph-type",
                demo_graph_type,
                "--graph-name",
                demo_subset_name,
                "--limit",
                str(demo_limit),
            ]
            success, output = run_command(command)
            st.code(output)
            if success:
                st.success("Demo graph built.")
            else:
                st.error("Graph build failed.")

    with c4:
        if st.button("4. Analyze demo graph", use_container_width=True):
            command = [
                PYTHON_EXECUTABLE,
                "scripts/analyze_graph.py",
                "--input",
                str(GRAPHS_DIR / f"{demo_subset_name}_{demo_graph_type}.gexf"),
                "--output",
                str(METRICS_DIR / f"{demo_subset_name}_{demo_graph_type}_analysis.json"),
                "--top-n",
                "10",
                "--betweenness-sample-k",
                "100",
            ]
            success, output = run_command(command)
            st.code(output)
            if success:
                st.success("Demo analysis completed.")
            else:
                st.error("Analysis failed.")

    demo_summary = read_json_if_exists(SUBSETS_DIR / demo_subset_name / "_subset_summary.json")
    demo_graph_summary = read_json_if_exists(GRAPHS_DIR / f"{demo_subset_name}_{demo_graph_type}_summary.json")
    demo_analysis = read_json_if_exists(METRICS_DIR / f"{demo_subset_name}_{demo_graph_type}_analysis.json")

    left, middle, right = st.columns(3)
    with left:
        render_json_card("Demo subset summary", demo_summary)
    with middle:
        render_json_card("Demo graph summary", demo_graph_summary)
    with right:
        render_json_card("Demo analysis", demo_analysis)

with inspect_tab:
    section_header("Inspect Raw Dataset", "Sample the source file safely and profile its structure.")
    max_records = st.slider("Sample record count", min_value=1, max_value=20, value=3)
    if st.button("Run raw inspection", use_container_width=True):
        command = [
            PYTHON_EXECUTABLE,
            "scripts/inspect_raw.py",
            "--input",
            str(RAW_DATASET_PATH),
            "--max-records",
            str(max_records),
        ]
        success, output = run_command(command)
        st.code(output)
        if success:
            st.success("Inspection completed.")
        else:
            st.error("Inspection failed.")

    col1, col2 = st.columns(2)
    with col1:
        render_json_card("raw_profile.json", read_json_if_exists(INSPECTION_DIR / "raw_profile.json"))
    with col2:
        render_json_card("raw_samples.json", read_json_if_exists(INSPECTION_DIR / "raw_samples.json"))

with normalize_tab:
    section_header("Normalize Dataset", "Convert the raw non-standard JSON array into partitioned parquet.")
    col1, col2, col3 = st.columns(3)
    with col1:
        batch_size = st.number_input("Batch size", min_value=1000, max_value=50000, value=10000, step=1000)
    with col2:
        min_year = st.number_input("Minimum valid year", min_value=0, max_value=3000, value=1800)
    with col3:
        max_year = st.number_input("Maximum valid year", min_value=0, max_value=3000, value=2026)
    overwrite = st.checkbox("Overwrite normalized output directory", value=False)

    if st.button("Run normalization", use_container_width=True):
        command = [
            PYTHON_EXECUTABLE,
            "scripts/normalize_dataset.py",
            "--input",
            str(RAW_DATASET_PATH),
            "--output",
            str(NORMALIZED_DIR),
            "--batch-size",
            str(batch_size),
            "--min-year",
            str(min_year),
            "--max-year",
            str(max_year),
        ]
        if overwrite:
            command.append("--overwrite")
        success, output = run_command(command)
        st.code(output)
        if success:
            st.success("Normalization completed.")
        else:
            st.error("Normalization failed.")

    render_json_card("_normalization_summary.json", read_json_if_exists(NORMALIZED_DIR / "_normalization_summary.json"))

with filter_tab:
    section_header("Create Filtered Subset", "Build a clean subset by year, range, exact FOS, or year + FOS.")

    subset_dirs = list_subset_dirs()
    existing_subset_names = [p.name for p in subset_dirs]
    available_fos = get_available_fos_values()

    info1, info2, info3 = st.columns(3)
    with info1:
        metric_card("Existing subsets", str(len(existing_subset_names)), "Currently available")
    with info2:
        metric_card("Distinct FOS", str(len(available_fos)), "Loaded from cached index")
    with info3:
        metric_card("FOS index status", status_text(file_exists(FOS_INDEX_PATH)), "Use refresh if missing or outdated")

    refresh_col1, refresh_col2 = st.columns([1, 2])
    with refresh_col1:
        if st.button("Refresh FOS index", use_container_width=True):
            command = [
                PYTHON_EXECUTABLE,
                "scripts/extract_fos_index.py",
                "--input",
                str(NORMALIZED_DIR),
                "--output",
                str(FOS_INDEX_PATH),
            ]
            success, output = run_command(command)
            st.code(output)
            if success:
                st.cache_data.clear()
                st.success("FOS index refreshed.")
            else:
                st.error("FOS index refresh failed.")
    with refresh_col2:
        st.caption("The FOS selector reads from a persisted JSON index instead of scanning parquet on every page load.")

    st.markdown("---")

    mode = st.selectbox("Filter mode", ["year", "range", "fos", "year_fos"])
    default_subset_name = "year_2020" if "year_2020" not in existing_subset_names else "year_2020_new"
    subset_name = st.text_input("Subset name", value=default_subset_name)

    year = None
    start_year = None
    end_year = None
    selected_fos_values: list[str] = []

    if mode == "year":
        year = st.number_input("Year", min_value=1800, max_value=2026, value=2020)
    elif mode == "range":
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input("Start year", min_value=1800, max_value=2026, value=2018)
        with col2:
            end_year = st.number_input("End year", min_value=1800, max_value=2026, value=2021)
    elif mode == "fos":
        selected_fos_values = st.multiselect(
            "Fields of Study",
            options=available_fos,
            default=[],
            placeholder="Type to search exact FOS values...",
        )
    elif mode == "year_fos":
        year = st.number_input("Year", min_value=1800, max_value=2026, value=2020)
        selected_fos_values = st.multiselect(
            "Fields of Study",
            options=available_fos,
            default=[],
            placeholder="Type to search exact FOS values...",
        )

    overwrite_subset = st.checkbox("Overwrite subset directory", value=False)

    if selected_fos_values:
        st.markdown("#### Selected FOS")
        st.write(selected_fos_values)

    if st.button("Create subset", use_container_width=True):
        command = [
            PYTHON_EXECUTABLE,
            "scripts/filter_dataset.py",
            "--input",
            str(NORMALIZED_DIR),
            "--output",
            str(SUBSETS_DIR),
            "--mode",
            mode,
            "--subset-name",
            subset_name,
        ]

        if mode == "year":
            command.extend(["--year", str(year)])
        elif mode == "range":
            command.extend(["--start-year", str(start_year), "--end-year", str(end_year)])
        elif mode == "fos":
            if selected_fos_values:
                command.extend(["--fos-values", *selected_fos_values])
        elif mode == "year_fos":
            command.extend(["--year", str(year)])
            if selected_fos_values:
                command.extend(["--fos-values", *selected_fos_values])

        if overwrite_subset:
            command.append("--overwrite")

        success, output = run_command(command)
        st.code(output)
        if success:
            st.success("Subset creation completed.")
        else:
            st.error("Subset creation failed.")

    selected_subset = st.selectbox("Existing subsets", options=existing_subset_names if existing_subset_names else ["<none>"], index=0)
    if selected_subset != "<none>":
        render_json_card(
            f"{selected_subset}/_subset_summary.json",
            read_json_if_exists(SUBSETS_DIR / selected_subset / "_subset_summary.json"),
        )

with graph_tab:
    section_header("Build Graph", "Create citation or collaboration graphs from an existing subset.")
    subset_dirs = list_subset_dirs()
    subset_names = [p.name for p in subset_dirs]

    selected_subset_name = st.selectbox("Choose subset", options=subset_names if subset_names else ["<none>"], index=0, key="graph_subset")
    graph_type = st.selectbox("Graph type", ["citation", "collaboration"])
    graph_name = st.text_input("Graph name", value=selected_subset_name if selected_subset_name != "<none>" else "graph")
    limit_value = st.number_input("Limit records (0 = no limit)", min_value=0, max_value=1000000, value=5000)

    if st.button("Build graph", use_container_width=True):
        if selected_subset_name == "<none>":
            st.error("No subset available.")
        else:
            subset_parquet = SUBSETS_DIR / selected_subset_name / "data.parquet"
            command = [
                PYTHON_EXECUTABLE,
                "scripts/build_graph.py",
                "--input",
                str(subset_parquet),
                "--output",
                str(GRAPHS_DIR),
                "--graph-type",
                graph_type,
                "--graph-name",
                graph_name,
            ]
            if limit_value > 0:
                command.extend(["--limit", str(limit_value)])
            success, output = run_command(command)
            st.code(output)
            if success:
                st.success("Graph build completed.")
            else:
                st.error("Graph build failed.")

    summary_path = GRAPHS_DIR / f"{graph_name}_{graph_type}_summary.json"
    render_json_card(f"{graph_name}_{graph_type}_summary.json", read_json_if_exists(summary_path))

with analyze_tab:
    section_header("Analyze Graph", "Compute graph summary, communities, centralities and PageRank.")
    graph_bases = extract_graph_base_names()
    selected_base = st.selectbox("Choose graph base name", options=graph_bases if graph_bases else ["<none>"], index=0)
    selected_graph_type = st.selectbox("Graph type to analyze", ["citation", "collaboration"], key="analysis_graph_type")
    top_n = st.number_input("Top N", min_value=1, max_value=100, value=10)
    exact_betweenness = st.checkbox("Exact betweenness (slow)", value=False)
    betweenness_sample_k = st.number_input("Betweenness sample k", min_value=10, max_value=5000, value=200)

    if selected_base != "<none>":
        graph_input = GRAPHS_DIR / f"{selected_base}_{selected_graph_type}.gexf"
        analysis_output = METRICS_DIR / f"{selected_base}_{selected_graph_type}_analysis.json"
    else:
        graph_input = GRAPHS_DIR / "graph.gexf"
        analysis_output = METRICS_DIR / "graph_analysis.json"

    st.code(f"Input graph: {graph_input}")
    st.code(f"Output analysis: {analysis_output}")

    if st.button("Run analysis", use_container_width=True):
        if selected_base == "<none>":
            st.error("No graph available.")
        else:
            command = [
                PYTHON_EXECUTABLE,
                "scripts/analyze_graph.py",
                "--input",
                str(graph_input),
                "--output",
                str(analysis_output),
                "--top-n",
                str(top_n),
                "--betweenness-sample-k",
                str(betweenness_sample_k),
            ]
            if exact_betweenness:
                command.append("--exact-betweenness")
            success, output = run_command(command)
            st.code(output)
            if success:
                st.success("Graph analysis completed.")
            else:
                st.error("Graph analysis failed.")

    render_json_card(analysis_output.name, read_json_if_exists(analysis_output))

with insights_tab:
    section_header("Graph Insights Dashboard", "Explore existing analysis results and export key rankings to CSV.")

    analysis_bases = extract_analysis_base_names()
    selected_insight_base = st.selectbox(
        "Choose analysis base name",
        options=analysis_bases if analysis_bases else ["<none>"],
        index=0,
    )
    selected_insight_type = st.selectbox(
        "Analysis graph type",
        ["citation", "collaboration"],
        key="insight_graph_type",
    )

    if selected_insight_base != "<none>":
        analysis_path = METRICS_DIR / f"{selected_insight_base}_{selected_insight_type}_analysis.json"
        analysis = read_json_if_exists(analysis_path)
    else:
        analysis_path = METRICS_DIR / "analysis.json"
        analysis = None

    export_dir = EXPORTS_DIR / f"{selected_insight_base}_{selected_insight_type}" if selected_insight_base != "<none>" else EXPORTS_DIR / "analysis"

    export_col1, export_col2 = st.columns([1, 2])
    with export_col1:
        if st.button("Export analysis CSV", use_container_width=True):
            if selected_insight_base == "<none>":
                st.error("No analysis available.")
            else:
                command = [
                    PYTHON_EXECUTABLE,
                    "scripts/export_analysis_csv.py",
                    "--input",
                    str(analysis_path),
                    "--output-dir",
                    str(export_dir),
                ]
                success, output = run_command(command)
                st.code(output)
                if success:
                    st.success("CSV export completed.")
                else:
                    st.error("CSV export failed.")
    with export_col2:
        st.caption("Exports pagerank, degree, closeness, betweenness and communities to CSV.")

    if isinstance(analysis, dict):
        summary = analysis.get("summary", {})
        communities = analysis.get("communities", {})
        pagerank = analysis.get("pagerank", [])
        degree = analysis.get("centralities", {}).get("degree", [])
        closeness = analysis.get("centralities", {}).get("closeness", [])
        betweenness = analysis.get("centralities", {}).get("betweenness", [])

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            metric_card("Nodes", str(summary.get("num_nodes", "")), "Graph size")
        with c2:
            metric_card("Edges", str(summary.get("num_edges", "")), "Connectivity")
        with c3:
            metric_card("Density", str(summary.get("density", "")), "Global density")
        with c4:
            metric_card("Diameter", str(summary.get("largest_component_diameter", "")), str(summary.get("largest_component_diameter_mode", "")))
        with c5:
            metric_card("Communities", str(communities.get("num_communities", "")), "Detected with Louvain")

        st.markdown("---")

        left, right = st.columns(2)
        with left:
            render_table_from_list("Top PageRank", pagerank)
            render_table_from_list("Top Degree Centrality", degree)
        with right:
            render_table_from_list("Top Closeness Centrality", closeness)
            render_table_from_list("Top Betweenness Centrality", betweenness)

        st.markdown("---")
        largest_communities = communities.get("largest_communities", [])
        render_table_from_list("Largest Communities", largest_communities)

        if largest_communities:
            community_df = pd.DataFrame(largest_communities)
            community_df = community_df.set_index("community_id")
            st.markdown("#### Largest community sizes")
            st.bar_chart(community_df["size"])

        export_files = list_relative_files(export_dir) if export_dir.exists() else []
        render_files_list("Exported CSV files", export_files, limit=50)
    else:
        st.info("No analysis file available for the selected graph.")

with artifacts_tab:
    section_header("Artifacts Explorer", "Browse generated files across inspection, subsets, graphs, metrics and exports.")
    c1, c2 = st.columns(2)
    with c1:
        render_files_list("Inspection files", list_relative_files(INSPECTION_DIR))
        render_files_list("Graph files", list_relative_files(GRAPHS_DIR), limit=200)
        render_files_list("Export files", list_relative_files(EXPORTS_DIR), limit=200)
    with c2:
        render_files_list("Metric files", list_relative_files(METRICS_DIR), limit=200)
        render_files_list("Subset files", list_relative_files(SUBSETS_DIR), limit=200)
