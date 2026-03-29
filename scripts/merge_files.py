from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.io import list_json_files, load_json, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge multiple JSON files into one.")
    parser.add_argument("--input", required=True, help="Input directory")
    parser.add_argument("--output", required=True, help="Output file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input)
    output_file = Path(args.output)

    merged_data = []
    for file_path in list_json_files(input_dir):
        data = load_json(file_path)
        if isinstance(data, list):
            merged_data.extend(data)

    save_json(merged_data, output_file)
    print(f"Saved merged file to: {output_file}")


if __name__ == "__main__":
    main()