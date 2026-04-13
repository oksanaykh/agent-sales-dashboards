"""
agents/state.py

Single source of truth for the Sales Dashboard Agent.
Every node reads from and writes to AgentState — no global variables.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict):
    # Input
    source: str                    # path to CSV or "<upload>"

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
    dashboard_exec_path: str       # path to generated HTML (CLI mode)
    dashboard_product_path: str
    dashboard_marketing_path: str
    dashboard_combined_path: str   # combined 3-tab HTML (CLI mode)
    dashboard_combined_html: str   # combined HTML as string (web mode)

    # Agent trace
    messages: list[str]
    error: str | None

    # Web mode: raw bytes from upload (not a file path)
    _file_bytes: bytes | None


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
        dashboard_combined_html="",
        messages=[],
        error=None,
        _file_bytes=None,
    )


def initial_state_from_bytes(file_bytes: bytes, filename: str = "<upload>") -> AgentState:
    """Create initial state for web upload (no file path needed)."""
    state = initial_state(filename)
    state["_file_bytes"] = file_bytes  # type: ignore[typeddict-unknown-key]
    return state
