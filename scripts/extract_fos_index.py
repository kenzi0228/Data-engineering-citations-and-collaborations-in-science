from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.fos_index import build_fos_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract and persist distinct FOS values from normalized parquet.")
    parser.add_argument("--input", required=True, help="Normalized parquet root directory")
    parser.add_argument("--output", required=True, help="Output JSON path for the FOS index")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_fos_index(args.input, args.output)
    print("FOS index extraction completed.")
    print(result)


if __name__ == "__main__":
    main()
