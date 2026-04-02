from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.filtering import create_subset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create filtered subsets from normalized parquet data.")
    parser.add_argument("--input", required=True, help="Normalized parquet root directory")
    parser.add_argument("--output", required=True, help="Subset output root directory")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["year", "range", "fos", "year_fos"],
        help="Filtering mode",
    )
    parser.add_argument("--subset-name", required=True, help="Name of the subset to create")
    parser.add_argument("--year", type=int, help="Year value")
    parser.add_argument("--start-year", type=int, help="Start year")
    parser.add_argument("--end-year", type=int, help="End year")
    parser.add_argument("--fos-values", nargs="*", default=[], help="Exact Field of Study values to match")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing subset directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    summary = create_subset(
        input_dir=args.input,
        output_dir=args.output,
        subset_name=args.subset_name,
        mode=args.mode,
        year=args.year,
        start_year=args.start_year,
        end_year=args.end_year,
        fos_values=args.fos_values,
        overwrite=args.overwrite,
    )

    print("Subset creation completed.")
    print(summary)


if __name__ == "__main__":
    main()
