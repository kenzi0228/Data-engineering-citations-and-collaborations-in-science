from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from citation_graphs.raw_inspection import build_raw_inspection_report, save_inspection_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a large raw JSON dataset safely.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the raw dataset file, e.g. data/raw/dblpv13.json",
    )
    parser.add_argument(
        "--output",
        default="outputs/inspection",
        help="Directory where inspection outputs will be saved",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=3,
        help="Number of sample records to inspect",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    result = build_raw_inspection_report(input_path, max_records=args.max_records)
    save_inspection_outputs(result, args.output)

    print("Inspection completed.")
    print(f"Profile saved to: {Path(args.output) / 'raw_profile.json'}")
    print(f"Samples saved to: {Path(args.output) / 'raw_samples.json'}")
    print(f"Detected structure: {result['report']['detected_structure']}")
    print(f"Sample record count: {result['report']['sample_record_count']}")


if __name__ == "__main__":
    main()
