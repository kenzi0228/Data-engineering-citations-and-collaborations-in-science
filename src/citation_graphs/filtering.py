from __future__ import annotations

from typing import Any


def filter_by_exact_year(records: list[dict[str, Any]], year: int) -> list[dict[str, Any]]:
    return [record for record in records if record.get("year") == year]


def filter_by_year_range(
    records: list[dict[str, Any]], start_year: int, end_year: int
) -> list[dict[str, Any]]:
    return [
        record for record in records
        if isinstance(record.get("year"), int) and start_year <= record["year"] <= end_year
    ]


def filter_before_year(records: list[dict[str, Any]], year: int) -> list[dict[str, Any]]:
    return [
        record for record in records
        if isinstance(record.get("year"), int) and record["year"] < year
    ]


def filter_after_year(records: list[dict[str, Any]], year: int) -> list[dict[str, Any]]:
    return [
        record for record in records
        if isinstance(record.get("year"), int) and record["year"] > year
    ]


def filter_by_fos(records: list[dict[str, Any]], fos_terms: list[str]) -> list[dict[str, Any]]:
    fos_terms_normalized = {term.lower().strip() for term in fos_terms}

    filtered: list[dict[str, Any]] = []
    for record in records:
        fos_values = record.get("fos", [])
        if not isinstance(fos_values, list):
            continue

        normalized_fos = {str(item).lower().strip() for item in fos_values}
        if normalized_fos & fos_terms_normalized:
            filtered.append(record)

    return filtered


def extract_unique_fos(records: list[dict[str, Any]]) -> list[str]:
    unique_values: set[str] = set()
    for record in records:
        fos_values = record.get("fos", [])
        if isinstance(fos_values, list):
            for value in fos_values:
                unique_values.add(str(value))
    return sorted(unique_values)


def extract_unique_organizations(records: list[dict[str, Any]]) -> list[str]:
    unique_orgs: set[str] = set()

    for record in records:
        authors = record.get("authors", [])
        if not isinstance(authors, list):
            continue

        for author in authors:
            if not isinstance(author, dict):
                continue

            org = author.get("org")
            if org:
                unique_orgs.add(str(org))

            orgs = author.get("orgs")
            if isinstance(orgs, list):
                for item in orgs:
                    unique_orgs.add(str(item))

    return sorted(unique_orgs)