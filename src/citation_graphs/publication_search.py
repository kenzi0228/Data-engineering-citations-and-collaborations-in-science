from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import duckdb

from citation_graphs.scan_strategy import (
    SEARCH_PUBLICATION_COLUMNS,
    build_duckdb_read_expression,
    resolve_partition_sources,
)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unknown"


def _safe_json_loads(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if text.startswith("[") or text.startswith("{"):
        try:
            return json.loads(text)
        except Exception:
            return value
    return value


def _parse_duckdb_list_string(text: str) -> list[str]:
    text = text.strip()
    if not (text.startswith("[") and text.endswith("]")):
        return [text] if text else []

    inner = text[1:-1].strip()
    if not inner:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass

    quoted_items = re.findall(r"'([^']*)'|\"([^\"]*)\"", inner)
    flattened = []
    for left, right in quoted_items:
        value = (left or right).strip()
        if value:
            flattened.append(value)

    if flattened:
        return flattened

    parts = [part.strip() for part in re.split(r"\s{2,}|\s*,\s*", inner) if part.strip()]
    return parts


def _flatten_list_like(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("[") and stripped.endswith("]"):
            return _parse_duckdb_list_string(stripped)
        return [stripped]

    value = _safe_json_loads(value)

    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_flatten_list_like(item))
        return out

    if isinstance(value, tuple):
        out = []
        for item in value:
            out.extend(_flatten_list_like(item))
        return out

    if hasattr(value, "tolist") and not isinstance(value, str):
        try:
            return _flatten_list_like(value.tolist())
        except Exception:
            pass

    return [value]


def _normalize_list(value: Any) -> list[Any]:
    flattened = _flatten_list_like(value)
    normalized = []
    for item in flattened:
        if item is None:
            continue
        if isinstance(item, str):
            item = item.strip()
            if not item or item.lower() == "nan":
                continue
        normalized.append(item)
    return normalized


def _clean_scalar(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "tolist") and not isinstance(value, str):
        try:
            value = value.tolist()
        except Exception:
            pass
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() == "nan":
            return None
        return stripped
    return value


def _row_to_python(row: dict[str, Any]) -> dict[str, Any]:
    converted = {}
    list_like_keys = {"author_names", "author_ids", "fos", "references_list"}

    for key, value in row.items():
        if key in list_like_keys:
            converted[key] = _normalize_list(value)
        else:
            converted[key] = _clean_scalar(value)

    if "references_list" in converted:
        converted["references"] = converted.pop("references_list")

    return converted


def search_publication_records(
    input_path: str | Path,
    title_query: str,
    limit: int = 200,
    start_year: int | None = None,
    end_year: int | None = None,
) -> list[dict[str, Any]]:
    title_query = (title_query or "").strip()
    if not title_query:
        raise ValueError("title_query cannot be empty")

    input_path = Path(input_path)
    resolved = resolve_partition_sources(
        input_path,
        start_year=start_year if input_path.is_dir() else None,
        end_year=end_year if input_path.is_dir() else None,
    )
    read_expr = build_duckdb_read_expression(resolved)
    if not read_expr:
        return []

    where_clauses = ["lower(title) LIKE lower(?)"]
    parameters: list[Any] = [f"%{title_query}%"]

    if input_path.is_file():
        if start_year is not None:
            where_clauses.append("year_clean >= ?")
            parameters.append(int(start_year))
        if end_year is not None:
            where_clauses.append("year_clean <= ?")
            parameters.append(int(end_year))

    select_columns = ",\n        ".join(
        [
            "paper_id",
            "title",
            "year_clean",
            "n_citation",
            "lang",
            "venue_name",
            "fos",
            "fos_count",
            '"references" AS references_list',
            "reference_count",
            "author_ids",
            "author_names",
            "author_count",
        ]
    )

    query = f"""
    SELECT
        {select_columns}
    FROM {read_expr}
    WHERE {' AND '.join(where_clauses)}
    ORDER BY year_clean DESC NULLS LAST, n_citation DESC NULLS LAST, title ASC
    LIMIT ?
    """
    parameters.append(int(limit))

    con = duckdb.connect(database=":memory:")
    try:
        rows = con.execute(query, parameters).fetchdf().to_dict(orient="records")
    finally:
        con.close()

    return [_row_to_python(row) for row in rows]


def export_publication_results_csv(
    rows: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized = {}
        for key, value in row.items():
            if isinstance(value, list):
                normalized[key] = " | ".join(str(item) for item in value)
            else:
                normalized[key] = value
        normalized_rows.append(normalized)

    fieldnames = sorted({key for row in normalized_rows for key in row.keys()})
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)

    return output_path
