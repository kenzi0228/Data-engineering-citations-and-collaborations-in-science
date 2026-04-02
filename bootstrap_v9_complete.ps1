$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path "src\citation_graphs" | Out-Null
New-Item -ItemType Directory -Force -Path "scripts" | Out-Null
New-Item -ItemType Directory -Force -Path "tests\fixtures" | Out-Null
New-Item -ItemType Directory -Force -Path "outputs\reports" | Out-Null
New-Item -ItemType Directory -Force -Path "app" | Out-Null

@'
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
    lines.append(f"# Graph Analysis Report — {analysis_name}")
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
'@ | Set-Content "src\citation_graphs\reporting.py" -Encoding UTF8

@'
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.reporting import export_analysis_markdown_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a graph analysis JSON file to a Markdown report.")
    parser.add_argument("--input", required=True, help="Input analysis JSON path")
    parser.add_argument("--output", required=True, help="Output Markdown report path")
    parser.add_argument("--name", help="Optional custom analysis display name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = export_analysis_markdown_report(
        analysis_path=args.input,
        output_path=args.output,
        analysis_name=args.name,
    )
    print("Analysis report export completed.")
    print(result)


if __name__ == "__main__":
    main()
'@ | Set-Content "scripts\export_analysis_report.py" -Encoding UTF8

@'
[
  {
    "paper_id": "paper_1",
    "title": "Graph Analytics for Science",
    "year_clean": 2020,
    "n_citation": 12,
    "lang": "en",
    "venue_name": "Journal A",
    "fos": ["Data Science", "Graph Theory"],
    "fos_count": 2,
    "references": ["paper_2"],
    "reference_count": 1,
    "author_ids": ["author_1", "author_2"],
    "author_names": ["Alice Doe", "Bob Ray"],
    "author_count": 2
  },
  {
    "paper_id": "paper_2",
    "title": "Network Methods in Research",
    "year_clean": 2019,
    "n_citation": 8,
    "lang": "en",
    "venue_name": "Conference B",
    "fos": ["Network Science"],
    "fos_count": 1,
    "references": [],
    "reference_count": 0,
    "author_ids": ["author_2"],
    "author_names": ["Bob Ray"],
    "author_count": 1
  },
  {
    "paper_id": "paper_3",
    "title": "Applied Collaboration Networks",
    "year_clean": 2020,
    "n_citation": 5,
    "lang": "en",
    "venue_name": "Workshop C",
    "fos": ["Data Science"],
    "fos_count": 1,
    "references": ["paper_1"],
    "reference_count": 1,
    "author_ids": ["author_1", "author_3"],
    "author_names": ["Alice Doe", "Charlie Lin"],
    "author_count": 2
  }
]
'@ | Set-Content "tests\fixtures\mini_records.json" -Encoding UTF8

@'
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mini_records(fixture_dir: Path) -> list[dict]:
    return json.loads((fixture_dir / "mini_records.json").read_text(encoding="utf-8"))


@pytest.fixture
def mini_parquet(tmp_path: Path, mini_records: list[dict]) -> Path:
    json_path = tmp_path / "mini_records.json"
    json_path.write_text(json.dumps(mini_records), encoding="utf-8")

    parquet_path = tmp_path / "mini_subset.parquet"
    con = duckdb.connect(database=":memory:")
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM read_json_auto('{json_path}')
        )
        TO '{parquet_path}'
        (FORMAT PARQUET)
        """
    )
    con.close()
    return parquet_path
'@ | Set-Content "tests\conftest.py" -Encoding UTF8

@'
from __future__ import annotations

import duckdb

from citation_graphs.filtering import build_where_clause


def test_build_where_clause_year() -> None:
    clause = build_where_clause(mode="year", year=2020)
    assert clause == "year_clean = 2020"


def test_build_where_clause_range() -> None:
    clause = build_where_clause(mode="range", start_year=2018, end_year=2020)
    assert clause == "year_clean BETWEEN 2018 AND 2020"


def test_build_where_clause_fos() -> None:
    clause = build_where_clause(mode="fos", fos_values=["Data Science", "Graph Theory"])
    assert "lower(f) = 'data science'" in clause
    assert "lower(f) = 'graph theory'" in clause


def test_filter_query_on_fixture(mini_parquet) -> None:
    con = duckdb.connect(database=":memory:")
    rows = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{mini_parquet}')
        WHERE year_clean = 2020
        """
    ).fetchone()[0]
    con.close()

    assert rows == 2
'@ | Set-Content "tests\test_filtering.py" -Encoding UTF8

@'
from __future__ import annotations

from citation_graphs.graph_builder import build_citation_graph, build_collaboration_graph


def test_build_citation_graph(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    assert graph.number_of_nodes() >= 3
    assert graph.number_of_edges() >= 2


def test_build_collaboration_graph(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() >= 2


def test_citation_graph_has_title_label(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    assert graph.nodes["paper_1"]["title"] == "Graph Analytics for Science"
    assert graph.nodes["paper_1"]["display_name"] == "Graph Analytics for Science"


def test_collaboration_graph_has_name_label(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    assert graph.nodes["author_1"]["name"] == "Alice Doe"
    assert graph.nodes["author_1"]["display_name"] == "Alice Doe"
'@ | Set-Content "tests\test_graph_builder.py" -Encoding UTF8

@'
from __future__ import annotations

from citation_graphs.graph_analysis import analyze_graph
from citation_graphs.graph_builder import build_citation_graph, build_collaboration_graph


def test_analyze_citation_graph_structure(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)

    assert "summary" in result
    assert "centralities" in result
    assert "pagerank" in result
    assert "communities" in result
    assert "node_details_index" in result


def test_analyze_collaboration_graph_structure(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)

    assert isinstance(result["pagerank"], list)
    assert isinstance(result["centralities"]["degree"], list)
    assert isinstance(result["communities"]["largest_communities"], list)


def test_display_name_priority_for_citation(mini_records) -> None:
    graph = build_citation_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)
    details = result["node_details_index"]["paper_1"]
    assert details["display_name"] == "Graph Analytics for Science"


def test_display_name_priority_for_collaboration(mini_records) -> None:
    graph = build_collaboration_graph(mini_records)
    result = analyze_graph(graph, top_n=5, betweenness_sample_k=10)
    details = result["node_details_index"]["author_1"]
    assert details["display_name"] == "Alice Doe"
'@ | Set-Content "tests\test_graph_analysis.py" -Encoding UTF8

@'
from __future__ import annotations

from citation_graphs.data_quality import compute_data_quality_report


def test_data_quality_report_structure(mini_parquet) -> None:
    report = compute_data_quality_report(mini_parquet, top_n=5)

    assert "summary" in report
    assert "top_years" in report
    assert "top_fos" in report

    summary = report["summary"]
    assert summary["row_count"] == 3
    assert summary["min_year"] == 2019
    assert summary["max_year"] == 2020
'@ | Set-Content "tests\test_data_quality.py" -Encoding UTF8

@'
from __future__ import annotations

import json
from pathlib import Path

from citation_graphs.reporting import build_analysis_markdown_report, export_analysis_markdown_report


def test_build_analysis_markdown_report() -> None:
    analysis = {
        "summary": {"num_nodes": 10, "num_edges": 12, "density": 0.1},
        "centralities": {"degree": [], "closeness": [], "betweenness": []},
        "pagerank": [],
        "communities": {"num_communities": 2, "largest_communities": []},
    }
    markdown = build_analysis_markdown_report("demo_analysis", analysis)
    assert "# Graph Analysis Report — demo_analysis" in markdown
    assert "## Executive Summary" in markdown


def test_export_analysis_markdown_report(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(
        json.dumps(
            {
                "summary": {"num_nodes": 10, "num_edges": 12, "density": 0.1},
                "centralities": {"degree": [], "closeness": [], "betweenness": []},
                "pagerank": [],
                "communities": {"num_communities": 2, "largest_communities": []},
            }
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "report.md"
    result = export_analysis_markdown_report(analysis_path, output_path)

    assert output_path.exists()
    assert result["report_path"].endswith("report.md")
'@ | Set-Content "tests\test_reporting.py" -Encoding UTF8

@'
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
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
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


def read_text_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
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


def comparison_dataframe(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]], label_a: str, label_b: str, top_n: int = 10) -> pd.DataFrame:
    a = pd.DataFrame(rows_a[:top_n]).copy()
    b = pd.DataFrame(rows_b[:top_n]).copy()

    for df in (a, b):
        if "details" in df.columns:
            df.drop(columns=["details"], inplace=True)

    a = a.rename(columns={"score": f"score_{label_a}", "display_name": f"display_name_{label_a}"})
    b = b.rename(columns={"score": f"score_{label_b}", "display_name": f"display_name_{label_b}"})

    if "node_id" not in a.columns:
        a["node_id"] = ""
    if "node_id" not in b.columns:
        b["node_id"] = ""

    return pd.merge(a, b, on="node_id", how="outer")


st.set_page_config(
    page_title="Citation & Collaboration Graph Pipeline",
    page_icon="📊",
    layout="wide",
)

st.title("Citation & Collaboration Graph Pipeline")
st.caption("Quick Start: 1) inspect raw data, 2) normalize, 3) create a subset, 4) build a graph, 5) run analysis, 6) explore insights, comparisons, quality and reports.")

overview_tab, demo_tab, inspect_tab, normalize_tab, filter_tab, graph_tab, analyze_tab, insights_tab, compare_tab, quality_tab, history_tab, artifacts_tab = st.tabs(
    [
        "Overview",
        "Demo",
        "Inspect Raw",
        "Normalize",
        "Filter Subset",
        "Build Graph",
        "Analyze Graph",
        "Insights",
        "Compare",
        "Data Quality",
        "Run History",
        "Artifacts",
    ]
)

with overview_tab:
    section_header("Workspace Overview", "Project health, available assets, and recommended entry points.")
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
        metric_card("Reports", str(len(list_relative_files(REPORTS_DIR, suffix=".md", limit=200))), "Markdown reports")
    with c6:
        metric_card("Tests", "Ready", "Run pytest from terminal")

    st.markdown("### Recommended Usage")
    st.markdown(
        """
        1. Start with **Inspect Raw** to verify the raw dataset structure.  
        2. Use **Normalize** to create partitioned parquet outputs.  
        3. Create a focused subset in **Filter Subset**.  
        4. Build citation or collaboration graphs in **Build Graph**.  
        5. Run analytics in **Analyze Graph**.  
        6. Explore results in **Insights**, **Compare**, **Data Quality**, and export a report.
        """
    )

with demo_tab:
    section_header("Demo Workflow", "Use an existing sample or create a small one, then build and analyze it.")
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

with inspect_tab:
    section_header("Inspect Raw Dataset", "Sample the source file safely and inspect its structure.")
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
    section_header("Normalize Dataset", "Convert the raw source into normalized partitioned parquet.")
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
    section_header("Create Filtered Subset", "Create subsets by year, year range, FOS, or year + FOS.")
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
    section_header("Build Graph", "Create citation or collaboration graphs from existing subsets.")
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
    section_header("Analyze Graph", "Run graph analytics and generate reusable analysis outputs.")
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
    section_header("Graph Insights Dashboard", "Inspect rankings, node details, exports, and markdown reports.")
    analysis_bases = extract_analysis_base_names()
    selected_insight_base = st.selectbox("Choose analysis base name", options=analysis_bases if analysis_bases else ["<none>"], index=0)
    selected_insight_type = st.selectbox("Analysis graph type", ["citation", "collaboration"], key="insight_graph_type")

    if selected_insight_base != "<none>":
        analysis_path = METRICS_DIR / f"{selected_insight_base}_{selected_insight_type}_analysis.json"
        analysis = read_json_if_exists(analysis_path)
        report_path = REPORTS_DIR / f"{selected_insight_base}_{selected_insight_type}_report.md"
    else:
        analysis = None
        analysis_path = METRICS_DIR / "analysis.json"
        report_path = REPORTS_DIR / "analysis_report.md"

    export_dir = EXPORTS_DIR / f"{selected_insight_base}_{selected_insight_type}" if selected_insight_base != "<none>" else EXPORTS_DIR / "analysis"

    action_col1, action_col2 = st.columns(2)

    with action_col1:
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

    with action_col2:
        if st.button("Export markdown report", width="stretch"):
            if selected_insight_base == "<none>":
                raise_ui_error("No analysis available.")
            else:
                command = [
                    PYTHON_EXECUTABLE,
                    "scripts/export_analysis_report.py",
                    "--input",
                    str(analysis_path),
                    "--output",
                    str(report_path),
                    "--name",
                    f"{selected_insight_base}_{selected_insight_type}",
                ]
                success, output = run_command(command, stage="export_analysis_report", parameters={"analysis": analysis_path.name}, outputs={"report": str(report_path)})
                st.code(output)
                if success:
                    st.success("Markdown report exported.")
                else:
                    st.error("Markdown report export failed.")

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

        report_text = read_text_if_exists(report_path)
        if report_text:
            st.markdown("### Latest Markdown Report")
            st.text_area("Report preview", report_text[:5000], height=300)

with compare_tab:
    section_header("Graph Comparison Dashboard", "Compare two analysis outputs side by side.")
    analysis_bases = extract_analysis_base_names()
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### Analysis A")
        base_a = st.selectbox("Base name A", options=analysis_bases if analysis_bases else ["<none>"], key="base_a")
        type_a = st.selectbox("Type A", ["citation", "collaboration"], key="type_a")

    with col_b:
        st.markdown("### Analysis B")
        base_b = st.selectbox("Base name B", options=analysis_bases if analysis_bases else ["<none>"], key="base_b")
        type_b = st.selectbox("Type B", ["citation", "collaboration"], key="type_b")

    analysis_a = read_json_if_exists(METRICS_DIR / f"{base_a}_{type_a}_analysis.json") if base_a != "<none>" else None
    analysis_b = read_json_if_exists(METRICS_DIR / f"{base_b}_{type_b}_analysis.json") if base_b != "<none>" else None

    if isinstance(analysis_a, dict) and isinstance(analysis_b, dict):
        summary_a = analysis_a.get("summary", {})
        summary_b = analysis_b.get("summary", {})

        metrics = [
            ("Nodes", summary_a.get("num_nodes", ""), summary_b.get("num_nodes", "")),
            ("Edges", summary_a.get("num_edges", ""), summary_b.get("num_edges", "")),
            ("Density", summary_a.get("density", ""), summary_b.get("density", "")),
            ("Diameter", summary_a.get("largest_component_diameter", ""), summary_b.get("largest_component_diameter", "")),
            ("Communities", analysis_a.get("communities", {}).get("num_communities", ""), analysis_b.get("communities", {}).get("num_communities", "")),
        ]

        st.markdown("### KPI Comparison")
        compare_rows = [{"metric": m, "A": a, "B": b} for m, a, b in metrics]
        st.dataframe(pd.DataFrame(compare_rows), width="stretch")

        st.markdown("### PageRank Comparison")
        pagerank_compare = comparison_dataframe(
            analysis_a.get("pagerank", []),
            analysis_b.get("pagerank", []),
            "A",
            "B",
            top_n=10,
        )
        st.dataframe(pagerank_compare, width="stretch", height=420)

        st.markdown("### Degree Comparison")
        degree_compare = comparison_dataframe(
            analysis_a.get("centralities", {}).get("degree", []),
            analysis_b.get("centralities", {}).get("degree", []),
            "A",
            "B",
            top_n=10,
        )
        st.dataframe(degree_compare, width="stretch", height=420)

with quality_tab:
    section_header("Data Quality Dashboard", "Profile normalized data, subsets, or samples.")
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
            metric_card("Year range", f"{summary.get('min_year', '')} - {summary.get('max_year', '')}", "Observed years")
        with c3:
            metric_card("Missing title", f"{round(summary.get('missing_title_ratio', 0) * 100, 2)}%", "Empty or null titles")
        with c4:
            metric_card("Zero authors", f"{round(summary.get('zero_author_ratio', 0) * 100, 2)}%", "author_count = 0")

        render_table_from_list("Top years", quality_report.get("top_years", []), max_rows=10)
        render_table_from_list("Top FOS", quality_report.get("top_fos", []), max_rows=10)

with history_tab:
    section_header("Pipeline Run History", "Review recent pipeline executions.")
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
    section_header("Artifacts Explorer", "Browse generated files across the project.")
    c1, c2 = st.columns(2)
    with c1:
        render_files_list("Sample files", list_relative_files(SAMPLE_DIR, limit=30))
        render_files_list("Graph files", list_relative_files(GRAPHS_DIR, limit=30))
        render_files_list("Report files", list_relative_files(REPORTS_DIR, suffix=".md", limit=30))
    with c2:
        render_files_list("Metric files", list_relative_files(METRICS_DIR, limit=30))
        render_files_list("Quality files", list_relative_files(QUALITY_DIR, limit=30))
'@ | Set-Content "app\streamlit_app.py" -Encoding UTF8

Write-Host "V9 bootstrap completed."
Write-Host "Created:"
Write-Host " - src\citation_graphs\reporting.py"
Write-Host " - scripts\export_analysis_report.py"
Write-Host " - tests\conftest.py"
Write-Host " - tests\fixtures\mini_records.json"
Write-Host " - tests\test_filtering.py"
Write-Host " - tests\test_graph_builder.py"
Write-Host " - tests\test_graph_analysis.py"
Write-Host " - tests\test_data_quality.py"
Write-Host " - tests\test_reporting.py"
Write-Host "Updated:"
Write-Host " - app\streamlit_app.py"