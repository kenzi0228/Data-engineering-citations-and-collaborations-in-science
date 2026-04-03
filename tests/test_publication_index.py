from __future__ import annotations

from pathlib import Path

from citation_graphs.publication_index import (
    extract_publication_index,
    load_publication_index,
    save_publication_index,
    suggest_publications,
)


def test_extract_publication_index(mini_parquet: Path) -> None:
    titles = extract_publication_index(mini_parquet)
    assert len(titles) >= 1
    assert "Graph Analytics for Science" in titles


def test_save_and_load_publication_index(tmp_path: Path) -> None:
    output_path = tmp_path / "publication_index.json"
    save_publication_index(["Graph Analytics for Science", "Applied Collaboration Networks"], output_path)
    loaded = load_publication_index(output_path)
    assert "Graph Analytics for Science" in loaded
    assert "Applied Collaboration Networks" in loaded


def test_suggest_publications_empty_query_returns_empty() -> None:
    titles = ["Graph Analytics for Science", "Applied Collaboration Networks"]
    assert suggest_publications(titles, "", limit=20) == []


def test_suggest_publications_starts_before_contains() -> None:
    titles = ["Graph Analytics for Science", "Science of Graphs", "Applied Collaboration Networks"]
    suggestions = suggest_publications(titles, "graph", limit=10)
    assert suggestions[0] == "Graph Analytics for Science"


def test_suggest_publications_word_match() -> None:
    titles = ["Detecting Change in Longitudinal Social Networks", "Applied Collaboration Networks"]
    suggestions = suggest_publications(titles, "long", limit=10)
    assert "Detecting Change in Longitudinal Social Networks" in suggestions
