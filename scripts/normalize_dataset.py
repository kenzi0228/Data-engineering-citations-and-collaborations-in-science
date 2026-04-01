from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.normalization import normalize_json_array_to_parquet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize a large non-standard JSON array dataset into partitioned Parquet."
    )
    parser.add_argument("--input", required=True, help="Path to the raw JSON dataset")
    parser.add_argument("--output", required=True, help="Output directory for normalized parquet files")
    parser.add_argument("--batch-size", type=int, default=5000, help="Number of records per write batch")
    parser.add_argument("--overwrite", action="store_true", help="Delete output directory before writing")
    parser.add_argument("--min-year", type=int, default=1800, help="Minimum valid year")
    parser.add_argument("--max-year", type=int, default=2026, help="Maximum valid year")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    summary = normalize_json_array_to_parquet(
        input_path=args.input,
        output_dir=args.output,
        batch_size=args.batch_size,
        overwrite=args.overwrite,
        min_year=args.min_year,
        max_year=args.max_year,
    )

    print("Normalization completed.")
    print(summary)


if __name__ == "__main__":
    main()
