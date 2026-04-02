from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from citation_graphs.exceptions import MissingInputError


def _resolve_input_glob(input_path: str | Path) -> str:
    path = Path(input_path)
    if path.is_dir():
        return str(path / "**" / "*.parquet")
    return str(path)


def compute_data_quality_report(input_path: str | Path, top_n: int = 10) -> dict[str, Any]:
    path = Path(input_path)
    if not path.exists():
        raise MissingInputError(f"Input path not found: {path}")

    input_glob = _resolve_input_glob(path)
    con = duckdb.connect(database=":memory:")

    summary_query = f"""
        SELECT
            COUNT(*) AS row_count,
            MIN(year_clean) AS min_year,
            MAX(year_clean) AS max_year,
            AVG(CASE WHEN title IS NULL OR TRIM(title) = '' THEN 1 ELSE 0 END) AS missing_title_ratio,
            AVG(CASE WHEN author_count IS NULL OR author_count = 0 THEN 1 ELSE 0 END) AS zero_author_ratio,
            AVG(CASE WHEN reference_count IS NULL OR reference_count = 0 THEN 1 ELSE 0 END) AS zero_reference_ratio,
            AVG(CASE WHEN lang IS NULL OR TRIM(lang) = '' THEN 1 ELSE 0 END) AS missing_lang_ratio
        FROM read_parquet('{input_glob}', hive_partitioning=true)
    """
    summary_row = con.execute(summary_query).fetchone()

    years_query = f"""
        SELECT year_clean AS year, COUNT(*) AS row_count
        FROM read_parquet('{input_glob}', hive_partitioning=true)
        WHERE year_clean IS NOT NULL
        GROUP BY year_clean
        ORDER BY row_count DESC
        LIMIT {top_n}
    """
    years_rows = con.execute(years_query).fetchall()

    fos_query = f"""
        SELECT TRIM(f) AS fos_value, COUNT(*) AS row_count
        FROM read_parquet('{input_glob}', hive_partitioning=true),
             UNNEST(fos) AS t(f)
        WHERE f IS NOT NULL AND TRIM(f) <> ''
        GROUP BY TRIM(f)
        ORDER BY row_count DESC
        LIMIT {top_n}
    """
    fos_rows = con.execute(fos_query).fetchall()

    con.close()

    return {
        "input_path": str(path.resolve()),
        "summary": {
            "row_count": summary_row[0],
            "min_year": summary_row[1],
            "max_year": summary_row[2],
            "missing_title_ratio": float(summary_row[3] or 0.0),
            "zero_author_ratio": float(summary_row[4] or 0.0),
            "zero_reference_ratio": float(summary_row[5] or 0.0),
            "missing_lang_ratio": float(summary_row[6] or 0.0),
        },
        "top_years": [
            {"year": row[0], "row_count": row[1]}
            for row in years_rows
        ],
        "top_fos": [
            {"fos_value": row[0], "row_count": row[1]}
            for row in fos_rows
        ],
    }
