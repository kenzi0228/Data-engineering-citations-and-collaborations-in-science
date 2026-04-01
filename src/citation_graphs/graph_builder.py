from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import duckdb
import networkx as nx


INVALID_XML_RE = re.compile(
    "[" +
    "\x00-\x08" +
    "\x0B-\x0C" +
    "\x0E-\x1F" +
    "\uD800-\uDFFF" +
    "\uFFFE-\uFFFF" +
    "]"
)


def load_subset_records(
    parquet_path: str | Path,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    parquet_path = Path(parquet_path)
    con = duckdb.connect(database=":memory:")

    query = f"SELECT * FROM read_parquet('{parquet_path}')"
    if limit is not None:
        query += f" LIMIT {limit}"

    table = con.execute(query).fetch_arrow_table()
    con.close()

    return table.to_pylist()


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return []
        return []

    try:
        return list(value)
    except TypeError:
        return []


def _clean_xml_string(value: str) -> str:
    return INVALID_XML_RE.sub("", value)


def _sanitize_gexf_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return _clean_xml_string(value)

    if isinstance(value, list):
        return _clean_xml_string(json.dumps(value, ensure_ascii=False))

    if isinstance(value, dict):
        return _clean_xml_string(json.dumps(value, ensure_ascii=False))

    return _clean_xml_string(str(value))


def _sanitize_graph_for_gexf(graph: nx.Graph) -> nx.Graph:
    sanitized = graph.__class__()

    for node_id, attrs in graph.nodes(data=True):
        clean_node_id = _sanitize_gexf_value(node_id)
        clean_attrs = {key: _sanitize_gexf_value(value) for key, value in attrs.items()}
        sanitized.add_node(clean_node_id, **clean_attrs)

    for source, target, attrs in graph.edges(data=True):
        clean_source = _sanitize_gexf_value(source)
        clean_target = _sanitize_gexf_value(target)
        clean_attrs = {key: _sanitize_gexf_value(value) for key, value in attrs.items()}
        sanitized.add_edge(clean_source, clean_target, **clean_attrs)

    return sanitized


def build_citation_graph(records: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()

    for record in records:
        paper_id = record.get("paper_id")
        if not paper_id:
            continue

        graph.add_node(
            str(paper_id),
            title=record.get("title"),
            year=record.get("year_clean"),
            n_citation=record.get("n_citation"),
            lang=record.get("lang"),
            venue_name=record.get("venue_name"),
            fos_count=record.get("fos_count"),
            reference_count=record.get("reference_count"),
            author_count=record.get("author_count"),
        )

    for record in records:
        paper_id = record.get("paper_id")
        if not paper_id:
            continue

        paper_id = str(paper_id)
        references = _ensure_list(record.get("references"))

        for ref_id in references:
            if not ref_id:
                continue

            ref_id = str(ref_id)

            if ref_id not in graph:
                graph.add_node(
                    ref_id,
                    title="",
                    year="",
                    n_citation="",
                    lang="",
                    venue_name="",
                    fos_count="",
                    reference_count="",
                    author_count="",
                )

            graph.add_edge(ref_id, paper_id)

    return graph


def build_collaboration_graph(records: list[dict[str, Any]]) -> nx.Graph:
    graph = nx.Graph()

    for record in records:
        author_ids = _ensure_list(record.get("author_ids"))
        author_names = _ensure_list(record.get("author_names"))

        valid_authors: list[tuple[str, str]] = []
        for idx, author_id in enumerate(author_ids):
            if not author_id:
                continue

            author_id = str(author_id)
            author_name = author_names[idx] if idx < len(author_names) else ""
            author_name = str(author_name) if author_name is not None else ""

            if author_id not in graph:
                graph.add_node(author_id, name=author_name)

            valid_authors.append((author_id, author_name))

        for i in range(len(valid_authors)):
            for j in range(i + 1, len(valid_authors)):
                source_id, _ = valid_authors[i]
                target_id, _ = valid_authors[j]

                if graph.has_edge(source_id, target_id):
                    graph[source_id][target_id]["weight"] += 1
                else:
                    graph.add_edge(source_id, target_id, weight=1)

    return graph


def graph_summary(graph: nx.Graph, graph_type: str) -> dict[str, Any]:
    return {
        "graph_type": graph_type,
        "is_directed": graph.is_directed(),
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "density": nx.density(graph),
    }


def save_graph_outputs(
    graph: nx.Graph,
    output_dir: str | Path,
    graph_name: str,
    graph_type: str,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gexf_path = output_dir / f"{graph_name}_{graph_type}.gexf"
    summary_path = output_dir / f"{graph_name}_{graph_type}_summary.json"

    sanitized_graph = _sanitize_graph_for_gexf(graph)
    nx.write_gexf(sanitized_graph, gexf_path)

    summary = graph_summary(graph, graph_type)
    summary["gexf_file"] = str(gexf_path.resolve())

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    return summary


def build_graph_from_subset(
    parquet_path: str | Path,
    output_dir: str | Path,
    graph_name: str,
    graph_type: str,
    limit: int | None = None,
) -> dict[str, Any]:
    records = load_subset_records(parquet_path, limit=limit)

    if graph_type == "citation":
        graph = build_citation_graph(records)
    elif graph_type == "collaboration":
        graph = build_collaboration_graph(records)
    else:
        raise ValueError("graph_type must be 'citation' or 'collaboration'")

    summary = save_graph_outputs(
        graph=graph,
        output_dir=output_dir,
        graph_name=graph_name,
        graph_type=graph_type,
    )

    summary["source_parquet"] = str(Path(parquet_path).resolve())
    summary["records_loaded"] = len(records)
    summary["limit"] = limit

    summary_path = Path(output_dir) / f"{graph_name}_{graph_type}_summary.json"
    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    return summary
