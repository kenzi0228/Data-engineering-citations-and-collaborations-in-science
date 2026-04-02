from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.reporting import export_analysis_markdown_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a graph analysis JSON file to a Markdown report.")
    parser.add_argument("--input", required=True, help="Input analysis JSON path")
    parser.add_argument("--output", required=True, help="Output Markdown report path")
    parser.add_argument("--name", help="Optional custom analysis display name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = export_analysis_markdown_report(
        analysis_path=args.input,
        output_path=args.output,
        analysis_name=args.name,
    )
    print("Analysis report export completed.")
    print(result)


if __name__ == "__main__":
    main()
