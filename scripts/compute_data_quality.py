from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.data_quality import compute_data_quality_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute a parquet data quality report.")
    parser.add_argument("--input", required=True, help="Input parquet file or parquet root directory")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--top-n", type=int, default=10, help="Top N values for years and FOS")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = compute_data_quality_report(args.input, top_n=args.top_n)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=4, ensure_ascii=False), encoding="utf-8")

    print("Data quality report completed.")
    print({"output": str(output_path.resolve())})


if __name__ == "__main__":
    main()
