from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Generator

import pyarrow as pa
import pyarrow.parquet as pq


NUMBERINT_PATTERN = re.compile(r"NumberInt\((\-?\d+)\)")


def normalize_non_standard_json_text(text: str) -> str:
    return NUMBERINT_PATTERN.sub(r"\1", text)


def detect_json_array(file_path: str | Path, chunk_size: int = 8192) -> bool:
    path = Path(file_path)
    with path.open("r", encoding="utf-8", errors="ignore") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                return False
            for char in chunk:
                if not char.isspace():
                    return char == "["
    return False


def stream_json_objects_from_array(
    file_path: str | Path,
    chunk_size: int = 65536,
) -> Generator[dict[str, Any], None, None]:
    path = Path(file_path)

    in_string = False
    escape = False
    depth = 0
    started = False
    buffer: list[str] = []

    with path.open("r", encoding="utf-8", errors="ignore") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break

            for char in chunk:
                if not started:
                    if char == "{":
                        started = True
                        depth = 1
                        buffer = ["{"]
                        in_string = False
                        escape = False
                    continue

                buffer.append(char)

                if in_string:
                    if escape:
                        escape = False
                    elif char == "\\":
                        escape = True
                    elif char == '"':
                        in_string = False
                    continue

                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        raw_object = "".join(buffer)
                        buffer = []
                        started = False

                        normalized = normalize_non_standard_json_text(raw_object)
                        try:
                            parsed = json.loads(normalized)
                            if isinstance(parsed, dict):
                                yield parsed
                        except json.JSONDecodeError:
                            continue


def safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_year(year_raw: int | None, min_year: int = 1800, max_year: int = 2026) -> int | None:
    if year_raw is None:
        return None
    if min_year <= year_raw <= max_year:
        return year_raw
    return None


def simplify_authors(authors: Any) -> tuple[list[str], list[str], str, int]:
    if not isinstance(authors, list):
        return [], [], "[]", 0

    simplified: list[dict[str, str | None]] = []
    author_ids: list[str] = []
    author_names: list[str] = []

    for author in authors:
        if not isinstance(author, dict):
            continue

        author_id = safe_str(author.get("_id"))
        author_name = safe_str(author.get("name"))

        simplified.append(
            {
                "_id": author_id,
                "name": author_name,
            }
        )

        if author_id:
            author_ids.append(author_id)
        if author_name:
            author_names.append(author_name)

    return author_ids, author_names, json.dumps(simplified, ensure_ascii=False), len(simplified)


def simplify_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(v) for v in values if v is not None and str(v).strip() != ""]


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    paper_id = safe_str(record.get("_id"))
    title = safe_str(record.get("title"))

    year_raw = safe_int(record.get("year"))
    year_clean = clean_year(year_raw)
    year_partition = str(year_clean) if year_clean is not None else "unknown"

    n_citation = safe_int(record.get("n_citation"))
    lang = safe_str(record.get("lang"))
    doi = safe_str(record.get("doi"))

    venue = record.get("venue", {})
    if not isinstance(venue, dict):
        venue = {}

    venue_id = safe_str(venue.get("_id"))
    venue_name = safe_str(venue.get("name_d"))
    venue_raw = safe_str(venue.get("raw"))

    author_ids, author_names, authors_json, author_count = simplify_authors(record.get("authors"))
    fos = simplify_string_list(record.get("fos"))
    references = simplify_string_list(record.get("references"))

    return {
        "paper_id": paper_id,
        "title": title,
        "year_raw": year_raw,
        "year_clean": year_clean,
        "year_partition": year_partition,
        "author_ids": author_ids,
        "author_names": author_names,
        "author_count": author_count,
        "authors_json": authors_json,
        "fos": fos,
        "fos_count": len(fos),
        "references": references,
        "reference_count": len(references),
        "n_citation": n_citation,
        "lang": lang,
        "venue_id": venue_id,
        "venue_name": venue_name,
        "venue_raw": venue_raw,
        "doi": doi,
    }


def write_parquet_batch(records: list[dict[str, Any]], output_dir: str | Path) -> None:
    if not records:
        return

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pylist(records)

    pq.write_to_dataset(
        table,
        root_path=str(output_path),
        partition_cols=["year_partition"],
        basename_template=f"part-{uuid.uuid4()}-{{i}}.parquet",
    )


def normalize_json_array_to_parquet(
    input_path: str | Path,
    output_dir: str | Path,
    batch_size: int = 5000,
    overwrite: bool = False,
    min_year: int = 1800,
    max_year: int = 2026,
) -> dict[str, Any]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if overwrite and output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    if not detect_json_array(input_path):
        raise ValueError("The input file does not appear to be a JSON array.")

    total_records = 0
    failed_records = 0
    written_batches = 0
    unknown_year_records = 0
    batch: list[dict[str, Any]] = []

    for raw_record in stream_json_objects_from_array(input_path):
        try:
            normalized = normalize_record(raw_record)

            year_raw = normalized["year_raw"]
            year_clean = normalized["year_clean"]
            if year_raw is not None and year_clean is None:
                unknown_year_records += 1

            batch.append(normalized)
            total_records += 1

            if len(batch) >= batch_size:
                write_parquet_batch(batch, output_dir)
                written_batches += 1
                batch = []
                print(f"[normalize] written_batches={written_batches} total_records={total_records}")
        except Exception:
            failed_records += 1

    if batch:
        write_parquet_batch(batch, output_dir)
        written_batches += 1

    summary = {
        "input_file": str(input_path.resolve()),
        "output_dir": str(output_dir.resolve()),
        "total_records_written": total_records,
        "failed_records": failed_records,
        "written_batches": written_batches,
        "batch_size": batch_size,
        "partition_column": "year_partition",
        "year_cleaning": {
            "min_year": min_year,
            "max_year": max_year,
            "records_with_invalid_year_moved_to_unknown": unknown_year_records,
        },
    }

    summary_path = output_dir / "_normalization_summary.json"
    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    return summary
