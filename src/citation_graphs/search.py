from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import duckdb


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unknown"


def resolve_search_input(
    source_mode: str,
    normalized_dir: str | Path | None = None,
    subset_path: str | Path | None = None,
    sample_path: str | Path | None = None,
) -> Path:
    source_mode = (source_mode or "").strip().lower()

    if source_mode == "normalized":
        if normalized_dir is None:
            raise ValueError("normalized_dir is required when source_mode='normalized'")
        path = Path(normalized_dir)
    elif source_mode == "subset":
        if subset_path is None:
            raise ValueError("subset_path is required when source_mode='subset'")
        path = Path(subset_path)
    elif source_mode == "sample":
        if sample_path is None:
            raise ValueError("sample_path is required when source_mode='sample'")
        path = Path(sample_path)
    else:
        raise ValueError(f"Unsupported source_mode: {source_mode}")

    if not path.exists():
        raise FileNotFoundError(f"Search input not found: {path}")

    return path


def _readable_input(path: Path) -> str:
    path = Path(path)
    if path.is_dir():
        return str(path / "**" / "*.parquet")
    return str(path)


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


def search_author_records(
    input_path: str | Path,
    author_query: str,
    limit: int = 200,
) -> list[dict[str, Any]]:
    return search_author_records_multi(
        input_path=input_path,
        author_queries=[author_query],
        limit=limit,
        match_mode="or",
    )


def search_author_records_multi(
    input_path: str | Path,
    author_queries: list[str],
    limit: int = 200,
    match_mode: str = "or",
) -> list[dict[str, Any]]:
    cleaned_queries = [q.strip() for q in author_queries if q and q.strip()]
    if not cleaned_queries:
        raise ValueError("author_queries cannot be empty")

    input_path = Path(input_path)
    source = _readable_input(input_path)
    match_mode = (match_mode or "or").strip().lower()
    if match_mode not in {"or", "and"}:
        raise ValueError("match_mode must be either 'or' or 'and'")

    conditions = []
    parameters: list[Any] = []

    for query in cleaned_queries:
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(author_names) AS t(author_name)
                WHERE lower(author_name) LIKE lower(?)
            )
            """
        )
        parameters.append(f"%{query}%")

    joiner = " OR " if match_mode == "or" else " AND "
    where_clause = joiner.join(f"({condition.strip()})" for condition in conditions)

    query = f"""
    SELECT
        paper_id,
        title,
        year_clean,
        n_citation,
        lang,
        venue_name,
        fos,
        fos_count,
        "references" AS references_list,
        reference_count,
        author_ids,
        author_names,
        author_count
    FROM read_parquet('{source}')
    WHERE {where_clause}
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


def export_search_results_csv(
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
