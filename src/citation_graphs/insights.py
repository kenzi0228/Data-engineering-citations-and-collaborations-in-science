from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_analysis_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_csv(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        with output_path.open("w", encoding="utf-8", newline="") as file:
            file.write("")
        return

    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_analysis_to_csvs(analysis_path: str | Path, output_dir: str | Path) -> dict[str, str]:
    analysis = load_analysis_json(analysis_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exported: dict[str, str] = {}

    pagerank_rows = analysis.get("pagerank", [])
    degree_rows = analysis.get("centralities", {}).get("degree", [])
    closeness_rows = analysis.get("centralities", {}).get("closeness", [])
    betweenness_rows = analysis.get("centralities", {}).get("betweenness", [])
    communities_rows = analysis.get("communities", {}).get("largest_communities", [])

    files = {
        "pagerank": output_dir / "pagerank.csv",
        "degree": output_dir / "degree.csv",
        "closeness": output_dir / "closeness.csv",
        "betweenness": output_dir / "betweenness.csv",
        "communities": output_dir / "communities.csv",
    }

    payloads = {
        "pagerank": pagerank_rows,
        "degree": degree_rows,
        "closeness": closeness_rows,
        "betweenness": betweenness_rows,
        "communities": communities_rows,
    }

    for key, path in files.items():
        _write_csv(payloads[key], path)
        exported[key] = str(path.resolve())

    return exported
