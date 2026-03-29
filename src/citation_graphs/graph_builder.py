from __future__ import annotations

from typing import Any

import networkx as nx


def _paper_attributes(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "year": str(record.get("year", "")),
        "title": str(record.get("title", "")),
        "fos": ", ".join(record.get("fos", [])) if isinstance(record.get("fos"), list) else "",
        "references": ", ".join(record.get("references", [])) if isinstance(record.get("references"), list) else "",
    }


def build_citation_graph(records: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()

    # Pass 1: add all known paper nodes
    for record in records:
        paper_id = record.get("_id")
        if not paper_id:
            continue
        graph.add_node(paper_id, **_paper_attributes(record))

    # Pass 2: add edges, regardless of input order
    for record in records:
        paper_id = record.get("_id")
        if not paper_id:
            continue

        references = record.get("references", [])
        if not isinstance(references, list):
            continue

        for ref_id in references:
            if not ref_id:
                continue
            if ref_id not in graph:
                graph.add_node(ref_id, title="", year="", fos="", references="")
            graph.add_edge(ref_id, paper_id)

    return graph


def build_collaboration_graph(records: list[dict[str, Any]]) -> nx.Graph:
    graph = nx.Graph()

    for record in records:
        paper_attrs = _paper_attributes(record)
        authors = record.get("authors", [])
        if not isinstance(authors, list):
            continue

        valid_authors: list[dict[str, Any]] = []
        for author in authors:
            if not isinstance(author, dict):
                continue
            author_id = author.get("_id")
            author_name = author.get("name")
            if not author_id:
                continue

            graph.add_node(
                author_id,
                name=str(author_name or "Unknown"),
                **paper_attrs,
            )
            valid_authors.append(author)

        for i in range(len(valid_authors)):
            for j in range(i + 1, len(valid_authors)):
                author_i = valid_authors[i].get("_id")
                author_j = valid_authors[j].get("_id")
                if not author_i or not author_j:
                    continue

                if graph.has_edge(author_i, author_j):
                    graph[author_i][author_j]["weight"] += 1
                else:
                    graph.add_edge(author_i, author_j, weight=1)

    return graph


def build_graph(records: list[dict[str, Any]], network_type: str) -> nx.Graph:
    if network_type == "citation":
        return build_citation_graph(records)
    if network_type == "collaboration":
        return build_collaboration_graph(records)
    raise ValueError("network_type must be 'citation' or 'collaboration'")


def append_records_to_graph(
    graph: nx.Graph, records: list[dict[str, Any]], network_type: str
) -> nx.Graph:
    if network_type == "citation":
        new_graph = build_citation_graph(records)
    elif network_type == "collaboration":
        new_graph = build_collaboration_graph(records)
    else:
        raise ValueError("network_type must be 'citation' or 'collaboration'")

    merged_graph = nx.compose(graph, new_graph)
    return merged_graph