from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


NUMBERINT_PATTERN = re.compile(r"NumberInt\((\-?\d+)\)")


def estimate_file_metadata(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)
    return {
        "file_name": path.name,
        "file_path": str(path.resolve()),
        "file_size_bytes": path.stat().st_size,
        "file_size_gb": round(path.stat().st_size / (1024 ** 3), 3),
        "suffix": path.suffix.lower(),
    }


def _first_non_whitespace_char(file_path: str | Path, chunk_size: int = 8192) -> str | None:
    path = Path(file_path)
    with path.open("r", encoding="utf-8", errors="ignore") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                return None
            for char in chunk:
                if not char.isspace():
                    return char
    return None


def detect_json_structure(file_path: str | Path) -> str:
    first_char = _first_non_whitespace_char(file_path)

    if first_char == "[":
        return "json_array_non_standard_possible"
    if first_char == "{":
        return "json_lines_or_single_object_non_standard_possible"
    return "unknown"


def _safe_preview_value(value: Any, max_length: int = 300) -> Any:
    if isinstance(value, str):
        return value[:max_length]
    return value


def _normalize_non_standard_json_text(text: str) -> str:
    return NUMBERINT_PATTERN.sub(r"\1", text)


def _extract_first_json_objects_from_array(
    file_path: str | Path,
    max_records: int = 3,
    chunk_size: int = 65536,
) -> list[str]:
    path = Path(file_path)
    objects: list[str] = []

    in_string = False
    escape = False
    depth = 0
    started = False
    buffer: list[str] = []

    with path.open("r", encoding="utf-8", errors="ignore") as file:
        while len(objects) < max_records:
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
                        objects.append("".join(buffer))
                        started = False
                        buffer = []

                        if len(objects) >= max_records:
                            break

    return objects


def sample_raw_records(file_path: str | Path, max_records: int = 3) -> list[dict[str, Any]]:
    structure = detect_json_structure(file_path)
    samples: list[dict[str, Any]] = []

    if structure == "json_array_non_standard_possible":
        raw_objects = _extract_first_json_objects_from_array(file_path, max_records=max_records)

        for raw_object in raw_objects:
            normalized = _normalize_non_standard_json_text(raw_object)
            try:
                parsed = json.loads(normalized)
                if isinstance(parsed, dict):
                    samples.append(parsed)
            except json.JSONDecodeError:
                continue

        return samples

    if structure == "json_lines_or_single_object_non_standard_possible":
        path = Path(file_path)
        with path.open("r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                stripped = line.strip()
                if not stripped:
                    continue

                normalized = _normalize_non_standard_json_text(stripped)

                try:
                    parsed = json.loads(normalized)
                    if isinstance(parsed, dict):
                        samples.append(parsed)
                    if len(samples) >= max_records:
                        break
                except json.JSONDecodeError:
                    continue

        return samples

    return samples


def profile_record_schema(records: list[dict[str, Any]]) -> dict[str, Any]:
    field_stats: dict[str, dict[str, Any]] = {}

    for record in records:
        if not isinstance(record, dict):
            continue

        for key, value in record.items():
            if key not in field_stats:
                field_stats[key] = {
                    "occurrences": 0,
                    "observed_types": set(),
                    "sample_value": None,
                }

            field_stats[key]["occurrences"] += 1
            field_stats[key]["observed_types"].add(type(value).__name__)

            if field_stats[key]["sample_value"] is None:
                field_stats[key]["sample_value"] = _safe_preview_value(value)

    normalized_stats = {}
    for key, value in field_stats.items():
        normalized_stats[key] = {
            "occurrences": value["occurrences"],
            "observed_types": sorted(value["observed_types"]),
            "sample_value": value["sample_value"],
        }

    return {
        "num_sampled_records": len(records),
        "fields": normalized_stats,
        "field_count": len(normalized_stats),
    }


def build_raw_inspection_report(file_path: str | Path, max_records: int = 3) -> dict[str, Any]:
    metadata = estimate_file_metadata(file_path)
    structure = detect_json_structure(file_path)
    samples = sample_raw_records(file_path, max_records=max_records)
    schema_profile = profile_record_schema(samples)

    report = {
        "metadata": metadata,
        "detected_structure": structure,
        "sample_record_count": len(samples),
        "schema_profile": schema_profile,
        "non_standard_json_tokens_detected": True,
        "notes": [
            "The raw file appears to contain non-standard JSON tokens such as NumberInt(...).",
            "Inspection samples were parsed with temporary normalization only.",
            "The raw source file was not modified.",
        ],
    }

    return {
        "report": report,
        "samples": samples,
    }


def save_inspection_outputs(result: dict[str, Any], output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    profile_path = output_path / "raw_profile.json"
    samples_path = output_path / "raw_samples.json"

    with profile_path.open("w", encoding="utf-8") as file:
        json.dump(result["report"], file, indent=4, ensure_ascii=False)

    with samples_path.open("w", encoding="utf-8") as file:
        json.dump(result["samples"], file, indent=4, ensure_ascii=False)
