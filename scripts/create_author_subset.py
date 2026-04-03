from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.ego_graphs import create_author_subset_from_input
from citation_graphs.search import slugify


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an author subset from parquet-based data.")
    parser.add_argument("--input", required=True, help="Input parquet file or normalized parquet directory")
    parser.add_argument("--author-query", required=True, help="Author query")
    parser.add_argument("--output-root", required=True, help="Output subsets root directory")
    parser.add_argument("--subset-name", help="Optional subset name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite target directory if it exists")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    subset_name = args.subset_name or f"author_{slugify(args.author_query)}"
    output_dir = Path(args.output_root) / subset_name

    if output_dir.exists() and not args.overwrite:
        raise FileExistsError(f"Subset directory already exists: {output_dir}")

    if output_dir.exists() and args.overwrite:
        import shutil
        shutil.rmtree(output_dir)

    result = create_author_subset_from_input(
        input_path=args.input,
        author_query=args.author_query,
        output_dir=output_dir,
    )

    print("Author subset creation completed.")
    print(result)


if __name__ == "__main__":
    main()
