from __future__ import annotations

import json
from pathlib import Path

from citation_graphs.reporting import build_analysis_markdown_report, export_analysis_markdown_report


def test_build_analysis_markdown_report() -> None:
    analysis = {
        "summary": {"num_nodes": 10, "num_edges": 12, "density": 0.1},
        "centralities": {"degree": [], "closeness": [], "betweenness": []},
        "pagerank": [],
        "communities": {"num_communities": 2, "largest_communities": []},
    }
    markdown = build_analysis_markdown_report("demo_analysis", analysis)
    assert "# Graph Analysis Report - demo_analysis" in markdown
    assert "## Executive Summary" in markdown


def test_export_analysis_markdown_report(tmp_path: Path) -> None:
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(
        json.dumps(
            {
                "summary": {"num_nodes": 10, "num_edges": 12, "density": 0.1},
                "centralities": {"degree": [], "closeness": [], "betweenness": []},
                "pagerank": [],
                "communities": {"num_communities": 2, "largest_communities": []},
            }
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "report.md"
    result = export_analysis_markdown_report(analysis_path, output_path)

    assert output_path.exists()
    assert result["report_path"].endswith("report.md")
