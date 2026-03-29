from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def load_json(file_path: str | Path) -> Any:
    with Path(file_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data: Any, file_path: str | Path) -> None:
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def list_json_files(directory: str | Path) -> list[Path]:
    return sorted(Path(directory).glob("*.json"))


def list_gexf_files(directory: str | Path) -> list[Path]:
    return sorted(Path(directory).glob("*.gexf"))