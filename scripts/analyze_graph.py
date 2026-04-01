from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.graph_analysis import analyze_graph, load_graph, save_analysis_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a GEXF graph and export JSON metrics.")
    parser.add_argument("--input", required=True, help="Path to the input GEXF file")
    parser.add_argument("--output", required=True, help="Path to the output JSON file")
    parser.add_argument("--top-n", type=int, default=10, help="Top N results for rankings")
    parser.add_argument(
        "--exact-betweenness",
        action="store_true",
        help="Use exact betweenness centrality instead of approximation",
    )
    parser.add_argument(
        "--betweenness-sample-k",
        type=int,
        default=200,
        help="Sample size for approximate betweenness",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    graph = load_graph(args.input)

    results = analyze_graph(
        graph,
        top_n=args.top_n,
        approximate_betweenness=not args.exact_betweenness,
        betweenness_sample_k=args.betweenness_sample_k,
    )

    save_analysis_results(results, args.output)

    print("Graph analysis completed.")
    print(f"Saved analysis to: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
