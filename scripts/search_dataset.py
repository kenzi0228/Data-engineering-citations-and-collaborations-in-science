from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.author_profile import build_author_profile
from citation_graphs.search import export_search_results_csv, search_author_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search author records inside normalized, subset, or sample parquet data.")
    parser.add_argument("--input", required=True, help="Path to parquet file or normalized parquet directory")
    parser.add_argument("--author-query", required=True, help="Author name query")
    parser.add_argument("--limit", type=int, default=200, help="Maximum number of rows to return")
    parser.add_argument("--output-csv", help="Optional CSV export path")
    parser.add_argument("--output-profile", help="Optional JSON profile export path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    rows = search_author_records(
        input_path=args.input,
        author_query=args.author_query,
        limit=args.limit,
    )
    profile = build_author_profile(rows, author_query=args.author_query)

    if args.output_csv:
        export_search_results_csv(rows, args.output_csv)

    if args.output_profile:
        output_profile = Path(args.output_profile)
        output_profile.parent.mkdir(parents=True, exist_ok=True)
        output_profile.write_text(json.dumps(profile, indent=4, ensure_ascii=False), encoding="utf-8")

    print("Author search completed.")
    print(json.dumps(
        {
            "author_query": args.author_query,
            "result_count": len(rows),
            "profile": profile,
            "output_csv": args.output_csv,
            "output_profile": args.output_profile,
        },
        indent=4,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
