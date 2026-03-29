from __future__ import annotations

import argparse
import sys
from pathlib import Path

import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.export import extract_top_nodes_from_graph
from citation_graphs.io import save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export top-ranked graph nodes.")
    parser.add_argument("--input", required=True, help="Input GEXF graph file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument(
        "--metric",
        default="degree",
        choices=["degree", "pagerank", "betweenness"],
        help="Ranking metric",
    )
    parser.add_argument("--top-n", type=int, default=100, help="Number of nodes to export")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    graph = nx.read_gexf(args.input)
    results = extract_top_nodes_from_graph(graph, metric=args.metric, top_n=args.top_n)
    save_json(results, args.output)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()