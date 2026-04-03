from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from citation_graphs.graph_builder import build_citation_graph
from citation_graphs.publication_search import search_publication_records, slugify


def filter_rows_for_publications(
    rows: list[dict[str, Any]],
    title_query: str,
) -> list[dict[str, Any]]:
    q = (title_query or "").strip().lower()
    if not q:
        return []
    return [row for row in rows if q in str(row.get("title") or "").lower()]


def save_publication_subset_parquet(
    rows: list[dict[str, Any]],
    output_dir: str | Path,
    title_query: str,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / "data.parquet"
    summary_path = output_dir / "_subset_summary.json"

    start = time.perf_counter()
    df = pd.DataFrame(rows)
    df.to_parquet(parquet_path, index=False)
    write_seconds = round(time.perf_counter() - start, 4)

    years = [
        int(row["year_clean"])
        for row in rows
        if row.get("year_clean") is not None and str(row.get("year_clean")).strip() != ""
    ]

    summary = {
        "subset_name": output_dir.name,
        "mode": "publication",
        "title_query": title_query,
        "row_count": len(rows),
        "output_dir": str(output_dir.resolve()),
        "data_file": str(parquet_path.resolve()),
        "write_seconds": write_seconds,
        "preview": {
            "min_year": min(years) if years else None,
            "max_year": max(years) if years else None,
        },
    }
    summary_path.write_text(json.dumps(summary, indent=4, ensure_ascii=False), encoding="utf-8")
    return summary


def create_publication_subset_from_input(
    input_path: str | Path,
    title_query: str,
    output_dir: str | Path,
    limit: int = 1_000_000,
) -> dict[str, Any]:
    rows = search_publication_records(
        input_path=input_path,
        title_query=title_query,
        limit=limit,
    )
    filtered = filter_rows_for_publications(rows, title_query=title_query)
    return save_publication_subset_parquet(filtered, output_dir=output_dir, title_query=title_query)


def save_publication_graph_outputs(
    graph: nx.DiGraph,
    output_dir: str | Path,
    graph_name: str,
    source_parquet: str | Path | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gexf_path = output_dir / f"{graph_name}.gexf"
    summary_path = output_dir / f"{graph_name}_summary.json"

    nx.write_gexf(graph, gexf_path)

    density = nx.density(graph) if graph.number_of_nodes() > 1 else 0.0

    summary = {
        "graph_type": "publication_citation_neighborhood",
        "is_directed": True,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": density,
        "gexf_file": str(gexf_path.resolve()),
        "source_parquet": str(Path(source_parquet).resolve()) if source_parquet else None,
    }
    summary_path.write_text(json.dumps(summary, indent=4, ensure_ascii=False), encoding="utf-8")
    return summary


def build_publication_neighborhood_graph_from_rows(rows: list[dict[str, Any]]) -> nx.DiGraph:
    return build_citation_graph(rows)


def build_publication_neighborhood_graph_from_input(
    input_path: str | Path,
    title_query: str,
    output_dir: str | Path,
    graph_name: str | None = None,
    limit: int = 1_000_000,
) -> dict[str, Any]:
    rows = search_publication_records(
        input_path=input_path,
        title_query=title_query,
        limit=limit,
    )
    filtered = filter_rows_for_publications(rows, title_query=title_query)
    graph = build_publication_neighborhood_graph_from_rows(filtered)

    resolved_graph_name = graph_name or f"publication_{slugify(title_query)}_citation"
    return save_publication_graph_outputs(
        graph,
        output_dir=output_dir,
        graph_name=resolved_graph_name,
        source_parquet=input_path,
    )
