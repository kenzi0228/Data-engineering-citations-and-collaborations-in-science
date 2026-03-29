from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split a large JSON-like file into chunks.")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output-prefix", required=True, help="Output file prefix")
    parser.add_argument("--chunk-size", type=int, default=2 * 10**9, help="Chunk size in bytes")
    return parser.parse_args()


def split_json_file(input_path: str | Path, output_prefix: str | Path, chunk_size: int) -> None:
    input_path = Path(input_path)
    output_prefix = str(output_prefix)

    with input_path.open("r", encoding="utf-8") as big_file:
        file_count = 1
        current_file = open(f"{output_prefix}{file_count}.json", "w", encoding="utf-8")
        current_file.write("[")
        current_size = 0
        first_record = True

        for line in big_file:
            record_size = len(line.encode("utf-8"))

            if current_size + record_size > chunk_size:
                current_file.write("]")
                current_file.close()

                file_count += 1
                current_file = open(f"{output_prefix}{file_count}.json", "w", encoding="utf-8")
                current_file.write("[")
                current_size = 0
                first_record = True

            if not first_record:
                current_file.write(",\n")
            else:
                first_record = False

            current_file.write(line.strip())
            current_size += record_size

        current_file.write("]")
        current_file.close()


def main() -> None:
    args = parse_args()
    split_json_file(args.input, args.output_prefix, args.chunk_size)
    print("Splitting completed.")


if __name__ == "__main__":
    main()