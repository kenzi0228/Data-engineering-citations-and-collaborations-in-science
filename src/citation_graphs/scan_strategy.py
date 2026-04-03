from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_partition_sources(
    input_path: str | Path,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, Any]:
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    if input_path.is_file():
        return {
            "mode": "file",
            "sources": [str(input_path)],
            "files_scanned": 1,
            "partitions": [],
            "used_year_filter": False,
        }

    all_parquets = sorted(input_path.glob("**/*.parquet"))

    if start_year is None and end_year is None:
        return {
            "mode": "directory",
            "sources": [str(p) for p in all_parquets],
            "files_scanned": len(all_parquets),
            "partitions": [],
            "used_year_filter": False,
        }

    if start_year is not None and end_year is not None and start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")

    selected_dirs = []
    selected_files = []

    for child in sorted(input_path.iterdir()):
        if not child.is_dir():
            continue

        name = child.name
        if not name.startswith("year_partition="):
            continue

        year_str = name.replace("year_partition=", "")
        if not year_str.isdigit():
            continue

        year = int(year_str)
        if start_year is not None and year < start_year:
            continue
        if end_year is not None and year > end_year:
            continue

        selected_dirs.append(name)
        selected_files.extend(sorted(child.glob("*.parquet")))

    return {
        "mode": "partitioned_directory",
        "sources": [str(p) for p in selected_files],
        "files_scanned": len(selected_files),
        "partitions": selected_dirs,
        "used_year_filter": True,
    }


def build_duckdb_read_expression(resolved: dict[str, Any]) -> str:
    sources = resolved.get("sources", [])
    if not sources:
        return ""

    if len(sources) == 1:
        return f"read_parquet('{sources[0]}')"

    joined = ", ".join(f"'{source}'" for source in sources)
    return f"read_parquet([{joined}])"


def select_columns(all_columns: list[str], required_columns: list[str]) -> list[str]:
    available = set(all_columns)
    selected = [column for column in required_columns if column in available]
    return selected


SEARCH_AUTHOR_COLUMNS = [
    "paper_id",
    "title",
    "year_clean",
    "n_citation",
    "lang",
    "venue_name",
    "fos",
    "fos_count",
    "references",
    "reference_count",
    "author_ids",
    "author_names",
    "author_count",
]

SEARCH_PUBLICATION_COLUMNS = [
    "paper_id",
    "title",
    "year_clean",
    "n_citation",
    "lang",
    "venue_name",
    "fos",
    "fos_count",
    "references",
    "reference_count",
    "author_ids",
    "author_names",
    "author_count",
]

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
