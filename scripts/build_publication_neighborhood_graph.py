from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.publication_graphs import build_publication_neighborhood_graph_from_input
from citation_graphs.publication_search import slugify


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a publication citation neighborhood graph from parquet-based data.")
    parser.add_argument("--input", required=True, help="Input parquet file or normalized parquet directory")
    parser.add_argument("--title-query", required=True, help="Publication title query")
    parser.add_argument("--output-dir", required=True, help="Graphs output directory")
    parser.add_argument("--graph-name", help="Optional graph name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite graph outputs if they exist")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    graph_name = args.graph_name or f"publication_{slugify(args.title_query)}_citation"
    output_dir = Path(args.output_dir)

    gexf_path = output_dir / f"{graph_name}.gexf"
    summary_path = output_dir / f"{graph_name}_summary.json"

    if not args.overwrite and (gexf_path.exists() or summary_path.exists()):
        raise FileExistsError(f"Graph output already exists for name: {graph_name}")

    if args.overwrite:
        if gexf_path.exists():
            gexf_path.unlink()
        if summary_path.exists():
            summary_path.unlink()

    result = build_publication_neighborhood_graph_from_input(
        input_path=args.input,
        title_query=args.title_query,
        output_dir=output_dir,
        graph_name=graph_name,
    )

    print("Publication neighborhood graph build completed.")
    print(result)


if __name__ == "__main__":
    main()
