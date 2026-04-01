from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXECUTABLE = sys.executable

RAW_DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "dblpv13.json"
INSPECTION_DIR = PROJECT_ROOT / "outputs" / "inspection"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "interim" / "normalized"
SUBSETS_DIR = PROJECT_ROOT / "data" / "processed" / "subsets"
GRAPHS_DIR = PROJECT_ROOT / "outputs" / "graphs"
METRICS_DIR = PROJECT_ROOT / "outputs" / "metrics"


def run_command(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout or "Command completed successfully."
    except subprocess.CalledProcessError as exc:
        error_output = exc.stdout + "\n" + exc.stderr
        return False, error_output.strip()


def read_json_if_exists(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_files(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    return sorted(str(path.relative_to(PROJECT_ROOT)) for path in directory.rglob("*") if path.is_file())


st.set_page_config(
    page_title="Citation Graph Pipeline",
    layout="wide",
)

st.title("Citation & Collaboration Graph Pipeline")
st.caption("Local orchestration interface for AMiner DBLP-Citation-network V13 processing")

tab_overview, tab_inspection, tab_normalization, tab_filtering, tab_graphs, tab_analysis, tab_artifacts = st.tabs(
    [
        "Overview",
        "Inspect Raw",
        "Normalize",
        "Filter Subset",
        "Build Graph",
        "Analyze Graph",
        "Artifacts",
    ]
)

with tab_overview:
    st.subheader("Pipeline Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("### 1. Raw")
        st.write(f"Dataset: `{RAW_DATASET_PATH}`")
        st.write("Exists:", RAW_DATASET_PATH.exists())

    with col2:
        st.markdown("### 2. Inspection")
        st.write("Profile exists:", (INSPECTION_DIR / "raw_profile.json").exists())
        st.write("Samples exist:", (INSPECTION_DIR / "raw_samples.json").exists())

    with col3:
        st.markdown("### 3. Normalization")
        st.write("Normalized dir exists:", NORMALIZED_DIR.exists())
        st.write("Summary exists:", (NORMALIZED_DIR / "_normalization_summary.json").exists())

    with col4:
        st.markdown("### 4. Subsets")
        st.write("Subset root exists:", SUBSETS_DIR.exists())
        if SUBSETS_DIR.exists():
            st.write("Subset directories:", len([p for p in SUBSETS_DIR.iterdir() if p.is_dir()]))

    with col5:
        st.markdown("### 5. Graph / Metrics")
        st.write("Graphs dir exists:", GRAPHS_DIR.exists())
        st.write("Metrics dir exists:", METRICS_DIR.exists())

    st.markdown("---")
    st.write("This V1 interface is designed to pilot the pipeline step by step before adding richer visual controls.")

with tab_inspection:
    st.subheader("Inspect Raw Dataset")

    max_records = st.number_input("Sample record count", min_value=1, max_value=20, value=3)

    if st.button("Run raw inspection"):
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

    profile = read_json_if_exists(INSPECTION_DIR / "raw_profile.json")
    samples = read_json_if_exists(INSPECTION_DIR / "raw_samples.json")

    st.markdown("### raw_profile.json")
    if profile is not None:
        st.json(profile)
    else:
        st.info("No inspection profile found yet.")

    st.markdown("### raw_samples.json")
    if samples is not None:
        st.json(samples)
    else:
        st.info("No inspection samples found yet.")

with tab_normalization:
    st.subheader("Normalize Raw Dataset to Parquet")

    batch_size = st.number_input("Batch size", min_value=1000, max_value=50000, value=10000, step=1000)
    min_year = st.number_input("Minimum valid year", min_value=0, max_value=3000, value=1800)
    max_year = st.number_input("Maximum valid year", min_value=0, max_value=3000, value=2026)
    overwrite = st.checkbox("Overwrite output directory", value=False)

    if st.button("Run normalization"):
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

    normalization_summary = read_json_if_exists(NORMALIZED_DIR / "_normalization_summary.json")
    st.markdown("### _normalization_summary.json")
    if normalization_summary is not None:
        st.json(normalization_summary)
    else:
        st.info("No normalization summary found yet.")

with tab_filtering:
    st.subheader("Create Filtered Subset")

    mode = st.selectbox("Filter mode", ["year", "range", "fos", "year_fos"])
    subset_name = st.text_input("Subset name", value="year_2020")
    year = st.number_input("Year", min_value=1800, max_value=2026, value=2020)
    start_year = st.number_input("Start year", min_value=1800, max_value=2026, value=2018)
    end_year = st.number_input("End year", min_value=1800, max_value=2026, value=2021)
    fos = st.text_input("Field of Study contains", value="Data Science")
    overwrite_subset = st.checkbox("Overwrite subset", value=False)

    if st.button("Create subset"):
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

        if mode in ("year", "year_fos"):
            command.extend(["--year", str(year)])

        if mode == "range":
            command.extend(["--start-year", str(start_year), "--end-year", str(end_year)])

        if mode in ("fos", "year_fos"):
            command.extend(["--fos", fos])

        if overwrite_subset:
            command.append("--overwrite")

        success, output = run_command(command)
        st.code(output)
        if success:
            st.success("Subset creation completed.")
        else:
            st.error("Subset creation failed.")

    selected_summary_path = SUBSETS_DIR / subset_name / "_subset_summary.json"
    subset_summary = read_json_if_exists(selected_summary_path)

    st.markdown("### Selected subset summary")
    if subset_summary is not None:
        st.json(subset_summary)
    else:
        st.info("No subset summary found for the current subset name.")

with tab_graphs:
    st.subheader("Build Graph")

    subset_parquet = st.text_input(
        "Subset parquet path",
        value=str(SUBSETS_DIR / "year_2020" / "data.parquet"),
    )
    graph_type = st.selectbox("Graph type", ["citation", "collaboration"])
    graph_name = st.text_input("Graph name", value="year_2020")
    limit_value = st.number_input("Limit records (0 = no limit)", min_value=0, max_value=1000000, value=5000)

    if st.button("Build graph"):
        command = [
            PYTHON_EXECUTABLE,
            "scripts/build_graph.py",
            "--input",
            subset_parquet,
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

    graph_summary_path = GRAPHS_DIR / f"{graph_name}_{graph_type}_summary.json"
    graph_summary = read_json_if_exists(graph_summary_path)

    st.markdown("### Selected graph summary")
    if graph_summary is not None:
        st.json(graph_summary)
    else:
        st.info("No graph summary found for the selected graph.")

with tab_analysis:
    st.subheader("Analyze Graph")

    graph_input = st.text_input(
        "Graph GEXF input",
        value=str(GRAPHS_DIR / "year_2020_citation.gexf"),
    )
    analysis_output = st.text_input(
        "Analysis output JSON",
        value=str(METRICS_DIR / "year_2020_citation_analysis.json"),
    )
    top_n = st.number_input("Top N", min_value=1, max_value=100, value=10)
    exact_betweenness = st.checkbox("Exact betweenness (slow)", value=False)
    betweenness_sample_k = st.number_input("Betweenness sample k", min_value=10, max_value=5000, value=200)

    if st.button("Run analysis"):
        command = [
            PYTHON_EXECUTABLE,
            "scripts/analyze_graph.py",
            "--input",
            graph_input,
            "--output",
            analysis_output,
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

    analysis_json = read_json_if_exists(Path(analysis_output))
    st.markdown("### Analysis result")
    if analysis_json is not None:
        st.json(analysis_json)
    else:
        st.info("No analysis result found for the selected output path.")

with tab_artifacts:
    st.subheader("Artifacts")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Graph files")
        graph_files = list_files(GRAPHS_DIR)
        if graph_files:
            st.code("\n".join(graph_files))
        else:
            st.info("No graph files found.")

    with col2:
        st.markdown("### Metric files")
        metric_files = list_files(METRICS_DIR)
        if metric_files:
            st.code("\n".join(metric_files))
        else:
            st.info("No metric files found.")

    st.markdown("### Subset files")
    subset_files = list_files(SUBSETS_DIR)
    if subset_files:
        st.code("\n".join(subset_files[:200]))
    else:
        st.info("No subset files found.")
