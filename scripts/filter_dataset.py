from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.filtering import (
    filter_after_year,
    filter_before_year,
    filter_by_exact_year,
    filter_by_fos,
    filter_by_year_range,
)
from citation_graphs.io import list_json_files, load_json, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter JSON dataset files.")
    parser.add_argument("--input", required=True, help="Input directory containing JSON files")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["year", "range", "before", "after", "fos"],
        help="Filtering mode",
    )
    parser.add_argument("--year", type=int, help="Year value")
    parser.add_argument("--start-year", type=int, help="Start year")
    parser.add_argument("--end-year", type=int, help="End year")
    parser.add_argument("--fos", nargs="*", help="FOS values")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = list_json_files(input_dir)

    for file_path in files:
        records = load_json(file_path)

        if args.mode == "year":
            filtered = filter_by_exact_year(records, args.year)
        elif args.mode == "range":
            filtered = filter_by_year_range(records, args.start_year, args.end_year)
        elif args.mode == "before":
            filtered = filter_before_year(records, args.year)
        elif args.mode == "after":
            filtered = filter_after_year(records, args.year)
        else:
            filtered = filter_by_fos(records, args.fos or [])

        output_file = output_dir / f"{file_path.stem}_filtered.json"
        save_json(filtered, output_file)
        print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()