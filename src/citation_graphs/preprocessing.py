from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from citation_graphs.io import load_json, save_json


NUMBERINT_PATTERN = re.compile(r"NumberInt\((\d+)\)")


KEEP_KEYS = {"_id", "title", "authors", "year", "fos", "references"}


def replace_numberint_tokens_in_text(text: str) -> str:
    return NUMBERINT_PATTERN.sub(r"\1", text)


def fix_json_brackets_in_text(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("["):
        stripped = "[" + stripped
    if not stripped.endswith("]"):
        stripped = stripped + "]"
    return stripped


def preprocess_raw_json_text(raw_text: str) -> str:
    text = replace_numberint_tokens_in_text(raw_text)
    text = fix_json_brackets_in_text(text)
    return text


def keep_required_fields(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned_records: list[dict[str, Any]] = []
    for record in records:
        cleaned_records.append({key: record[key] for key in KEEP_KEYS if key in record})
    return cleaned_records


def preprocess_file(input_path: str | Path, output_path: str | Path) -> None:
    input_path = Path(input_path)
    raw_text = input_path.read_text(encoding="utf-8")
    processed_text = preprocess_raw_json_text(raw_text)

    temp_path = input_path.with_suffix(".tmp.json")
    temp_path.write_text(processed_text, encoding="utf-8")

    data = load_json(temp_path)
    if isinstance(data, dict):
        data = [data]

    cleaned_data = keep_required_fields(data)
    save_json(cleaned_data, output_path)

    temp_path.unlink(missing_ok=True)