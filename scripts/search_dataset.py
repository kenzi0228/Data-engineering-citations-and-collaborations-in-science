from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.io import list_json_files, load_json, save_json
from citation_graphs.search import search_term_in_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search a term in dataset JSON files.")
    parser.add_argument("--input", required=True, help="Input JSON directory")
    parser.add_argument("--term", required=True, help="Search term")
    parser.add_argument("--output", help="Optional JSON output file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input)

    all_results = {}

    for file_path in list_json_files(input_dir):
        records = load_json(file_path)
        results = search_term_in_records(records, args.term)
        if results:
            all_results[file_path.name] = results

    if args.output:
        save_json(all_results, args.output)
        print(f"Saved: {args.output}")
    else:
        for filename, matches in all_results.items():
            print(f"\n{filename}")
            for match in matches[:20]:
                print(match)


if __name__ == "__main__":
    main()