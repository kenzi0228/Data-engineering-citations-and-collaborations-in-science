from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.author_index import extract_author_index, save_author_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a distinct author index from parquet-based data.")
    parser.add_argument("--input", required=True, help="Input parquet file or normalized parquet directory")
    parser.add_argument("--output", required=True, help="Output JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    authors = extract_author_index(args.input)
    save_author_index(authors, args.output)

    result = {
        "input": str(Path(args.input).resolve()),
        "output": str(Path(args.output).resolve()),
        "author_count": len(authors),
    }
    print("Author index extraction completed.")
    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
