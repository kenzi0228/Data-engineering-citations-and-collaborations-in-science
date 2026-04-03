from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

import duckdb
import networkx as nx

from citation_graphs.search import search_author_records, slugify


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


def filter_rows_for_author(
    rows: list[dict[str, Any]],
    author_query: str,
) -> list[dict[str, Any]]:
    filtered = []
    for row in rows:
        author_names = [str(name).strip() for name in _normalize_list(row.get("author_names")) if str(name).strip()]
        if any(_match_author_name(name, author_query) for name in author_names):
            filtered.append(row)
    return filtered


def save_author_subset_parquet(
    rows: list[dict[str, Any]],
    output_dir: str | Path,
    author_query: str,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "_author_subset_temp.json"
    parquet_path = output_dir / "data.parquet"
    summary_path = output_dir / "_subset_summary.json"

    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    con = duckdb.connect(database=":memory:")
    try:
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
    finally:
        con.close()

    if json_path.exists():
        json_path.unlink()

    years = [
        int(row["year_clean"])
        for row in rows
        if row.get("year_clean") is not None and str(row.get("year_clean")).strip() != ""
    ]

    summary = {
        "subset_name": output_dir.name,
        "mode": "author",
        "author_query": author_query,
        "row_count": len(rows),
        "output_dir": str(output_dir.resolve()),
        "data_file": str(parquet_path.resolve()),
        "preview": {
            "min_year": min(years) if years else None,
            "max_year": max(years) if years else None,
        },
    }
    summary_path.write_text(json.dumps(summary, indent=4, ensure_ascii=False), encoding="utf-8")
    return summary


def build_author_ego_collaboration_graph(
    rows: list[dict[str, Any]],
    author_query: str,
    include_center_node_only_matches: bool = True,
) -> nx.Graph:
    graph = nx.Graph()

    filtered_rows = filter_rows_for_author(rows, author_query)

    for row in filtered_rows:
        author_names = [str(name).strip() for name in _normalize_list(row.get("author_names")) if str(name).strip()]
        author_ids = [str(value).strip() for value in _normalize_list(row.get("author_ids")) if str(value).strip()]

        # align ids to names when possible
        pairs: list[tuple[str, str | None]] = []
        for idx, name in enumerate(author_names):
            author_id = author_ids[idx] if idx < len(author_ids) else None
            pairs.append((name, author_id))

        if include_center_node_only_matches:
            if not any(_match_author_name(name, author_query) for name, _ in pairs):
                continue

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
                is_query_match=_match_author_name(name, author_query),
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


def save_author_ego_graph_outputs(
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
        "graph_type": "author_ego_collaboration",
        "is_directed": False,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": density,
        "gexf_file": str(gexf_path.resolve()),
        "source_parquet": str(Path(source_parquet).resolve()) if source_parquet else None,
    }
    summary_path.write_text(json.dumps(summary, indent=4, ensure_ascii=False), encoding="utf-8")
    return summary


def create_author_subset_from_input(
    input_path: str | Path,
    author_query: str,
    output_dir: str | Path,
) -> dict[str, Any]:
    rows = search_author_records(input_path=input_path, author_query=author_query, limit=1_000_000)
    filtered = filter_rows_for_author(rows, author_query=author_query)
    return save_author_subset_parquet(filtered, output_dir=output_dir, author_query=author_query)


def build_author_ego_graph_from_input(
    input_path: str | Path,
    author_query: str,
    output_dir: str | Path,
    graph_name: str | None = None,
) -> dict[str, Any]:
    rows = search_author_records(input_path=input_path, author_query=author_query, limit=1_000_000)
    filtered = filter_rows_for_author(rows, author_query=author_query)
    graph = build_author_ego_collaboration_graph(filtered, author_query=author_query)

    resolved_graph_name = graph_name or f"author_{slugify(author_query)}_ego_collaboration"
    return save_author_ego_graph_outputs(
        graph,
        output_dir=output_dir,
        graph_name=resolved_graph_name,
        source_parquet=input_path,
    )
