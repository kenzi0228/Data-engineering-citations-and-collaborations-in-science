from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.insights import export_analysis_to_csvs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export graph analysis JSON results into CSV files.")
    parser.add_argument("--input", required=True, help="Path to the analysis JSON file")
    parser.add_argument("--output-dir", required=True, help="Directory where CSV files will be exported")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = export_analysis_to_csvs(args.input, args.output_dir)
    print("Analysis CSV export completed.")
    print(result)


if __name__ == "__main__":
    main()
