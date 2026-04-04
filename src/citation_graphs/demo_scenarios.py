from __future__ import annotations

from typing import Any


DEMO_SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario_id": "author_investigation",
        "title": "Author Investigation",
        "description": "Demonstrate author search, publication footprint, collaborators, venues, and dashboard synthesis.",
        "target_tab": "Search",
        "next_step": "Open Search, run the query, then inspect Dashboards.",
        "preset_name": "author_demo",
        "expected_capabilities": [
            "author retrieval",
            "profile synthesis",
            "collaborator ranking",
            "dashboard preview",
        ],
    },
    {
        "scenario_id": "publication_investigation",
        "title": "Publication Investigation",
        "description": "Demonstrate title-based discovery, publication profile, and citation workflow preparation.",
        "target_tab": "Publication Search",
        "next_step": "Open Publication Search, run the query, then inspect Dashboards or build a graph.",
        "preset_name": "publication_demo",
        "expected_capabilities": [
            "title search",
            "publication profile",
            "citation workflow",
            "dashboard preview",
        ],
    },
    {
        "scenario_id": "comparison_walkthrough",
        "title": "Comparison Walkthrough",
        "description": "Demonstrate graph-based comparison between two nodes through shortest paths and connectivity.",
        "target_tab": "Compare",
        "next_step": "Open Compare and select an existing graph to compare two nodes.",
        "preset_name": "compare_demo",
        "expected_capabilities": [
            "graph comparison",
            "shortest path analysis",
            "connectivity reasoning",
        ],
    },
    {
        "scenario_id": "insights_walkthrough",
        "title": "Insights Walkthrough",
        "description": "Demonstrate graph health, centrality leaders, communities, and narrative insights.",
        "target_tab": "Insights",
        "next_step": "Open Insights and review the selected analysis base.",
        "preset_name": "insights_demo",
        "expected_capabilities": [
            "graph health summary",
            "centrality interpretation",
            "community analysis",
            "narrative insights",
        ],
    },
]


def get_demo_scenarios() -> list[dict[str, Any]]:
    return DEMO_SCENARIOS
