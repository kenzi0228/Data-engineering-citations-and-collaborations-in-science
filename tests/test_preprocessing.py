from citation_graphs.preprocessing import (
    fix_json_brackets_in_text,
    keep_required_fields,
    replace_numberint_tokens_in_text,
)


def test_replace_numberint_tokens_in_text() -> None:
    raw_text = '{"year": NumberInt(2020)}'
    processed = replace_numberint_tokens_in_text(raw_text)
    assert processed == '{"year": 2020}'


def test_fix_json_brackets_in_text() -> None:
    raw_text = '{"a": 1}, {"b": 2}'
    processed = fix_json_brackets_in_text(raw_text)
    assert processed.startswith("[")
    assert processed.endswith("]")


def test_keep_required_fields() -> None:
    records = [
        {
            "_id": "paper_1",
            "title": "Title",
            "year": 2020,
            "authors": [],
            "fos": ["AI"],
            "references": ["paper_0"],
            "extra_field": "should be removed",
        }
    ]

    cleaned = keep_required_fields(records)

    assert len(cleaned) == 1
    assert "extra_field" not in cleaned[0]
    assert cleaned[0]["_id"] == "paper_1"
    assert cleaned[0]["title"] == "Title"