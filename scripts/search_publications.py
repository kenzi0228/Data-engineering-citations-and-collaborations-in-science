from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.publication_profile import build_publication_profile
from citation_graphs.publication_search import export_publication_results_csv, search_publication_records, slugify


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search publication records from parquet-based data.")
    parser.add_argument("--input", required=True, help="Input parquet file or normalized parquet directory")
    parser.add_argument("--title-query", required=True, help="Publication title query")
    parser.add_argument("--limit", type=int, default=200, help="Maximum rows")
    parser.add_argument("--output-csv", help="Optional output CSV path")
    parser.add_argument("--output-profile", help="Optional output profile JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    rows = search_publication_records(
        input_path=args.input,
        title_query=args.title_query,
        limit=args.limit,
    )
    profile = build_publication_profile(rows, title_query=args.title_query)

    output_csv = None
    output_profile = None

    if args.output_csv:
        output_csv = str(export_publication_results_csv(rows, args.output_csv))

    if args.output_profile:
        output_profile = Path(args.output_profile)
        output_profile.parent.mkdir(parents=True, exist_ok=True)
        output_profile.write_text(json.dumps(profile, indent=4, ensure_ascii=False), encoding="utf-8")
        output_profile = str(output_profile)

    result = {
        "title_query": args.title_query,
        "result_count": len(rows),
        "profile": profile,
        "output_csv": output_csv,
        "output_profile": output_profile,
    }

    print("Publication search completed.")
    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
