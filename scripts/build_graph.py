from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.graph_builder import append_records_to_graph, build_graph
from citation_graphs.io import load_json
from citation_graphs.utils import normalize_network_type


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or update citation/collaboration graphs.")
    parser.add_argument("--input", required=True, help="Input JSON file")
    parser.add_argument(
        "--network-type",
        required=True,
        help="Graph type to build: citation/collaboration or 1/2",
    )
    parser.add_argument("--gexf-output", required=True, help="Output GEXF path")
    parser.add_argument("--image-output", help="Optional output image path")
    parser.add_argument("--existing-graph", help="Optional existing GEXF graph to update")
    return parser.parse_args()


def save_graph_image(graph: nx.Graph, output_path: str | Path, title: str) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(graph, seed=42)

    nx.draw_networkx_nodes(graph, pos, node_size=8, alpha=0.7)
    nx.draw_networkx_edges(graph, pos, alpha=0.3)
    plt.axis("off")
    plt.title(title)
    plt.savefig(output_path, dpi=300, format=output_path.suffix.replace(".", "") or "png")
    plt.close()


def main() -> None:
    args = parse_args()

    records = load_json(args.input)
    network_type = normalize_network_type(args.network_type)

    if args.existing_graph:
        existing_graph = nx.read_gexf(args.existing_graph)
        graph = append_records_to_graph(existing_graph, records, network_type)
    else:
        graph = build_graph(records, network_type)

    gexf_output = Path(args.gexf_output)
    gexf_output.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(graph, gexf_output)
    print(f"Saved graph to: {gexf_output}")

    if args.image_output:
        save_graph_image(graph, args.image_output, f"{network_type.capitalize()} graph")
        print(f"Saved graph image to: {args.image_output}")


if __name__ == "__main__":
    main()