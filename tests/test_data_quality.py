from __future__ import annotations

from citation_graphs.data_quality import compute_data_quality_report


def test_data_quality_report_structure(mini_parquet) -> None:
    report = compute_data_quality_report(mini_parquet, top_n=5)

    assert "summary" in report
    assert "top_years" in report
    assert "top_fos" in report

    summary = report["summary"]
    assert summary["row_count"] == 3
    assert summary["min_year"] == 2019
    assert summary["max_year"] == 2020
