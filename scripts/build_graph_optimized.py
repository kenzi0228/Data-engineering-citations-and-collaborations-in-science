from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.graph_build_optimized import (
    build_citation_graph,
    build_collaboration_graph,
    load_graph_build_rows,
    save_graph_and_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build optimized citation or collaboration graph from parquet-based data.")
    parser.add_argument("--input", required=True, help="Input parquet file or directory")
    parser.add_argument("--graph-type", choices=["citation", "collaboration"], required=True, help="Graph type to build")
    parser.add_argument("--output-dir", required=True, help="Output graph directory")
    parser.add_argument("--graph-name", required=True, help="Graph file base name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_dir = Path(args.output_dir)
    gexf_path = output_dir / f"{args.graph_name}.gexf"
    summary_path = output_dir / f"{args.graph_name}_summary.json"

    if not args.overwrite and (gexf_path.exists() or summary_path.exists()):
        raise FileExistsError(f"Graph output already exists for name: {args.graph_name}")

    if args.overwrite:
        if gexf_path.exists():
            gexf_path.unlink()
        if summary_path.exists():
            summary_path.unlink()

    rows, load_meta = load_graph_build_rows(args.input)

    if args.graph_type == "citation":
        graph, build_meta = build_citation_graph(rows)
        graph_type_name = "optimized_citation"
    else:
        graph, build_meta = build_collaboration_graph(rows)
        graph_type_name = "optimized_collaboration"

    summary = save_graph_and_summary(
        graph,
        output_dir=output_dir,
        graph_name=args.graph_name,
        graph_type=graph_type_name,
        source_parquet=args.input,
        load_meta=load_meta,
        build_meta=build_meta,
    )

    print("Optimized graph build completed.")
    print(json.dumps(summary, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
