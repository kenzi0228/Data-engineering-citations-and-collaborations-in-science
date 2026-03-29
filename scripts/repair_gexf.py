from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.graph_cleaning import repair_gexf_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair malformed GEXF/XML files.")
    parser.add_argument("--input", required=True, help="Input GEXF file")
    parser.add_argument("--output", required=True, help="Output repaired GEXF file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repair_gexf_file(args.input, args.output)
    print(f"Saved repaired GEXF to: {args.output}")


if __name__ == "__main__":
    main()