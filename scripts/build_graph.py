from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.graph_builder import build_graph_from_subset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build citation or collaboration graph from a filtered subset.")
    parser.add_argument("--input", required=True, help="Subset parquet file path")
    parser.add_argument("--output", required=True, help="Output directory for graph files")
    parser.add_argument(
        "--graph-type",
        required=True,
        choices=["citation", "collaboration"],
        help="Graph type to build",
    )
    parser.add_argument("--graph-name", required=True, help="Base name for generated graph files")
    parser.add_argument("--limit", type=int, help="Optional record limit for testing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    summary = build_graph_from_subset(
        parquet_path=args.input,
        output_dir=args.output,
        graph_name=args.graph_name,
        graph_type=args.graph_type,
        limit=args.limit,
    )

    print("Graph build completed.")
    print(summary)


if __name__ == "__main__":
    main()
