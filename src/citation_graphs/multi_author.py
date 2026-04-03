from __future__ import annotations

import json
import time
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd
import networkx as nx

from citation_graphs.search import search_author_records_multi, slugify


def _normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _match_author_name(candidate: str, author_query: str) -> bool:
    candidate = (candidate or "").strip().lower()
    author_query = (author_query or "").strip().lower()
    return bool(candidate) and bool(author_query) and author_query in candidate


def build_multi_author_slug(author_queries: list[str], match_mode: str, max_authors: int = 3) -> str:
    cleaned = [slugify(author) for author in author_queries if author and author.strip()]
    selected = cleaned[:max_authors]
    joined = "_".join(selected) if selected else "unknown"
    return f"authors_{joined}_{match_mode}"


def row_matches_authors(
    row: dict[str, Any],
    author_queries: list[str],
    match_mode: str = "or",
) -> bool:
    names = [str(name).strip() for name in _normalize_list(row.get("author_names")) if str(name).strip()]
    match_mode = (match_mode or "or").strip().lower()

    if not author_queries:
        return False

    if match_mode == "or":
        return any(
            any(_match_author_name(name, query) for name in names)
            for query in author_queries
        )

    if match_mode == "and":
        return all(
            any(_match_author_name(name, query) for name in names)
            for query in author_queries
        )

    raise ValueError("match_mode must be 'or' or 'and'")


def filter_rows_for_authors(
    rows: list[dict[str, Any]],
    author_queries: list[str],
    match_mode: str = "or",
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row_matches_authors(row, author_queries=author_queries, match_mode=match_mode)
    ]


def save_multi_author_subset_parquet(
    rows: list[dict[str, Any]],
    output_dir: str | Path,
    author_queries: list[str],
    match_mode: str,
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
        "mode": "multi_author",
        "author_queries": author_queries,
        "match_mode": match_mode,
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


def build_multi_author_collaboration_graph(
    rows: list[dict[str, Any]],
) -> nx.Graph:
    graph = nx.Graph()

    for row in rows:
        author_names = [str(name).strip() for name in _normalize_list(row.get("author_names")) if str(name).strip()]
        author_ids = [str(value).strip() for value in _normalize_list(row.get("author_ids")) if str(value).strip()]

        pairs: list[tuple[str, str | None]] = []
        for idx, name in enumerate(author_names):
            author_id = author_ids[idx] if idx < len(author_ids) else None
            pairs.append((name, author_id))

        unique_pairs = []
        seen = set()
        for name, author_id in pairs:
            key = (name, author_id)
            if key in seen:
                continue
            seen.add(key)
            unique_pairs.append((name, author_id))

        for name, author_id in unique_pairs:
            node_id = author_id or name
            graph.add_node(
                node_id,
                display_name=name,
                name=name,
                node_type="author",
                label=node_id,
            )

        for (name_a, author_id_a), (name_b, author_id_b) in combinations(unique_pairs, 2):
            node_a = author_id_a or name_a
            node_b = author_id_b or name_b

            if graph.has_edge(node_a, node_b):
                graph[node_a][node_b]["weight"] += 1
                graph[node_a][node_b]["shared_papers"] += 1
            else:
                graph.add_edge(
                    node_a,
                    node_b,
                    weight=1,
                    shared_papers=1,
                )

    return graph


def save_multi_author_graph_outputs(
    graph: nx.Graph,
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
        "graph_type": "multi_author_collaboration",
        "is_directed": False,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": density,
        "gexf_file": str(gexf_path.resolve()),
        "source_parquet": str(Path(source_parquet).resolve()) if source_parquet else None,
    }
    summary_path.write_text(json.dumps(summary, indent=4, ensure_ascii=False), encoding="utf-8")
    return summary


def create_multi_author_subset_from_input(
    input_path: str | Path,
    author_queries: list[str],
    match_mode: str,
    output_dir: str | Path,
) -> dict[str, Any]:
    rows = search_author_records_multi(
        input_path=input_path,
        author_queries=author_queries,
        limit=1_000_000,
        match_mode=match_mode,
    )
    filtered = filter_rows_for_authors(rows, author_queries=author_queries, match_mode=match_mode)
    return save_multi_author_subset_parquet(
        filtered,
        output_dir=output_dir,
        author_queries=author_queries,
        match_mode=match_mode,
    )


def build_multi_author_graph_from_input(
    input_path: str | Path,
    author_queries: list[str],
    match_mode: str,
    output_dir: str | Path,
    graph_name: str | None = None,
) -> dict[str, Any]:
    rows = search_author_records_multi(
        input_path=input_path,
        author_queries=author_queries,
        limit=1_000_000,
        match_mode=match_mode,
    )
    filtered = filter_rows_for_authors(rows, author_queries=author_queries, match_mode=match_mode)
    graph = build_multi_author_collaboration_graph(filtered)

    resolved_graph_name = graph_name or f"{build_multi_author_slug(author_queries, match_mode)}_collaboration"
    return save_multi_author_graph_outputs(
        graph,
        output_dir=output_dir,
        graph_name=resolved_graph_name,
        source_parquet=input_path,
    )
