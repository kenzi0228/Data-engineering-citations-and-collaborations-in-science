from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mini_records(fixture_dir: Path) -> list[dict]:
    return json.loads((fixture_dir / "mini_records.json").read_text(encoding="utf-8"))


@pytest.fixture
def mini_parquet(tmp_path: Path, mini_records: list[dict]) -> Path:
    json_path = tmp_path / "mini_records.json"
    json_path.write_text(json.dumps(mini_records), encoding="utf-8")

    parquet_path = tmp_path / "mini_subset.parquet"
    con = duckdb.connect(database=":memory:")
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM read_json_auto('{json_path}')
        )
        TO '{parquet_path}'
        (FORMAT PARQUET)
        """
    )
    con.close()
    return parquet_path
