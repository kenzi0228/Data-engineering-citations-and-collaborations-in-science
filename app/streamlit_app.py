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
from citation_graphs.manifests import append_pipeline_run, read_pipeline_runs

PYTHON_EXECUTABLE = sys.executable

RAW_DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "dblpv13.json"
INSPECTION_DIR = PROJECT_ROOT / "outputs" / "inspection"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "interim" / "normalized"
SUBSETS_DIR = PROJECT_ROOT / "data" / "processed" / "subsets"
GRAPHS_DIR = PROJECT_ROOT / "outputs" / "graphs"
METRICS_DIR = PROJECT_ROOT / "outputs" / "metrics"
EXPORTS_DIR = PROJECT_ROOT / "outputs" / "exports"
FOS_INDEX_PATH = PROJECT_ROOT / "data" / "reference" / "fos_index.json"
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
MANIFEST_PATH = PROJECT_ROOT / "outputs" / "manifests" / "pipeline_runs.jsonl"
QUALITY_DIR = PROJECT_ROOT / "outputs" / "quality"


def run_command(command: list[str], stage: str, parameters: dict[str, Any] | None = None, outputs: dict[str, Any] | None = None) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        append_pipeline_run(
            MANIFEST_PATH,
            stage=stage,
            status="success",
            parameters=parameters,
            outputs=outputs,
            message=(result.stdout or "").strip(),
        )
        return True, (result.stdout or "Command completed successfully.").strip()
    except subprocess.CalledProcessError as exc:
        output = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        append_pipeline_run(
            MANIFEST_PATH,
            stage=stage,
            status="failed",
            parameters=parameters,
            outputs=outputs,
            message=output,
        )
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


def list_relative_files(directory: Path, suffix: str | None = None, limit: int = 100) -> list[Path]:
    if not directory.exists():
        return []
    files = [p for p in directory.rglob("*") if p.is_file()]
    if suffix:
        files = [p for p in files if p.suffix.lower() == suffix.lower()]
    return sorted(files)[:limit]


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


def list_sample_parquets() -> list[Path]:
    if not SAMPLE_DIR.exists():
        return []
    return sorted(SAMPLE_DIR.glob("*.parquet"))


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


def metric_card(title: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(128,128,128,0.25);
            border-radius:16px;
            padding:14px;
            min-height:110px;
            background: rgba(255,255,255,0.02);
        ">
            <div style="font-size:0.95rem; opacity:0.85;">{title}</div>
            <div style="font-size:1.45rem; font-weight:700; margin-top:8px;">{value}</div>
            <div style="font-size:0.82rem; opacity:0.7; margin-top:8px;">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str = "") -> None:
    st.markdown(f"## {title}")
    if description:
        st.caption(description)


def render_json_summary(title: str, data: Any) -> None:
    st.markdown(f"#### {title}")
    if data is None:
        st.info("No data available.")
        return

    if isinstance(data, dict):
        preview = {}
        for key, value in list(data.items())[:12]:
            if isinstance(value, list):
                preview[key] = f"list[{len(value)}]"
            elif isinstance(value, dict):
                preview[key] = f"dict[{len(value)}]"
            else:
                preview[key] = value
        st.json(preview)
    elif isinstance(data, list):
        st.write(f"List with {len(data)} item(s).")
        if data:
            first = data[0]
            if isinstance(first, dict):
                st.json(first)
            else:
                st.write(first)
    else:
        st.write(data)


def render_json_details_toggle(title: str, data: Any, key: str) -> None:
    if data is None:
        return
    if st.checkbox(f"Show full {title}", key=key):
        st.json(data)


def render_files_list(title: str, files: list[Path]) -> None:
    st.markdown(f"#### {title}")
    if not files:
        st.info("No files found.")
        return
    display_lines = [str(p.relative_to(PROJECT_ROOT)) for p in files]
    st.code("\n".join(display_lines))


def render_table_from_list(title: str, rows: list[dict[str, Any]], max_rows: int = 20) -> None:
    st.markdown(f"#### {title}")
    if not rows:
        st.info("No rows available.")
        return
    df = pd.DataFrame(rows[:max_rows])
    if "details" in df.columns:
        df = df.drop(columns=["details"])
    st.dataframe(df, width="stretch", height=min(420, 80 + 35 * len(df)))


def raise_ui_error(message: str, category: str = "error") -> None:
    if category == "warning":
        st.warning(message)
    else:
        st.error(message)


st.set_page_config(
    page_title="Citation & Collaboration Graph Pipeline",
    page_icon="ðŸ“Š",
    layout="wide",
)

st.title("Citation & Collaboration Graph Pipeline")
st.caption("Performance-safe interface")

overview_tab, demo_tab, inspect_tab, normalize_tab, filter_tab, graph_tab, analyze_tab, insights_tab, quality_tab, history_tab, artifacts_tab = st.tabs(
    [
        "Overview",
        "Demo",
        "Inspect Raw",
        "Normalize",
        "Filter Subset",
        "Build Graph",
        "Analyze Graph",
        "Insights",
        "Data Quality",
        "Run History",
        "Artifacts",
    ]
)

with overview_tab:
    section_header("Pipeline Overview", "Compact status without heavy payload rendering.")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        metric_card("Raw", status_text(file_exists(RAW_DATASET_PATH)), "Source dataset")
    with c2:
        metric_card("Inspection", status_text(file_exists(INSPECTION_DIR / "raw_profile.json")), "Profile ready")
    with c3:
        metric_card("Normalization", status_text(file_exists(NORMALIZED_DIR / "_normalization_summary.json")), "Parquet ready")
    with c4:
        metric_card("FOS index", status_text(file_exists(FOS_INDEX_PATH)), "Cached values")
    with c5:
        metric_card("Samples", str(len(list_sample_parquets())), "Demo parquet files")
    with c6:
        metric_card("Runs", str(len(read_pipeline_runs(MANIFEST_PATH))), "History entries")

with demo_tab:
    section_header("Demo Workflow", "Choose an existing sample or create a new one, then build/analyze it.")

    sample_parquets = list_sample_parquets()
    sample_names = [p.name for p in sample_parquets]

    mode = st.radio("Demo mode", ["Use existing sample", "Create new sample"], horizontal=True)
    selected_sample_path: Path | None = None

    if mode == "Use existing sample":
        if sample_names:
            selected_sample_name = st.selectbox("Choose sample parquet", options=sample_names)
            selected_sample_path = SAMPLE_DIR / selected_sample_name
        else:
            st.info("No sample parquet found yet.")
    else:
        subset_names = [p.name for p in list_subset_dirs()]
        selected_subset = st.selectbox("Source subset", options=subset_names if subset_names else ["<none>"])
        new_sample_name = st.text_input("New sample file name", value="demo_subset_2020.parquet")
        sample_row_limit = st.number_input("Sample row limit", min_value=100, max_value=10000, value=1000, step=100)

        if st.button("Create sample parquet", width="stretch"):
            if selected_subset == "<none>":
                raise_ui_error("No subset available to create a sample.")
            elif not new_sample_name.endswith(".parquet"):
                raise_ui_error("Sample file name must end with .parquet")
            else:
                sample_output = SAMPLE_DIR / new_sample_name
                sample_metadata = SAMPLE_DIR / new_sample_name.replace(".parquet", "_metadata.json")
                command = [
                    PYTHON_EXECUTABLE,
                    "scripts/create_sample_dataset.py",
                    "--input",
                    str(SUBSETS_DIR / selected_subset / "data.parquet"),
                    "--output",
                    str(sample_output),
                    "--metadata",
                    str(sample_metadata),
                    "--row-limit",
                    str(sample_row_limit),
                ]
                success, output = run_command(
                    command,
                    stage="create_sample_dataset",
                    parameters={"input_subset": selected_subset, "row_limit": sample_row_limit},
                    outputs={"sample_parquet": str(sample_output), "metadata": str(sample_metadata)},
                )
                st.code(output)
                if success:
                    st.success("Sample parquet created.")
                    selected_sample_path = sample_output
                else:
                    st.error("Sample extraction failed.")

    st.markdown("---")

    demo_graph_type = st.selectbox("Demo graph type", ["citation", "collaboration"])
    demo_graph_name = st.text_input("Demo graph name", value="sample_demo")
    overwrite_demo_graph = st.checkbox("Overwrite demo graph", value=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Refresh FOS index", width="stretch"):
            command = [
                PYTHON_EXECUTABLE,
                "scripts/extract_fos_index.py",
                "--input",
                str(NORMALIZED_DIR),
                "--output",
                str(FOS_INDEX_PATH),
            ]
            success, output = run_command(command, stage="refresh_fos_index", parameters={"input": str(NORMALIZED_DIR)}, outputs={"output": str(FOS_INDEX_PATH)})
            st.code(output)
            if success:
                st.cache_data.clear()
                st.success("FOS index refreshed.")
            else:
                st.error("Refresh failed.")

    with col2:
        if st.button("Build demo graph", width="stretch"):
            current_sample = selected_sample_path
            if current_sample is None and mode == "Use existing sample" and sample_names:
                current_sample = SAMPLE_DIR / selected_sample_name

            if current_sample is None:
                raise_ui_error("No sample parquet selected.")
            else:
                command = [
                    PYTHON_EXECUTABLE,
                    "scripts/build_graph.py",
                    "--input",
                    str(current_sample),
                    "--output",
                    str(GRAPHS_DIR),
                    "--graph-type",
                    demo_graph_type,
                    "--graph-name",
                    demo_graph_name,
                ]
                if overwrite_demo_graph:
                    command.append("--overwrite")
                success, output = run_command(
                    command,
                    stage="build_demo_graph",
                    parameters={"sample": str(current_sample), "graph_type": demo_graph_type},
                    outputs={"graph_name": f"{demo_graph_name}_{demo_graph_type}"},
                )
                st.code(output)
                if success:
                    st.success("Demo graph built.")
                else:
                    st.error("Demo graph build failed.")

    with col3:
        if st.button("Analyze demo graph", width="stretch"):
            graph_input = GRAPHS_DIR / f"{demo_graph_name}_{demo_graph_type}.gexf"
            analysis_output = METRICS_DIR / f"{demo_graph_name}_{demo_graph_type}_analysis.json"

            if not graph_input.exists():
                raise_ui_error(f"Graph file not found: {graph_input}")
            else:
                command = [
                    PYTHON_EXECUTABLE,
                    "scripts/analyze_graph.py",
                    "--input",
                    str(graph_input),
                    "--output",
                    str(analysis_output),
                    "--top-n",
                    "10",
                    "--betweenness-sample-k",
                    "100",
                ]
                success, output = run_command(
                    command,
                    stage="analyze_demo_graph",
                    parameters={"graph_input": str(graph_input)},
                    outputs={"analysis_output": str(analysis_output)},
                )
                st.code(output)
                if success:
                    st.success("Demo analysis completed.")
                else:
                    st.error("Demo analysis failed.")

    st.markdown("---")

    current_sample_name = None
    if mode == "Use existing sample" and sample_names:
        current_sample_name = selected_sample_name
    elif selected_sample_path is not None:
        current_sample_name = selected_sample_path.name

    current_metadata = SAMPLE_DIR / current_sample_name.replace(".parquet", "_metadata.json") if current_sample_name else None
    current_graph_summary = GRAPHS_DIR / f"{demo_graph_name}_{demo_graph_type}_summary.json"
    current_analysis = METRICS_DIR / f"{demo_graph_name}_{demo_graph_type}_analysis.json"

    left, middle, right = st.columns(3)
    with left:
        sample_meta = read_json_if_exists(current_metadata) if current_metadata else None
        render_json_summary("Sample metadata", sample_meta)
        render_json_details_toggle("sample metadata", sample_meta, "demo_meta_full")
    with middle:
        graph_summary = read_json_if_exists(current_graph_summary)
        render_json_summary("Demo graph summary", graph_summary)
        render_json_details_toggle("demo graph summary", graph_summary, "demo_graph_summary_full")
    with right:
        analysis = read_json_if_exists(current_analysis)
        render_json_summary("Demo analysis", analysis)
        render_json_details_toggle("demo analysis", analysis, "demo_analysis_full")

with inspect_tab:
    section_header("Inspect Raw Dataset", "Compact inspection view.")
    max_records = st.slider("Sample record count", min_value=1, max_value=20, value=3)

    if st.button("Run raw inspection", width="stretch"):
        command = [PYTHON_EXECUTABLE, "scripts/inspect_raw.py", "--input", str(RAW_DATASET_PATH), "--max-records", str(max_records)]
        success, output = run_command(command, stage="inspect_raw", parameters={"max_records": max_records}, outputs={"profile": str(INSPECTION_DIR / "raw_profile.json")})
        st.code(output)
        if success:
            st.success("Inspection completed.")
        else:
            st.error("Inspection failed.")

    profile = read_json_if_exists(INSPECTION_DIR / "raw_profile.json")
    samples = read_json_if_exists(INSPECTION_DIR / "raw_samples.json")

    c1, c2 = st.columns(2)
    with c1:
        render_json_summary("raw_profile.json", profile)
        render_json_details_toggle("raw profile", profile, "inspect_profile_full")
    with c2:
        render_json_summary("raw_samples.json", samples)
        render_json_details_toggle("raw samples", samples, "inspect_samples_full")

with normalize_tab:
    section_header("Normalize Dataset", "Run normalization without heavy auto-render.")
    col1, col2, col3 = st.columns(3)
    with col1:
        batch_size = st.number_input("Batch size", min_value=1000, max_value=50000, value=10000, step=1000)
    with col2:
        min_year = st.number_input("Minimum valid year", min_value=0, max_value=3000, value=1800)
    with col3:
        max_year = st.number_input("Maximum valid year", min_value=0, max_value=3000, value=2026)
    overwrite = st.checkbox("Overwrite normalized output directory", value=False)

    if st.button("Run normalization", width="stretch"):
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
        success, output = run_command(command, stage="normalize_dataset", parameters={"batch_size": batch_size}, outputs={"output_dir": str(NORMALIZED_DIR)})
        st.code(output)
        if success:
            st.success("Normalization completed.")
        else:
            st.error("Normalization failed.")

    norm_summary = read_json_if_exists(NORMALIZED_DIR / "_normalization_summary.json")
    render_json_summary("_normalization_summary.json", norm_summary)
    render_json_details_toggle("normalization summary", norm_summary, "norm_summary_full")

with filter_tab:
    section_header("Create Filtered Subset", "Only render compact summaries.")
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
        c1, c2 = st.columns(2)
        with c1:
            start_year = st.number_input("Start year", min_value=1800, max_value=2026, value=2018)
        with c2:
            end_year = st.number_input("End year", min_value=1800, max_value=2026, value=2021)
    elif mode == "fos":
        selected_fos_values = st.multiselect("Fields of Study", options=available_fos, default=[], placeholder="Type to search exact FOS values...")
    elif mode == "year_fos":
        year = st.number_input("Year", min_value=1800, max_value=2026, value=2020)
        selected_fos_values = st.multiselect("Fields of Study", options=available_fos, default=[], placeholder="Type to search exact FOS values...")

    overwrite_subset = st.checkbox("Overwrite subset directory", value=False)

    if st.button("Create subset", width="stretch"):
        if not subset_name.strip():
            raise_ui_error("Subset name cannot be empty.")
        elif mode == "range" and start_year is not None and end_year is not None and start_year > end_year:
            raise_ui_error("Start year must be less than or equal to end year.")
        elif mode in ("fos", "year_fos") and not selected_fos_values:
            raise_ui_error("Select at least one Field of Study.")
        else:
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
                command.extend(["--fos-values", *selected_fos_values])
            elif mode == "year_fos":
                command.extend(["--year", str(year), "--fos-values", *selected_fos_values])

            if overwrite_subset:
                command.append("--overwrite")

            success, output = run_command(command, stage="create_subset", parameters={"mode": mode, "subset_name": subset_name}, outputs={"subset": subset_name})
            st.code(output)
            if success:
                st.success("Subset creation completed.")
            else:
                st.error("Subset creation failed.")

    selected_subset = st.selectbox("Existing subsets", options=existing_subset_names if existing_subset_names else ["<none>"], index=0)
    if selected_subset != "<none>":
        subset_summary = read_json_if_exists(SUBSETS_DIR / selected_subset / "_subset_summary.json")
        render_json_summary(f"{selected_subset}/_subset_summary.json", subset_summary)
        render_json_details_toggle("subset summary", subset_summary, "subset_summary_full")

with graph_tab:
    section_header("Build Graph", "Compact graph build UI.")
    subset_names = [p.name for p in list_subset_dirs()]
    selected_subset_name = st.selectbox("Choose subset", options=subset_names if subset_names else ["<none>"], index=0, key="graph_subset")
    graph_type = st.selectbox("Graph type", ["citation", "collaboration"])
    graph_name = st.text_input("Graph name", value=selected_subset_name if selected_subset_name != "<none>" else "graph")
    limit_value = st.number_input("Limit records (0 = no limit)", min_value=0, max_value=1000000, value=5000)
    overwrite_graph = st.checkbox("Overwrite graph outputs", value=False)

    if st.button("Build graph", width="stretch"):
        if selected_subset_name == "<none>":
            raise_ui_error("No subset available.")
        elif not graph_name.strip():
            raise_ui_error("Graph name cannot be empty.")
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
            if overwrite_graph:
                command.append("--overwrite")

            success, output = run_command(command, stage="build_graph", parameters={"subset": selected_subset_name}, outputs={"graph": f"{graph_name}_{graph_type}"})
            st.code(output)
            if success:
                st.success("Graph build completed.")
            else:
                st.error("Graph build failed.")

    graph_summary = read_json_if_exists(GRAPHS_DIR / f"{graph_name}_{graph_type}_summary.json")
    render_json_summary(f"{graph_name}_{graph_type}_summary.json", graph_summary)
    render_json_details_toggle("graph summary", graph_summary, "graph_summary_full")

with analyze_tab:
    section_header("Analyze Graph", "Compact analysis view.")
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

    st.code(f"Input graph: {graph_input.name}")
    st.code(f"Output analysis: {analysis_output.name}")

    if st.button("Run analysis", width="stretch"):
        if selected_base == "<none>":
            raise_ui_error("No graph available.")
        elif not graph_input.exists():
            raise_ui_error(f"Graph file not found: {graph_input}")
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
            success, output = run_command(command, stage="analyze_graph", parameters={"graph": graph_input.name}, outputs={"analysis": analysis_output.name})
            st.code(output)
            if success:
                st.success("Graph analysis completed.")
            else:
                st.error("Graph analysis failed.")

    analysis_data = read_json_if_exists(analysis_output)
    render_json_summary(analysis_output.name, analysis_data)
    render_json_details_toggle("analysis output", analysis_data, "analysis_output_full")

with insights_tab:
    section_header("Graph Insights Dashboard", "Only small tables by default.")
    analysis_bases = extract_analysis_base_names()
    selected_insight_base = st.selectbox("Choose analysis base name", options=analysis_bases if analysis_bases else ["<none>"], index=0)
    selected_insight_type = st.selectbox("Analysis graph type", ["citation", "collaboration"], key="insight_graph_type")

    if selected_insight_base != "<none>":
        analysis_path = METRICS_DIR / f"{selected_insight_base}_{selected_insight_type}_analysis.json"
        analysis = read_json_if_exists(analysis_path)
    else:
        analysis = None
        analysis_path = METRICS_DIR / "analysis.json"

    export_dir = EXPORTS_DIR / f"{selected_insight_base}_{selected_insight_type}" if selected_insight_base != "<none>" else EXPORTS_DIR / "analysis"

    if st.button("Export analysis CSV", width="stretch"):
        if selected_insight_base == "<none>":
            raise_ui_error("No analysis available.")
        else:
            command = [
                PYTHON_EXECUTABLE,
                "scripts/export_analysis_csv.py",
                "--input",
                str(analysis_path),
                "--output-dir",
                str(export_dir),
            ]
            success, output = run_command(command, stage="export_analysis_csv", parameters={"analysis": analysis_path.name}, outputs={"export_dir": str(export_dir)})
            st.code(output)
            if success:
                st.success("CSV export completed.")
            else:
                st.error("CSV export failed.")

    if isinstance(analysis, dict):
        summary = analysis.get("summary", {})
        communities = analysis.get("communities", {})
        pagerank = analysis.get("pagerank", [])
        degree = analysis.get("centralities", {}).get("degree", [])
        closeness = analysis.get("centralities", {}).get("closeness", [])
        betweenness = analysis.get("centralities", {}).get("betweenness", [])
        node_details_index = analysis.get("node_details_index", {})

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

        left, right = st.columns(2)
        with left:
            render_table_from_list("Top PageRank", pagerank, max_rows=10)
            render_table_from_list("Top Degree", degree, max_rows=10)
        with right:
            render_table_from_list("Top Closeness", closeness, max_rows=10)
            render_table_from_list("Top Betweenness", betweenness, max_rows=10)

        detail_options = []
        for section in [pagerank, degree, closeness, betweenness]:
            for row in section:
                display_name = row.get("display_name", row.get("node_id"))
                node_id = row.get("node_id")
                label = f"{display_name} | {node_id}"
                if label not in detail_options:
                    detail_options.append(label)

        if detail_options:
            selected_label = st.selectbox("Choose a ranked node", options=detail_options)
            selected_node_id = selected_label.split(" | ")[-1]
            selected_node_details = node_details_index.get(selected_node_id, {})
            render_json_summary("Node details", selected_node_details)
            render_json_details_toggle("node details", selected_node_details, "node_details_full")

with quality_tab:
    section_header("Data Quality Dashboard", "Compact quality reporting.")
    quality_input_mode = st.selectbox("Quality source", ["normalized", "subset", "sample"])
    top_n = st.number_input("Top N values", min_value=3, max_value=50, value=10, step=1)

    if quality_input_mode == "normalized":
        quality_input = NORMALIZED_DIR
        quality_default_name = "normalized_quality_report.json"
    elif quality_input_mode == "sample":
        sample_names = [p.name for p in list_sample_parquets()]
        selected_quality_sample = st.selectbox("Choose sample parquet", options=sample_names if sample_names else ["<none>"])
        quality_input = SAMPLE_DIR / selected_quality_sample if selected_quality_sample != "<none>" else Path("missing")
        quality_default_name = f"{selected_quality_sample.replace('.parquet', '')}_quality_report.json" if selected_quality_sample != "<none>" else "sample_quality_report.json"
    else:
        subset_names = [p.name for p in list_subset_dirs()]
        selected_quality_subset = st.selectbox("Choose subset", options=subset_names if subset_names else ["<none>"])
        quality_input = SUBSETS_DIR / selected_quality_subset / "data.parquet" if selected_quality_subset != "<none>" else Path("missing")
        quality_default_name = f"{selected_quality_subset}_quality_report.json" if selected_quality_subset != "<none>" else "subset_quality_report.json"

    quality_output = QUALITY_DIR / quality_default_name

    if st.button("Compute data quality report", width="stretch"):
        command = [
            PYTHON_EXECUTABLE,
            "scripts/compute_data_quality.py",
            "--input",
            str(quality_input),
            "--output",
            str(quality_output),
            "--top-n",
            str(top_n),
        ]
        success, output = run_command(command, stage="compute_data_quality", parameters={"input": str(quality_input)}, outputs={"output": str(quality_output)})
        st.code(output)
        if success:
            st.success("Data quality report completed.")
        else:
            st.error("Data quality report failed.")

    quality_report = read_json_if_exists(quality_output)
    if isinstance(quality_report, dict):
        summary = quality_report.get("summary", {})
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Rows", str(summary.get("row_count", "")), "Total records")
        with c2:
            metric_card("Year range", f"{summary.get('min_year', '')} â†’ {summary.get('max_year', '')}", "Observed years")
        with c3:
            metric_card("Missing title", f"{round(summary.get('missing_title_ratio', 0) * 100, 2)}%", "Empty or null titles")
        with c4:
            metric_card("Zero authors", f"{round(summary.get('zero_author_ratio', 0) * 100, 2)}%", "author_count = 0")

        render_table_from_list("Top years", quality_report.get("top_years", []), max_rows=10)
        render_table_from_list("Top FOS", quality_report.get("top_fos", []), max_rows=10)

with history_tab:
    section_header("Pipeline Run History", "Compact history viewer.")
    runs = read_pipeline_runs(MANIFEST_PATH)

    if runs:
        runs_df = pd.DataFrame(runs[::-1][:30])
        st.dataframe(runs_df, width="stretch", height=420)
        selected_index = st.number_input("Run index from latest (0 = latest)", min_value=0, max_value=max(len(runs) - 1, 0), value=0, step=1)
        selected_run = runs[::-1][selected_index]
        render_json_summary("Selected run", selected_run)
        render_json_details_toggle("selected run", selected_run, "run_details_full")
    else:
        st.info("No pipeline runs logged yet.")

with artifacts_tab:
    section_header("Artifacts Explorer", "Lightweight file browser.")
    c1, c2 = st.columns(2)
    with c1:
        render_files_list("Sample files", list_relative_files(SAMPLE_DIR, limit=30))
        render_files_list("Graph files", list_relative_files(GRAPHS_DIR, limit=30))
    with c2:
        render_files_list("Metric files", list_relative_files(METRICS_DIR, limit=30))
        render_files_list("Quality files", list_relative_files(QUALITY_DIR, limit=30))
