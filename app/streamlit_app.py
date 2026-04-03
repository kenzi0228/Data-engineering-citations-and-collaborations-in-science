from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.author_index import load_author_index, suggest_authors
from citation_graphs.author_profile import build_author_profile
from citation_graphs.fos_index import load_fos_index
from citation_graphs.manifests import append_pipeline_run, read_pipeline_runs
from citation_graphs.path_finder import investigate_path_between_nodes, load_graph
from citation_graphs.publication_profile import build_publication_profile
from citation_graphs.publication_search import export_publication_results_csv, search_publication_records
from citation_graphs.search import export_search_results_csv, search_author_records, search_author_records_multi, slugify

PYTHON_EXECUTABLE = sys.executable

RAW_DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "dblpv13.json"
INSPECTION_DIR = PROJECT_ROOT / "outputs" / "inspection"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "interim" / "normalized"
SUBSETS_DIR = PROJECT_ROOT / "data" / "processed" / "subsets"
GRAPHS_DIR = PROJECT_ROOT / "outputs" / "graphs"
METRICS_DIR = PROJECT_ROOT / "outputs" / "metrics"
EXPORTS_DIR = PROJECT_ROOT / "outputs" / "exports"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
SEARCH_DIR = PROJECT_ROOT / "outputs" / "search"
FOS_INDEX_PATH = PROJECT_ROOT / "data" / "reference" / "fos_index.json"
AUTHOR_INDEX_NORMALIZED_PATH = PROJECT_ROOT / "data" / "reference" / "author_index_normalized.json"
AUTHOR_INDEX_SAMPLE_PATH = PROJECT_ROOT / "data" / "reference" / "author_index_sample.json"
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
MANIFEST_PATH = PROJECT_ROOT / "outputs" / "manifests" / "pipeline_runs.jsonl"
QUALITY_DIR = PROJECT_ROOT / "outputs" / "quality"


def run_command(command: list[str], stage: str, parameters: dict[str, Any] | None = None, outputs: dict[str, Any] | None = None) -> tuple[bool, str]:
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        elapsed = round(time.perf_counter() - started, 4)
        message = (result.stdout or "Command completed successfully.").strip()
        append_pipeline_run(
            MANIFEST_PATH,
            stage=stage,
            status="success",
            parameters=parameters,
            outputs=outputs,
            message=f"[{elapsed}s]\n{message}",
        )
        return True, f"[{elapsed}s]\n{message}"
    except subprocess.CalledProcessError as exc:
        elapsed = round(time.perf_counter() - started, 4)
        output = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        append_pipeline_run(
            MANIFEST_PATH,
            stage=stage,
            status="failed",
            parameters=parameters,
            outputs=outputs,
            message=f"[{elapsed}s]\n{output}",
        )
        return False, f"[{elapsed}s]\n{output or 'Command failed with no output.'}"


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
def load_graph_node_catalog(graph_path_str: str) -> list[dict[str, str]]:
    graph = load_graph(graph_path_str)
    rows = []
    for node_id, attrs in graph.nodes(data=True):
        display_name = (
            attrs.get("display_name")
            or attrs.get("title")
            or attrs.get("name")
            or attrs.get("label")
            or str(node_id)
        )
        rows.append(
            {
                "node_id": str(node_id),
                "display_name": str(display_name),
                "node_type": str(attrs.get("node_type") or ""),
            }
        )
    rows.sort(key=lambda x: x["display_name"].lower())
    return rows


def filter_node_catalog(rows: list[dict[str, str]], query: str, limit: int = 50) -> list[dict[str, str]]:
    query = (query or "").strip().lower()
    if not query:
        return rows[:limit]

    starts = [row for row in rows if row["display_name"].lower().startswith(query)]
    contains = [row for row in rows if query in row["display_name"].lower() and row not in starts]
    return (starts + contains)[:limit]


def merge_selected_with_suggestions(selected: list[str], suggestions: list[str]) -> list[str]:
    merged = []
    seen = set()
    for name in (selected or []) + (suggestions or []):
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        merged.append(name)
    return merged


def render_readable_paths(paths: list[list[dict[str, str]]], title: str) -> None:
    st.markdown(f"#### {title}")
    if not paths:
        st.info("No paths available.")
        return

    for idx, path in enumerate(paths, start=1):
        labels = [step.get("display_name", step.get("node_id", "")) for step in path]
        st.markdown(f"**Path {idx}**")
        st.code(" -> ".join(labels))


def readable_path_to_dataframe(path: list[dict[str, str]]) -> pd.DataFrame:
    rows = []
    for idx, step in enumerate(path, start=1):
        rows.append(
            {
                "order": idx,
                "display_name": step.get("display_name"),
                "node_type": step.get("node_type"),
                "node_id": step.get("node_id"),
            }
        )
    return pd.DataFrame(rows)


def render_readable_paths_table(paths: list[list[dict[str, str]]], title: str) -> None:
    st.markdown(f"#### {title}")
    if not paths:
        st.info("No paths available.")
        return

    for idx, path in enumerate(paths, start=1):
        with st.expander(f"Path {idx} ({len(path)} node(s))", expanded=(idx == 1)):
            labels = [step.get("display_name", step.get("node_id", "")) for step in path]
            st.code(" -> ".join(labels))
            st.dataframe(readable_path_to_dataframe(path), width="stretch", height=min(420, 80 + 35 * len(path)))


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


def resolve_search_source(source_mode: str, selected_subset: str | None, selected_sample: str | None) -> Path | None:
    if source_mode == "normalized":
        return NORMALIZED_DIR if NORMALIZED_DIR.exists() else None
    if source_mode == "subset":
        if selected_subset and selected_subset != "<none>":
            subset_path = SUBSETS_DIR / selected_subset / "data.parquet"
            return subset_path if subset_path.exists() else None
        return None
    if source_mode == "sample":
        if selected_sample and selected_sample != "<none>":
            sample_path = SAMPLE_DIR / selected_sample
            return sample_path if sample_path.exists() else None
        return None
    return None


def build_search_results_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    prepared = []
    for row in rows:
        prepared.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year_clean": row.get("year_clean"),
                "venue_name": row.get("venue_name"),
                "author_names": " | ".join(str(x) for x in row.get("author_names", [])),
                "fos": " | ".join(str(x) for x in row.get("fos", [])),
                "n_citation": row.get("n_citation"),
            }
        )
    return pd.DataFrame(prepared)


def build_publication_results_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    prepared = []
    for row in rows:
        prepared.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year_clean": row.get("year_clean"),
                "venue_name": row.get("venue_name"),
                "author_names": " | ".join(str(x) for x in row.get("author_names", [])),
                "fos": " | ".join(str(x) for x in row.get("fos", [])),
                "reference_count": row.get("reference_count"),
                "n_citation": row.get("n_citation"),
            }
        )
    return pd.DataFrame(prepared)


st.set_page_config(
    page_title="Citation & Collaboration Graph Pipeline",
    page_icon="ðŸ“Š",
    layout="wide",
)

if "search_rows" not in st.session_state:
    st.session_state["search_rows"] = []
if "search_profile" not in st.session_state:
    st.session_state["search_profile"] = None
if "search_author_query" not in st.session_state:
    st.session_state["search_author_query"] = ""
if "search_selected_authors" not in st.session_state:
    st.session_state["search_selected_authors"] = []
if "search_selected_authors_input" not in st.session_state:
    st.session_state["search_selected_authors_input"] = []
if "path_source_label" not in st.session_state:
    st.session_state["path_source_label"] = "<none>"
if "path_target_label" not in st.session_state:
    st.session_state["path_target_label"] = "<none>"
if "path_finder_result" not in st.session_state:
    st.session_state["path_finder_result"] = None
if "publication_rows" not in st.session_state:
    st.session_state["publication_rows"] = []
if "publication_profile" not in st.session_state:
    st.session_state["publication_profile"] = None
if "publication_title_query" not in st.session_state:
    st.session_state["publication_title_query"] = ""
if "insights_base_name" not in st.session_state:
    st.session_state["insights_base_name"] = None
if "insights_graph_type" not in st.session_state:
    st.session_state["insights_graph_type"] = "collaboration"

st.title("Citation & Collaboration Graph Pipeline")
st.caption("Quick Start: 1) inspect raw data, 2) normalize, 3) create a subset, 4) build a graph, 5) run analysis, 6) explore insights, comparisons, quality and reports.")

overview_tab, search_tab, publication_tab, demo_tab, inspect_tab, normalize_tab, filter_tab, graph_tab, analyze_tab, insights_tab, compare_tab, path_tab, quality_tab, history_tab, artifacts_tab = st.tabs(
    [
        "Overview",
        "Search",
        "Publication Search",
        "Demo",
        "Inspect Raw",
        "Normalize",
        "Filter Subset",
        "Build Graph",
        "Analyze Graph",
        "Insights",
        "Compare",
        "Path Finder",
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
        metric_card("Tests", "Ready", "Core suite green")

    st.markdown("### Recommended Usage")
    st.markdown(
        """
        1. Start with **Search** or **Inspect Raw**.  
        2. Use **Normalize** to create partitioned parquet outputs.  
        3. Create a focused subset in **Filter Subset** or directly from **Search**.  
        4. Build citation or collaboration graphs.  
        5. Run analytics and export reports.  
        6. Explore results in **Insights**, **Compare**, and **Data Quality**.
        """
    )

with search_tab:
    section_header("Author Investigation", "Search one or several authors, use exact indexed suggestions, and build subset or ego-graph artifacts.")
    st.info("Quick guide: choose a source, type at least 2 characters to search indexed authors, optionally enable a year filter for faster searches on normalized data, then run the search.")

    source_col, mode_col, limit_col = st.columns([1.0, 1.0, 0.8])

    with source_col:
        source_mode = st.selectbox("Source", ["normalized", "subset", "sample"], key="search_source_mode")

    with mode_col:
        match_mode = st.selectbox("Match mode", ["or", "and"], key="search_match_mode")

    with limit_col:
        search_limit = st.number_input("Result row limit", min_value=1, max_value=5000, value=200, step=50, key="search_limit")

    enable_year_filter = st.checkbox("Filter by year range", value=False, key="search_enable_year_filter")
    year_col1, year_col2 = st.columns(2)
    with year_col1:
        start_year = st.number_input("Start year", min_value=1800, max_value=2026, value=2018, step=1, key="search_start_year")
    with year_col2:
        end_year = st.number_input("End year", min_value=1800, max_value=2026, value=2022, step=1, key="search_end_year")

    selected_subset = None
    selected_sample = None

    if source_mode == "subset":
        subset_names = [p.name for p in list_subset_dirs()]
        selected_subset = st.selectbox("Subset source", options=subset_names if subset_names else ["<none>"], key="search_subset_name")
    elif source_mode == "sample":
        sample_names = [p.name for p in list_sample_parquets()]
        selected_sample = st.selectbox("Sample source", options=sample_names if sample_names else ["<none>"], key="search_sample_name")

    source_path = resolve_search_source(source_mode, selected_subset, selected_sample)
    st.code(f"Resolved source: {source_path if source_path else 'missing'}")
    if source_mode == "normalized" and not enable_year_filter:
        st.warning("Searching across all normalized yearly partitions can be slow. Use a year range when possible.")

    if source_mode == "normalized":
        author_index_path = AUTHOR_INDEX_NORMALIZED_PATH
    elif source_mode == "sample":
        author_index_path = AUTHOR_INDEX_SAMPLE_PATH
    else:
        author_index_path = None

    indexed_authors = load_author_index(author_index_path) if author_index_path else []

    query_col, suggest_col = st.columns([1.2, 1.8])

    with query_col:
        author_query = st.text_input(
            "Author text filter",
            value="",
            key="search_author_query_input",
            help="Type part of a name to filter indexed suggestions, without removing already selected authors.",
        )
        suggestion_limit = st.number_input("Suggestion limit", min_value=10, max_value=200, value=60, step=10, key="search_suggestion_limit")

        if st.button("Clear selected authors", width="stretch", key="search_clear_selected_authors"):
            st.session_state["search_selected_authors"] = []
            st.session_state["search_clear_request"] = True

    with suggest_col:
        if st.session_state.get("search_clear_request"):
            st.session_state["search_selected_authors_input"] = []
            st.session_state["search_clear_request"] = False

        existing_selected = st.session_state.get("search_selected_authors_input", st.session_state.get("search_selected_authors", []))
        suggestions = suggest_authors(indexed_authors, author_query, limit=int(suggestion_limit)) if indexed_authors and len(author_query.strip()) >= 2 else []
        selection_options = merge_selected_with_suggestions(existing_selected, suggestions)

        selected_authors = st.multiselect(
            "Indexed author selection",
            options=selection_options,
            default=existing_selected,
            key="search_selected_authors_input",
            help="Selected authors persist even when the filter text changes.",
        )

        st.session_state["search_selected_authors"] = selected_authors

        if selected_authors:
            st.caption("Selected authors")
            st.code("\n".join(selected_authors))
        else:
            st.info("No author selected yet. Type at least 2 characters to get clean suggestions.")

        if len(author_query.strip()) >= 2:
            if suggestions:
                st.caption("Current suggestions preview")
                st.write(", ".join(suggestions[:20]))
            else:
                st.caption("No suggestions for the current filter.")

    effective_queries = selected_authors if selected_authors else ([author_query.strip()] if author_query.strip() else [])

    if st.button("Search author(s)", width="stretch", key="search_author_button"):
        if not source_path:
            raise_ui_error("Selected source is missing.")
        elif not effective_queries:
            raise_ui_error("Provide a text query or choose at least one indexed author.")
        else:
            try:
                rows = search_author_records_multi(
                    source_path,
                    author_queries=effective_queries,
                    limit=int(search_limit),
                    match_mode=match_mode,
                    start_year=start_year if enable_year_filter else None,
                    end_year=end_year if enable_year_filter else None,
                )
                profile = build_author_profile(rows, author_query=" | ".join(effective_queries))

                st.session_state["search_rows"] = rows
                st.session_state["search_profile"] = profile
                st.session_state["search_author_query"] = " | ".join(effective_queries)
                st.session_state["search_selected_authors"] = selected_authors
                st.success(f"Found {len(rows)} matching record(s).")
            except Exception as exc:
                raise_ui_error(str(exc))

    rows = st.session_state.get("search_rows", [])
    profile = st.session_state.get("search_profile")

    if rows:
        st.markdown("### Search Results")
        results_df = build_search_results_dataframe(rows)
        st.dataframe(results_df, width="stretch", height=420)

        st.markdown("### Author Profile")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            metric_card("Publications", str(profile.get("publication_count", 0)), "Matching records")
        with p2:
            metric_card("Year range", f"{profile.get('min_year', '-') } - {profile.get('max_year', '-')}", "Observed span")
        with p3:
            metric_card("Total citations", str(profile.get("total_citations", 0)), "Summed on returned rows")
        with p4:
            metric_card("Matched names", str(len(profile.get("matched_author_names", []))), "Distinct matching variants")

        left, right = st.columns(2)
        with left:
            render_table_from_list("Top collaborators", profile.get("top_collaborators", []), max_rows=10)
            render_table_from_list("Top venues", profile.get("top_venues", []), max_rows=10)
        with right:
            render_table_from_list("Top fields of study", profile.get("top_fos", []), max_rows=10)
            render_json_summary("Matched author names", {"matched_author_names": profile.get("matched_author_names", [])})

        effective_label = "_and_".join(slugify(name) for name in effective_queries) if match_mode == "and" else "_or_".join(slugify(name) for name in effective_queries)
        author_slug = effective_label[:120] if effective_label else slugify(st.session_state["search_author_query"])

        search_csv_path = SEARCH_DIR / f"author_search_{author_slug}_results.csv"
        search_profile_path = SEARCH_DIR / f"author_search_{author_slug}_profile.json"
        subset_name = f"author_{author_slug}" if len(effective_queries) == 1 else author_slug
        ego_graph_name = f"author_{author_slug}_ego_collaboration" if len(effective_queries) == 1 else f"{subset_name}_collaboration"
        ego_graph_path = GRAPHS_DIR / f"{ego_graph_name}.gexf"
        ego_analysis_path = METRICS_DIR / f"{ego_graph_name}_analysis.json"
        ego_report_path = REPORTS_DIR / f"{ego_graph_name}_report.md"

        st.markdown("### Search execution context")
        st.info(
            f"Selected authors: {len(effective_queries)} | Match mode: {match_mode.upper()} | "
            + (f"Year filter: {start_year}-{end_year}" if enable_year_filter else "Year filter: disabled")
        )

        action_a, action_b, action_c = st.columns(3)

        with action_a:
            if st.button("Export search CSV", width="stretch", key="search_export_csv"):
                try:
                    export_search_results_csv(rows, search_csv_path)
                    search_profile_path.write_text(json.dumps(profile, indent=4, ensure_ascii=False), encoding="utf-8")
                    st.success("Saved search artifacts under outputs/search/")
                except Exception as exc:
                    raise_ui_error(str(exc))

        with action_b:
            if len(effective_queries) == 1:
                if st.button("Create author subset", width="stretch", key="search_create_subset"):
                    if not source_path:
                        raise_ui_error("Source path missing.")
                    else:
                        command = [
                            PYTHON_EXECUTABLE,
                            "scripts/create_author_subset.py",
                            "--input",
                            str(source_path),
                            "--author-query",
                            effective_queries[0],
                            "--output-root",
                            str(SUBSETS_DIR),
                            "--subset-name",
                            subset_name,
                            "--overwrite",
                        ]
                        success, output = run_command(
                            command,
                            stage="create_author_subset",
                            parameters={"author_query": effective_queries[0]},
                            outputs={"subset_name": subset_name},
                        )
                        st.code(output)
                        if success:
                            st.success(f"Subset created: {subset_name}")
                        else:
                            st.error("Subset creation failed.")
            else:
                if st.button("Create multi-author subset", width="stretch", key="search_create_multi_subset"):
                    if not source_path:
                        raise_ui_error("Source path missing.")
                    else:
                        command = [
                            PYTHON_EXECUTABLE,
                            "scripts/create_multi_author_subset.py",
                            "--input",
                            str(source_path),
                            "--authors",
                            *effective_queries,
                            "--match-mode",
                            match_mode,
                            "--output-root",
                            str(SUBSETS_DIR),
                            "--subset-name",
                            subset_name,
                            "--overwrite",
                        ]
                        success, output = run_command(
                            command,
                            stage="create_multi_author_subset",
                            parameters={"author_queries": effective_queries, "match_mode": match_mode},
                            outputs={"subset_name": subset_name},
                        )
                        st.code(output)
                        if success:
                            st.success(f"Multi-author subset created: {subset_name}")
                        else:
                            st.error("Multi-author subset creation failed.")

        with action_c:
            if len(effective_queries) == 1:
                if st.button("Build ego graph", width="stretch", key="search_build_ego"):
                    if not source_path:
                        raise_ui_error("Source path missing.")
                    else:
                        command = [
                            PYTHON_EXECUTABLE,
                            "scripts/build_author_ego_graph.py",
                            "--input",
                            str(source_path),
                            "--author-query",
                            effective_queries[0],
                            "--output-dir",
                            str(GRAPHS_DIR),
                            "--graph-name",
                            ego_graph_name,
                            "--overwrite",
                        ]
                        success, output = run_command(
                            command,
                            stage="build_author_ego_graph",
                            parameters={"author_query": effective_queries[0]},
                            outputs={"graph_name": ego_graph_name},
                        )
                        st.code(output)
                        if success:
                            st.success(f"Ego graph created: {ego_graph_name}")
                        else:
                            st.error("Ego graph build failed.")
            else:
                if st.button("Build multi-author graph", width="stretch", key="search_build_multi_graph"):
                    if not source_path:
                        raise_ui_error("Source path missing.")
                    else:
                        command = [
                            PYTHON_EXECUTABLE,
                            "scripts/build_multi_author_graph.py",
                            "--input",
                            str(source_path),
                            "--authors",
                            *effective_queries,
                            "--match-mode",
                            match_mode,
                            "--output-dir",
                            str(GRAPHS_DIR),
                            "--graph-name",
                            f"{subset_name}_collaboration",
                            "--overwrite",
                        ]
                        success, output = run_command(
                            command,
                            stage="build_multi_author_graph",
                            parameters={"author_queries": effective_queries, "match_mode": match_mode},
                            outputs={"graph_name": f"{subset_name}_collaboration"},
                        )
                        st.code(output)
                        if success:
                            st.success(f"Multi-author graph created: {subset_name}_collaboration")
                        else:
                            st.error("Multi-author graph build failed.")

        action_d, action_e, action_f = st.columns(3)

        with action_d:
            if st.button("Analyze ego graph", width="stretch", key="search_analyze_ego"):
                if not ego_graph_path.exists():
                    raise_ui_error(f"Graph file not found: {ego_graph_path.name}")
                else:
                    command = [
                        PYTHON_EXECUTABLE,
                        "scripts/analyze_graph.py",
                        "--input",
                        str(ego_graph_path),
                        "--output",
                        str(ego_analysis_path),
                        "--top-n",
                        "10",
                        "--betweenness-sample-k",
                        "100",
                    ]
                    success, output = run_command(
                        command,
                        stage="analyze_author_ego_graph",
                        parameters={"graph_name": ego_graph_name},
                        outputs={"analysis": ego_analysis_path.name},
                    )
                    st.code(output)
                    if success:
                        st.success("Ego graph analysis completed.")
                    else:
                        st.error("Ego graph analysis failed.")

        with action_e:
            if st.button("Export ego report", width="stretch", key="search_export_ego_report"):
                if not ego_analysis_path.exists():
                    raise_ui_error(f"Analysis file not found: {ego_analysis_path.name}")
                else:
                    command = [
                        PYTHON_EXECUTABLE,
                        "scripts/export_analysis_report.py",
                        "--input",
                        str(ego_analysis_path),
                        "--output",
                        str(ego_report_path),
                        "--name",
                        ego_graph_name,
                    ]
                    success, output = run_command(
                        command,
                        stage="export_author_ego_report",
                        parameters={"analysis": ego_analysis_path.name},
                        outputs={"report": ego_report_path.name},
                    )
                    st.code(output)
                    if success:
                        st.success("Ego report exported.")
                    else:
                        st.error("Ego report export failed.")

        with action_f:
            if st.button("Open in Insights", width="stretch", key="search_open_in_insights"):
                st.session_state["insights_base_name"] = ego_graph_name
                st.session_state["insights_graph_type"] = "collaboration"
                st.success(f"Insights target set to: {ego_graph_name}. Open the Insights tab to inspect it.")

        preview_left, preview_right = st.columns(2)
        with preview_left:
            subset_summary = read_json_if_exists(SUBSETS_DIR / subset_name / "_subset_summary.json")
            render_json_summary("Author subset summary", subset_summary)
            graph_summary = read_json_if_exists(GRAPHS_DIR / f"{ego_graph_name}_summary.json")
            render_json_summary("Ego graph summary", graph_summary)
        with preview_right:
            analysis_summary = read_json_if_exists(ego_analysis_path)
            render_json_summary("Ego graph analysis", analysis_summary)
            report_preview = read_text_if_exists(ego_report_path)
            if report_preview:
                st.markdown("#### Ego report preview")
                st.text_area("Report preview", report_preview[:4000], height=220, key="search_report_preview")


with publication_tab:
    section_header("Publication Search", "Search publications by title, inspect their profile, and build publication-centered citation artifacts.")
    st.info("Quick guide: choose a source, enter a title fragment, optionally filter by year range, then search. Use sample or subset for faster demos.")

    source_col, limit_col = st.columns([1.2, 0.8])

    with source_col:
        publication_source_mode = st.selectbox("Source", ["normalized", "subset", "sample"], key="publication_source_mode")

    with limit_col:
        publication_limit = st.number_input("Result row limit", min_value=1, max_value=5000, value=100, step=25, key="publication_limit")

    publication_selected_subset = None
    publication_selected_sample = None

    if publication_source_mode == "subset":
        subset_names = [p.name for p in list_subset_dirs()]
        publication_selected_subset = st.selectbox(
            "Subset source",
            options=subset_names if subset_names else ["<none>"],
            key="publication_subset_name",
        )
    elif publication_source_mode == "sample":
        sample_names = [p.name for p in list_sample_parquets()]
        publication_selected_sample = st.selectbox(
            "Sample source",
            options=sample_names if sample_names else ["<none>"],
            key="publication_sample_name",
        )

    publication_source_path = resolve_search_source(
        publication_source_mode,
        publication_selected_subset,
        publication_selected_sample,
    )

    st.code(f"Resolved source: {publication_source_path if publication_source_path else 'missing'}")

    publication_enable_year_filter = st.checkbox("Filter by year range", value=False, key="publication_enable_year_filter")
    publication_year_col1, publication_year_col2 = st.columns(2)
    with publication_year_col1:
        publication_start_year = st.number_input("Start year", min_value=1800, max_value=2026, value=2018, step=1, key="publication_start_year")
    with publication_year_col2:
        publication_end_year = st.number_input("End year", min_value=1800, max_value=2026, value=2022, step=1, key="publication_end_year")

    publication_title_query = st.text_input(
        "Publication title filter",
        value=st.session_state.get("publication_title_query", ""),
        key="publication_title_query_input",
        help="Search publications by title fragment.",
    )

    if st.button("Search publications", width="stretch", key="publication_search_button"):
        if not publication_source_path:
            raise_ui_error("Selected source is missing.")
        elif not publication_title_query.strip():
            raise_ui_error("Publication title query cannot be empty.")
        else:
            try:
                rows = search_publication_records(
                    publication_source_path,
                    title_query=publication_title_query.strip(),
                    limit=int(publication_limit),
                    start_year=publication_start_year if publication_enable_year_filter else None,
                    end_year=publication_end_year if publication_enable_year_filter else None,
                )
                profile = build_publication_profile(rows, title_query=publication_title_query.strip())

                st.session_state["publication_rows"] = rows
                st.session_state["publication_profile"] = profile
                st.session_state["publication_title_query"] = publication_title_query.strip()
                st.success(f"Found {len(rows)} matching publication record(s).")
            except Exception as exc:
                raise_ui_error(str(exc))

    publication_rows = st.session_state.get("publication_rows", [])
    publication_profile = st.session_state.get("publication_profile")

    if publication_rows:
        st.markdown("### Publication Search Results")
        publication_df = build_publication_results_dataframe(publication_rows)
        st.dataframe(publication_df, width="stretch", height=420)

        st.markdown("### Publication Profile")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            metric_card("Publications", str(publication_profile.get("publication_count", 0)), "Matching records")
        with p2:
            metric_card("Year range", f"{publication_profile.get('min_year', '-') } - {publication_profile.get('max_year', '-')}", "Observed span")
        with p3:
            metric_card("Total citations", str(publication_profile.get("total_citations", 0)), "Summed on returned rows")
        with p4:
            metric_card("Top authors", str(len(publication_profile.get("top_authors", []))), "Distinct ranked authors")

        left, right = st.columns(2)
        with left:
            render_table_from_list("Top venues", publication_profile.get("top_venues", []), max_rows=10)
            render_table_from_list("Top authors", publication_profile.get("top_authors", []), max_rows=10)
        with right:
            render_table_from_list("Top fields of study", publication_profile.get("top_fos", []), max_rows=10)
            render_json_summary(
                "Search summary",
                {
                    "title_query": publication_profile.get("title_query"),
                    "publication_count": publication_profile.get("publication_count"),
                    "total_citations": publication_profile.get("total_citations"),
                },
            )

        publication_slug = slugify(st.session_state["publication_title_query"])
        publication_csv_path = SEARCH_DIR / f"publication_{publication_slug}_results.csv"
        publication_profile_path = SEARCH_DIR / f"publication_{publication_slug}_profile.json"
        publication_subset_name = f"publication_{publication_slug}"
        publication_graph_name = f"publication_{publication_slug}_citation"
        publication_graph_path = GRAPHS_DIR / f"{publication_graph_name}.gexf"
        publication_analysis_path = METRICS_DIR / f"{publication_graph_name}_analysis.json"
        publication_report_path = REPORTS_DIR / f"{publication_graph_name}_report.md"

        st.markdown("### Search execution context")
        st.info(
            f"Title query: {st.session_state['publication_title_query']} | "
            + (f"Year filter: {publication_start_year}-{publication_end_year}" if publication_enable_year_filter else "Year filter: disabled")
        )

        action_a, action_b, action_c = st.columns(3)

        with action_a:
            if st.button("Export publication CSV", width="stretch", key="publication_export_csv"):
                try:
                    export_publication_results_csv(publication_rows, publication_csv_path)
                    publication_profile_path.write_text(json.dumps(publication_profile, indent=4, ensure_ascii=False), encoding="utf-8")
                    st.success("Saved publication search artifacts under outputs/search/")
                except Exception as exc:
                    raise_ui_error(str(exc))

        with action_b:
            if st.button("Create publication subset", width="stretch", key="publication_create_subset"):
                if not publication_source_path:
                    raise_ui_error("Source path missing.")
                else:
                    command = [
                        PYTHON_EXECUTABLE,
                        "scripts/create_publication_subset.py",
                        "--input",
                        str(publication_source_path),
                        "--title-query",
                        st.session_state["publication_title_query"],
                        "--output-root",
                        str(SUBSETS_DIR),
                        "--subset-name",
                        publication_subset_name,
                        "--overwrite",
                    ]
                    success, output = run_command(
                        command,
                        stage="create_publication_subset",
                        parameters={"title_query": st.session_state["publication_title_query"]},
                        outputs={"subset_name": publication_subset_name},
                    )
                    st.code(output)
                    if success:
                        st.success(f"Publication subset created: {publication_subset_name}")
                    else:
                        st.error("Publication subset creation failed.")

        with action_c:
            if st.button("Build publication graph", width="stretch", key="publication_build_graph"):
                if not publication_source_path:
                    raise_ui_error("Source path missing.")
                else:
                    command = [
                        PYTHON_EXECUTABLE,
                        "scripts/build_publication_neighborhood_graph.py",
                        "--input",
                        str(publication_source_path),
                        "--title-query",
                        st.session_state["publication_title_query"],
                        "--output-dir",
                        str(GRAPHS_DIR),
                        "--graph-name",
                        publication_graph_name,
                        "--overwrite",
                    ]
                    success, output = run_command(
                        command,
                        stage="build_publication_graph",
                        parameters={"title_query": st.session_state["publication_title_query"]},
                        outputs={"graph_name": publication_graph_name},
                    )
                    st.code(output)
                    if success:
                        st.success(f"Publication graph created: {publication_graph_name}")
                    else:
                        st.error("Publication graph build failed.")

        action_d, action_e, action_f = st.columns(3)

        with action_d:
            if st.button("Analyze publication graph", width="stretch", key="publication_analyze_graph"):
                if not publication_graph_path.exists():
                    raise_ui_error(f"Graph file not found: {publication_graph_path.name}")
                else:
                    command = [
                        PYTHON_EXECUTABLE,
                        "scripts/analyze_graph.py",
                        "--input",
                        str(publication_graph_path),
                        "--output",
                        str(publication_analysis_path),
                        "--top-n",
                        "10",
                        "--betweenness-sample-k",
                        "100",
                    ]
                    success, output = run_command(
                        command,
                        stage="analyze_publication_graph",
                        parameters={"graph_name": publication_graph_name},
                        outputs={"analysis": publication_analysis_path.name},
                    )
                    st.code(output)
                    if success:
                        st.success("Publication graph analysis completed.")
                    else:
                        st.error("Publication graph analysis failed.")

        with action_e:
            if st.button("Export publication report", width="stretch", key="publication_export_report"):
                if not publication_analysis_path.exists():
                    raise_ui_error(f"Analysis file not found: {publication_analysis_path.name}")
                else:
                    command = [
                        PYTHON_EXECUTABLE,
                        "scripts/export_analysis_report.py",
                        "--input",
                        str(publication_analysis_path),
                        "--output",
                        str(publication_report_path),
                        "--name",
                        publication_graph_name,
                    ]
                    success, output = run_command(
                        command,
                        stage="export_publication_report",
                        parameters={"analysis": publication_analysis_path.name},
                        outputs={"report": publication_report_path.name},
                    )
                    st.code(output)
                    if success:
                        st.success("Publication report exported.")
                    else:
                        st.error("Publication report export failed.")

        with action_f:
            if st.button("Open publication graph in Insights", width="stretch", key="publication_open_in_insights"):
                st.session_state["insights_base_name"] = publication_graph_name
                st.session_state["insights_graph_type"] = "citation"
                st.success(f"Insights target set to: {publication_graph_name}. Open the Insights tab to inspect it.")

        preview_left, preview_right = st.columns(2)
        with preview_left:
            subset_summary = read_json_if_exists(SUBSETS_DIR / publication_subset_name / "_subset_summary.json")
            render_json_summary("Publication subset summary", subset_summary)
            graph_summary = read_json_if_exists(GRAPHS_DIR / f"{publication_graph_name}_summary.json")
            render_json_summary("Publication graph summary", graph_summary)
        with preview_right:
            analysis_summary = read_json_if_exists(publication_analysis_path)
            render_json_summary("Publication graph analysis", analysis_summary)
            report_preview = read_text_if_exists(publication_report_path)
            if report_preview:
                st.markdown("#### Publication report preview")
                st.text_area("Publication report preview", report_preview[:4000], height=220, key="publication_report_preview")

with demo_tab:
    section_header("Demo Workflow", "Create or select a sample, then build, analyze and report on it end to end.")

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

    with col2:
        if st.button("Analyze demo graph", width="stretch"):
            graph_input = GRAPHS_DIR / f"{demo_graph_name}_{demo_graph_type}.gexf"
            analysis_output = METRICS_DIR / f"{demo_graph_name}_{demo_graph_type}_analysis.json"

            if not graph_input.exists():
                raise_ui_error(f"Graph file not found: {graph_input.name}")
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

    with col3:
        if st.button("Export demo report", width="stretch"):
            analysis_input = METRICS_DIR / f"{demo_graph_name}_{demo_graph_type}_analysis.json"
            report_output = REPORTS_DIR / f"{demo_graph_name}_{demo_graph_type}_report.md"

            if not analysis_input.exists():
                raise_ui_error(f"Analysis file not found: {analysis_input.name}")
            else:
                command = [
                    PYTHON_EXECUTABLE,
                    "scripts/export_analysis_report.py",
                    "--input",
                    str(analysis_input),
                    "--output",
                    str(report_output),
                    "--name",
                    f"{demo_graph_name}_{demo_graph_type}",
                ]
                success, output = run_command(
                    command,
                    stage="export_demo_report",
                    parameters={"analysis": str(analysis_input)},
                    outputs={"report": str(report_output)},
                )
                st.code(output)
                if success:
                    st.success("Demo report exported.")
                else:
                    st.error("Demo report export failed.")

    st.markdown("---")

    current_sample_name = None
    if mode == "Use existing sample" and sample_names:
        current_sample_name = selected_sample_name
    elif selected_sample_path is not None:
        current_sample_name = selected_sample_path.name

    current_metadata = SAMPLE_DIR / current_sample_name.replace(".parquet", "_metadata.json") if current_sample_name else None
    current_graph_summary = GRAPHS_DIR / f"{demo_graph_name}_{demo_graph_type}_summary.json"
    current_analysis = METRICS_DIR / f"{demo_graph_name}_{demo_graph_type}_analysis.json"
    current_report = REPORTS_DIR / f"{demo_graph_name}_{demo_graph_type}_report.md"

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

    report_text = read_text_if_exists(current_report)
    if report_text:
        st.markdown("### Demo Report Preview")
        st.text_area("Markdown report", report_text[:5000], height=260)

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
    selected_base_default = st.session_state.get("insights_base_name")
    selected_graph_type = st.selectbox("Graph type to analyze", ["citation", "collaboration"], key="analysis_graph_type")

    selected_index = 0
    if selected_base_default and selected_base_default in graph_bases:
        selected_index = graph_bases.index(selected_base_default)

    selected_base = st.selectbox("Choose graph base name", options=graph_bases if graph_bases else ["<none>"], index=selected_index if graph_bases else 0)
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

    selected_base_default = st.session_state.get("insights_base_name")
    selected_type_default = st.session_state.get("insights_graph_type", "collaboration")

    base_index = 0
    if selected_base_default and selected_base_default in analysis_bases:
        base_index = analysis_bases.index(selected_base_default)

    selected_insight_base = st.selectbox("Choose analysis base name", options=analysis_bases if analysis_bases else ["<none>"], index=base_index if analysis_bases else 0)
    type_index = 0 if selected_type_default == "citation" else 1
    selected_insight_type = st.selectbox("Analysis graph type", ["citation", "collaboration"], key="insight_graph_type", index=type_index)

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


with path_tab:
    section_header("Path Finder", "Investigate whether two nodes are connected and inspect the shortest path between them.")
    st.info("Use collaboration graphs for author-to-author paths and citation graphs for publication-to-publication paths.")

    graph_bases = extract_graph_base_names()
    top_row_1, top_row_2, top_row_3 = st.columns([1.2, 1.2, 0.8])

    with top_row_1:
        graph_type = st.selectbox("Graph type", ["collaboration", "citation"], key="path_graph_type")

    with top_row_2:
        selected_base = st.selectbox("Graph base name", options=graph_bases if graph_bases else ["<none>"], key="path_graph_base")

    with top_row_3:
        max_paths = st.number_input("Maximum shortest paths", min_value=1, max_value=20, value=5, step=1, key="path_max_paths")

    if selected_base != "<none>":
        graph_path = GRAPHS_DIR / f"{selected_base}_{graph_type}.gexf"
    else:
        graph_path = GRAPHS_DIR / "missing.gexf"

    st.code(f"Graph path: {graph_path}")

    if graph_path.exists():
        try:
            catalog = load_graph_node_catalog(str(graph_path))
            st.caption(f"Loaded {len(catalog)} node(s) from the graph.")

            control_col_1, control_col_2, control_col_3 = st.columns([1.2, 1.2, 0.8])

            with control_col_1:
                source_filter = st.text_input("Source filter", value="", key="path_source_filter")
                source_candidates = filter_node_catalog(catalog, source_filter, limit=100)
                source_options = [f"{row['display_name']} | {row['node_id']}" for row in source_candidates]

                if st.session_state.get("path_source_label") not in source_options and source_options:
                    if st.session_state.get("path_source_label") == "<none>":
                        pass

                selected_source_label = st.selectbox(
                    "Source node",
                    options=source_options if source_options else ["<none>"],
                    key="path_source_label",
                )

            with control_col_2:
                target_filter = st.text_input("Target filter", value="", key="path_target_filter")
                target_candidates = filter_node_catalog(catalog, target_filter, limit=100)
                target_options = [f"{row['display_name']} | {row['node_id']}" for row in target_candidates]

                selected_target_label = st.selectbox(
                    "Target node",
                    options=target_options if target_options else ["<none>"],
                    key="path_target_label",
                )

            with control_col_3:
                st.markdown("#### Actions")
                if st.button("Swap source / target", width="stretch", key="path_swap_button"):
                    source_value = st.session_state.get("path_source_label", "<none>")
                    target_value = st.session_state.get("path_target_label", "<none>")
                    st.session_state["path_source_label"] = target_value
                    st.session_state["path_target_label"] = source_value
                    st.rerun()

                if st.button("Clear path result", width="stretch", key="path_clear_result_button"):
                    st.session_state["path_finder_result"] = None
                    st.rerun()

            if st.button("Investigate path", width="stretch", key="path_investigate_button"):
                if st.session_state.get("path_source_label") == "<none>" or st.session_state.get("path_target_label") == "<none>":
                    raise_ui_error("Choose both source and target nodes.")
                else:
                    try:
                        source_node_id = st.session_state["path_source_label"].split(" | ")[-1]
                        target_node_id = st.session_state["path_target_label"].split(" | ")[-1]
                        graph = load_graph(str(graph_path))
                        result = investigate_path_between_nodes(
                            graph,
                            source_node_id=source_node_id,
                            target_node_id=target_node_id,
                            max_paths=int(max_paths),
                        )
                        result["graph_path"] = str(graph_path)
                        st.session_state["path_finder_result"] = result
                        st.success("Path investigation completed.")
                    except Exception as exc:
                        raise_ui_error(str(exc))

        except Exception as exc:
            raise_ui_error(f"Failed to load graph catalog: {exc}")
    else:
        st.info("Choose a graph that exists in outputs/graphs first.")

    result = st.session_state.get("path_finder_result")

    if isinstance(result, dict):
        st.markdown("### Path Investigation Result")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Connected", "Yes" if result.get("connected") else "No", "Path exists or not")
        with c2:
            metric_card("Distance", str(result.get("shortest_path_length")), "Number of hops")
        with c3:
            metric_card("Directed graph", "Yes" if result.get("graph_is_directed") else "No", "Graph orientation")
        with c4:
            metric_card("Returned paths", str(len(result.get("all_shortest_paths_readable", []))), "Shortest paths found")

        left, right = st.columns(2)
        with left:
            render_json_summary(
                "Endpoints",
                {
                    "source_node_id": result.get("source_node_id"),
                    "source_display_name": result.get("source_display_name"),
                    "target_node_id": result.get("target_node_id"),
                    "target_display_name": result.get("target_display_name"),
                },
            )
        with right:
            render_json_summary(
                "Connectivity Summary",
                {
                    "connected": result.get("connected"),
                    "shortest_path_length": result.get("shortest_path_length"),
                    "graph_is_directed": result.get("graph_is_directed"),
                    "graph_path": result.get("graph_path"),
                },
            )

        shortest_path_readable = result.get("shortest_path_readable", [])
        if shortest_path_readable:
            st.markdown("#### Main shortest path")
            main_labels = [step.get("display_name", step.get("node_id", "")) for step in shortest_path_readable]
            st.code(" -> ".join(main_labels))
            st.dataframe(
                readable_path_to_dataframe(shortest_path_readable),
                width="stretch",
                height=min(420, 80 + 35 * len(shortest_path_readable)),
            )
        else:
            st.info("No shortest path available.")

        render_readable_paths_table(result.get("all_shortest_paths_readable", []), "All shortest paths")

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
        render_files_list("Search files", list_relative_files(SEARCH_DIR, limit=30))
        render_files_list("Sample files", list_relative_files(SAMPLE_DIR, limit=30))
        render_files_list("Graph files", list_relative_files(GRAPHS_DIR, limit=30))
        render_files_list("Report files", list_relative_files(REPORTS_DIR, suffix=".md", limit=30))
    with c2:
        render_files_list("Metric files", list_relative_files(METRICS_DIR, limit=30))
        render_files_list("Quality files", list_relative_files(QUALITY_DIR, limit=30))
