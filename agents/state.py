"""
agents/state.py

Single source of truth for the Sales Dashboard Agent.
Every node reads from and writes to AgentState — no global variables.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict):
    # Input
    source: str                    # path to CSV

    # Data
    rows: list[dict]               # parsed rows
    row_count: int
    col_count: int
    columns: list[str]
    date_range: tuple[str, str]    # (min_date, max_date)

    # Computed metrics (one dict per audience)
    metrics_exec: dict[str, Any]
    metrics_product: dict[str, Any]
    metrics_marketing: dict[str, Any]

    # Output artifacts
    dashboard_exec_path: str       # path to generated HTML
    dashboard_product_path: str
    dashboard_marketing_path: str
    dashboard_combined_path: str   # combined 3-tab HTML

    # Agent trace
    messages: list[str]
    error: str | None


def initial_state(source: str) -> AgentState:
    return AgentState(
        source=source,
        rows=[],
        row_count=0,
        col_count=0,
        columns=[],
        date_range=("", ""),
        metrics_exec={},
        metrics_product={},
        metrics_marketing={},
        dashboard_exec_path="",
        dashboard_product_path="",
        dashboard_marketing_path="",
        dashboard_combined_path="",
        messages=[],
        error=None,
    )
