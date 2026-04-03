from __future__ import annotations

from citation_graphs.author_index import suggest_authors


def test_suggest_authors_empty_query_returns_empty() -> None:
    authors = ["Alice Doe", "Bob Ray"]
    assert suggest_authors(authors, "", limit=20) == []


def test_suggest_authors_word_match() -> None:
    authors = ["Ian McCulloh", "Kathleen M. Carley", "Alice Doe"]
    suggestions = suggest_authors(authors, "mcc", limit=20)
    assert "Ian McCulloh" in suggestions


def test_suggest_authors_starts_before_contains() -> None:
    authors = ["Ian McCulloh", "McCulloh Ian", "Zed Ian"]
    suggestions = suggest_authors(authors, "ian", limit=10)
    assert suggestions[0] == "Ian McCulloh"
