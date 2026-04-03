from __future__ import annotations

import json
import time
from itertools import combinations
from pathlib import Path
from typing import Any

import duckdb
import networkx as nx


GRAPH_BUILD_COLUMNS = [
    "paper_id",
    "title",
    "year_clean",
    "n_citation",
    "lang",
    "venue_name",
    "fos_count",
    "reference_count",
    "author_count",
    "references",
    "author_ids",
    "author_names",
]


def _normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _readable_input(path: Path) -> str:
    path = Path(path)
    if path.is_dir():
        return str(path / "**" / "*.parquet")
    return str(path)


def load_graph_build_rows(input_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    input_path = Path(input_path)
    source = _readable_input(input_path)

    started = time.perf_counter()

    query = f"""
    SELECT
        paper_id,
        title,
        year_clean,
        n_citation,
        lang,
        venue_name,
        fos_count,
        reference_count,
        author_count,
        "references" AS references_list,
        author_ids,
        author_names
    FROM read_parquet('{source}')
    """

    con = duckdb.connect(database=":memory:")
    try:
        rows = con.execute(query).fetchdf().to_dict(orient="records")
    finally:
        con.close()

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized_rows.append(
            {
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "year_clean": row.get("year_clean"),
                "n_citation": row.get("n_citation"),
                "lang": row.get("lang"),
                "venue_name": row.get("venue_name"),
                "fos_count": row.get("fos_count"),
                "reference_count": row.get("reference_count"),
                "author_count": row.get("author_count"),
                "references": _normalize_list(row.get("references_list")),
                "author_ids": _normalize_list(row.get("author_ids")),
                "author_names": _normalize_list(row.get("author_names")),
            }
        )

    elapsed = round(time.perf_counter() - started, 4)
    return normalized_rows, {
        "load_seconds": elapsed,
        "row_count": len(normalized_rows),
        "source": str(input_path.resolve()),
    }


def build_citation_graph(rows: list[dict[str, Any]]) -> tuple[nx.DiGraph, dict[str, Any]]:
    started = time.perf_counter()

    graph = nx.DiGraph()

    paper_ids = set()
    for row in rows:
        paper_id = row.get("paper_id")
        if paper_id:
            paper_ids.add(str(paper_id))

    for row in rows:
        paper_id = row.get("paper_id")
        if not paper_id:
            continue

        node_id = str(paper_id)
        graph.add_node(
            node_id,
            display_name=row.get("title") or node_id,
            node_type="publication",
            title=row.get("title"),
            year=row.get("year_clean"),
            n_citation=row.get("n_citation"),
            lang=row.get("lang"),
            venue_name=row.get("venue_name"),
            fos_count=row.get("fos_count"),
            reference_count=row.get("reference_count"),
            author_count=row.get("author_count"),
            label=node_id,
        )

    edge_count = 0
    for row in rows:
        source_id = row.get("paper_id")
        if not source_id:
            continue
        source_id = str(source_id)

        for ref in row.get("references", []):
            ref_id = str(ref).strip()
            if not ref_id:
                continue
            if ref_id not in paper_ids:
                continue

            if not graph.has_node(ref_id):
                continue

            graph.add_edge(ref_id, source_id)
            edge_count += 1

    elapsed = round(time.perf_counter() - started, 4)
    return graph, {
        "build_seconds": elapsed,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "edge_insertions_attempted": edge_count,
    }


def build_collaboration_graph(rows: list[dict[str, Any]]) -> tuple[nx.Graph, dict[str, Any]]:
    started = time.perf_counter()

    graph = nx.Graph()
    edge_updates = 0

    for row in rows:
        author_names = [str(name).strip() for name in row.get("author_names", []) if str(name).strip()]
        author_ids = [str(value).strip() for value in row.get("author_ids", []) if str(value).strip()]

        author_pairs: list[tuple[str, str | None]] = []
        for idx, name in enumerate(author_names):
            author_id = author_ids[idx] if idx < len(author_ids) else None
            author_pairs.append((name, author_id))

        unique_pairs = []
        seen = set()
        for name, author_id in author_pairs:
            key = (name, author_id)
            if key in seen:
                continue
            seen.add(key)
            unique_pairs.append((name, author_id))

        for name, author_id in unique_pairs:
            node_id = author_id or name
            if not graph.has_node(node_id):
                graph.add_node(
                    node_id,
                    display_name=name,
                    node_type="author",
                    name=name,
                    label=node_id,
                )

        for (name_a, author_id_a), (name_b, author_id_b) in combinations(unique_pairs, 2):
            node_a = author_id_a or name_a
            node_b = author_id_b or name_b

            if graph.has_edge(node_a, node_b):
                graph[node_a][node_b]["weight"] += 1
                graph[node_a][node_b]["shared_papers"] += 1
            else:
                graph.add_edge(node_a, node_b, weight=1, shared_papers=1)
            edge_updates += 1

    elapsed = round(time.perf_counter() - started, 4)
    return graph, {
        "build_seconds": elapsed,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "edge_updates": edge_updates,
    }


def save_graph_and_summary(
    graph,
    output_dir: str | Path,
    graph_name: str,
    graph_type: str,
    source_parquet: str | Path | None = None,
    load_meta: dict[str, Any] | None = None,
    build_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gexf_path = output_dir / f"{graph_name}.gexf"
    summary_path = output_dir / f"{graph_name}_summary.json"

    write_started = time.perf_counter()
    nx.write_gexf(graph, gexf_path)
    write_seconds = round(time.perf_counter() - write_started, 4)

    density = nx.density(graph) if graph.number_of_nodes() > 1 else 0.0
    load_seconds = float((load_meta or {}).get("load_seconds", 0.0))
    build_seconds = float((build_meta or {}).get("build_seconds", 0.0))
    total_seconds = round(load_seconds + build_seconds + write_seconds, 4)

    summary = {
        "graph_type": graph_type,
        "is_directed": bool(graph.is_directed()),
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": density,
        "gexf_file": str(gexf_path.resolve()),
        "source_parquet": str(Path(source_parquet).resolve()) if source_parquet else None,
        "load_seconds": load_seconds,
        "build_seconds": build_seconds,
        "write_seconds": write_seconds,
        "total_seconds": total_seconds,
        "load_meta": load_meta or {},
        "build_meta": build_meta or {},
    }
    summary_path.write_text(json.dumps(summary, indent=4, ensure_ascii=False), encoding="utf-8")
    return summary
