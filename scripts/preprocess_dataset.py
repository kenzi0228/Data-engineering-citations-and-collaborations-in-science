from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.io import list_json_files
from citation_graphs.preprocessing import preprocess_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess raw JSON dataset files.")
    parser.add_argument("--input", required=True, help="Input file or directory")
    parser.add_argument("--output", required=True, help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        output_file = output_dir / input_path.name
        preprocess_file(input_path, output_file)
        print(f"Saved: {output_file}")
        return

    if input_path.is_dir():
        files = list_json_files(input_path)
        for file_path in files:
            output_file = output_dir / file_path.name
            preprocess_file(file_path, output_file)
            print(f"Saved: {output_file}")
        return

    print("Invalid input path.")


if __name__ == "__main__":
    main()