from __future__ import annotations

from typing import Any


def search_term_in_records(records: list[dict[str, Any]], term: str) -> list[dict[str, Any]]:
    term_lower = term.lower()
    results: list[dict[str, Any]] = []

    for record in records:
        record_id = record.get("_id")
        for key, value in record.items():
            if isinstance(value, str) and term_lower in value.lower():
                results.append(
                    {
                        "record_id": record_id,
                        "field": key,
                        "value": value,
                    }
                )
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and term_lower in item.lower():
                        results.append(
                            {
                                "record_id": record_id,
                                "field": key,
                                "value": item,
                            }
                        )
    return results