from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.graph_analysis import analyze_graph, load_graph, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze one or more GEXF graph files and export JSON metrics."
    )
    parser.add_argument("--input", required=True, help="Path to a .gexf file or a directory")
    parser.add_argument("--output", default="outputs/metrics", help="Output directory")
    parser.add_argument("--top-n", type=int, default=5, help="Top N scores")
    return parser.parse_args()


def iter_gexf_files(input_path: Path) -> list[Path]:
    if input_path.is_file() and input_path.suffix.lower() == ".gexf":
        return [input_path]
    if input_path.is_dir():
        return sorted(input_path.glob("*.gexf"))
    return []


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = iter_gexf_files(input_path)
    if not files:
        print("No GEXF files found.")
        return

    for file_path in files:
        graph = load_graph(file_path)
        results = analyze_graph(graph, top_n=args.top_n)

        output_file = output_dir / f"{file_path.stem}_analysis.json"
        save_json(results, output_file)
        print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()