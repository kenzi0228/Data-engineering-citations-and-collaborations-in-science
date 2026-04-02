from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import duckdb


def _normalized_glob(input_dir: str | Path) -> str:
    return str(Path(input_dir) / "**" / "*.parquet")


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def get_distinct_fos_values(input_dir: str | Path) -> list[str]:
    input_glob = _normalized_glob(input_dir)
    con = duckdb.connect(database=":memory:")

    query = f"""
        SELECT DISTINCT TRIM(f) AS fos_value
        FROM read_parquet('{input_glob}', hive_partitioning=true),
             UNNEST(fos) AS t(f)
        WHERE f IS NOT NULL
          AND TRIM(f) <> ''
        ORDER BY fos_value
    """

    rows = con.execute(query).fetchall()
    con.close()

    return [row[0] for row in rows if row[0]]


def build_where_clause(
    mode: str,
    year: int | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    fos_values: list[str] | None = None,
) -> str:
    clauses: list[str] = []
    fos_values = fos_values or []

    if mode == "year":
        if year is None:
            raise ValueError("--year is required for mode=year")
        clauses.append(f"year_clean = {year}")

    elif mode == "range":
        if start_year is None or end_year is None:
            raise ValueError("--start-year and --end-year are required for mode=range")
        clauses.append(f"year_clean BETWEEN {start_year} AND {end_year}")

    elif mode == "fos":
        if not fos_values:
            raise ValueError("--fos-values is required for mode=fos")

        fos_subclauses = []
        for fos in fos_values:
            fos_escaped = _escape_sql_string(fos.lower())
            fos_subclauses.append(
                f"EXISTS (SELECT 1 FROM UNNEST(fos) AS t(f) WHERE lower(f) = '{fos_escaped}')"
            )
        clauses.append("(" + " OR ".join(fos_subclauses) + ")")

    elif mode == "year_fos":
        if year is None:
            raise ValueError("--year is required for mode=year_fos")
        if not fos_values:
            raise ValueError("--fos-values is required for mode=year_fos")

        clauses.append(f"year_clean = {year}")

        fos_subclauses = []
        for fos in fos_values:
            fos_escaped = _escape_sql_string(fos.lower())
            fos_subclauses.append(
                f"EXISTS (SELECT 1 FROM UNNEST(fos) AS t(f) WHERE lower(f) = '{fos_escaped}')"
            )
        clauses.append("(" + " OR ".join(fos_subclauses) + ")")

    else:
        raise ValueError("Unsupported mode")

    if not clauses:
        return "1=1"

    return " AND ".join(clauses)


def create_subset(
    input_dir: str | Path,
    output_dir: str | Path,
    subset_name: str,
    mode: str,
    year: int | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    fos_values: list[str] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    input_glob = _normalized_glob(input_dir)
    subset_dir = Path(output_dir) / subset_name

    if overwrite and subset_dir.exists():
        shutil.rmtree(subset_dir)

    subset_dir.mkdir(parents=True, exist_ok=True)

    where_clause = build_where_clause(
        mode=mode,
        year=year,
        start_year=start_year,
        end_year=end_year,
        fos_values=fos_values,
    )

    con = duckdb.connect(database=":memory:")

    source_query = f"""
        SELECT *
        FROM read_parquet('{input_glob}', hive_partitioning=true)
        WHERE {where_clause}
    """

    count_query = f"SELECT COUNT(*) AS row_count FROM ({source_query}) AS q"
    row_count = con.execute(count_query).fetchone()[0]

    summary = {
        "subset_name": subset_name,
        "mode": mode,
        "row_count": row_count,
        "input_dir": str(Path(input_dir).resolve()),
        "output_dir": str(subset_dir.resolve()),
        "where_clause": where_clause,
        "parameters": {
            "year": year,
            "start_year": start_year,
            "end_year": end_year,
            "fos_values": fos_values or [],
        },
    }

    if row_count == 0:
        with (subset_dir / "_subset_summary.json").open("w", encoding="utf-8") as file:
            json.dump(summary, file, indent=4, ensure_ascii=False)

        con.close()
        return summary

    export_path = subset_dir / "data.parquet"

    export_query = f"""
        COPY (
            {source_query}
        )
        TO '{export_path}'
        (FORMAT PARQUET)
    """

    con.execute(export_query)

    preview_query = f"""
        SELECT
            COUNT(*) AS row_count,
            MIN(year_clean) AS min_year,
            MAX(year_clean) AS max_year
        FROM read_parquet('{export_path}')
    """
    row_count_check, min_year, max_year = con.execute(preview_query).fetchone()

    summary["data_file"] = str(export_path.resolve())
    summary["preview"] = {
        "min_year": min_year,
        "max_year": max_year,
    }
    summary["row_count"] = row_count_check

    with (subset_dir / "_subset_summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    con.close()
    return summary
