from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.sample_data import extract_sample_subset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a small sample parquet dataset from an existing subset parquet.")
    parser.add_argument("--input", required=True, help="Input subset parquet")
    parser.add_argument("--output", required=True, help="Output sample parquet")
    parser.add_argument("--metadata", required=True, help="Output sample metadata JSON")
    parser.add_argument("--row-limit", type=int, default=1000, help="Maximum number of rows to keep")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = extract_sample_subset(
        input_parquet=args.input,
        output_parquet=args.output,
        output_metadata=args.metadata,
        row_limit=args.row_limit,
    )
    print("Sample dataset extraction completed.")
    print(result)


if __name__ == "__main__":
    main()
