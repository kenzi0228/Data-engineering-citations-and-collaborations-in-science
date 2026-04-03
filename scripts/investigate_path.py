from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.path_finder import investigate_path_between_nodes, load_graph, save_path_investigation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Investigate shortest path connectivity between two nodes in a graph.")
    parser.add_argument("--input", required=True, help="Input GEXF graph path")
    parser.add_argument("--source", required=True, help="Source node id")
    parser.add_argument("--target", required=True, help="Target node id")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--max-paths", type=int, default=5, help="Maximum number of shortest paths to return")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    graph = load_graph(args.input)
    result = investigate_path_between_nodes(
        graph,
        source_node_id=args.source,
        target_node_id=args.target,
        max_paths=args.max_paths,
    )
    save_path_investigation(result, args.output)

    print("Path investigation completed.")
    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
