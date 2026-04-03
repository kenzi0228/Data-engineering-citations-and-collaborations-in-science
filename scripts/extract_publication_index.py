from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.publication_index import extract_publication_index, save_publication_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a publication title index from parquet-based data.")
    parser.add_argument("--input", required=True, help="Input parquet file or directory")
    parser.add_argument("--output", required=True, help="Output JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    titles = extract_publication_index(args.input)
    output_path = save_publication_index(titles, args.output)

    result = {
        "input": args.input,
        "output": str(output_path),
        "count": len(titles),
    }

    print("Publication index extraction completed.")
    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
