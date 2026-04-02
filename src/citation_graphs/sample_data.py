from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from citation_graphs.exceptions import MissingInputError, InvalidConfigurationError


def extract_sample_subset(
    input_parquet: str | Path,
    output_parquet: str | Path,
    output_metadata: str | Path,
    row_limit: int = 1000,
) -> dict[str, Any]:
    input_parquet = Path(input_parquet)
    output_parquet = Path(output_parquet)
    output_metadata = Path(output_metadata)

    if not input_parquet.exists():
        raise MissingInputError(f"Sample source parquet not found: {input_parquet}")

    if row_limit <= 0:
        raise InvalidConfigurationError("row_limit must be > 0")

    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    output_metadata.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=":memory:")
    query = f"""
        COPY (
            SELECT *
            FROM read_parquet('{input_parquet}')
            LIMIT {row_limit}
        )
        TO '{output_parquet}'
        (FORMAT PARQUET)
    """
    con.execute(query)

    profile_query = f"""
        SELECT
            COUNT(*) AS row_count,
            MIN(year_clean) AS min_year,
            MAX(year_clean) AS max_year
        FROM read_parquet('{output_parquet}')
    """
    row_count, min_year, max_year = con.execute(profile_query).fetchone()
    con.close()

    metadata = {
        "source_parquet": str(input_parquet.resolve()),
        "sample_parquet": str(output_parquet.resolve()),
        "row_limit_requested": row_limit,
        "row_count": row_count,
        "min_year": min_year,
        "max_year": max_year,
    }

    with output_metadata.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    return metadata
