from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.multi_author import build_multi_author_slug, create_multi_author_subset_from_input


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a multi-author subset from parquet-based data.")
    parser.add_argument("--input", required=True, help="Input parquet file or normalized parquet directory")
    parser.add_argument("--authors", nargs="+", required=True, help="One or more author queries")
    parser.add_argument("--match-mode", choices=["or", "and"], default="or", help="Author matching mode")
    parser.add_argument("--output-root", required=True, help="Output subsets root directory")
    parser.add_argument("--subset-name", help="Optional subset name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite target directory if it exists")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    subset_name = args.subset_name or build_multi_author_slug(args.authors, args.match_mode)
    output_dir = Path(args.output_root) / subset_name

    if output_dir.exists() and not args.overwrite:
        raise FileExistsError(f"Subset directory already exists: {output_dir}")

    if output_dir.exists() and args.overwrite:
        shutil.rmtree(output_dir)

    result = create_multi_author_subset_from_input(
        input_path=args.input,
        author_queries=args.authors,
        match_mode=args.match_mode,
        output_dir=output_dir,
    )

    print("Multi-author subset creation completed.")
    print(result)


if __name__ == "__main__":
    main()
