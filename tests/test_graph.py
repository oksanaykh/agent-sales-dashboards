"""
tests/test_graph.py

End-to-end integration tests for the LangGraph agent.
No LLM is called — the graph is fully deterministic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.graph import get_app
from agents.state import initial_state


def test_graph_happy_path(sample_csv, tmp_path, monkeypatch):
    """Full run on a real CSV produces four HTML files."""
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))

    # Invalidate the lru_cache so monkeypatched env is picked up
    from config import settings as settings_module
    settings_module.get_settings.cache_clear()

    app = get_app()
    state = initial_state(sample_csv)
    final = app.invoke(state)

    assert final.get("error") is None
    assert final["row_count"] == 8
    assert final["col_count"] == 9
    assert len(final["messages"]) >= 4

    for key in ("dashboard_exec_path", "dashboard_product_path",
                "dashboard_marketing_path", "dashboard_combined_path"):
        path = final.get(key, "")
        assert path, f"{key} should be set"
        assert Path(path).exists(), f"File missing: {path}"
        assert Path(path).stat().st_size > 1000, f"File suspiciously small: {path}"


def test_graph_missing_file():
    """Loader failure should set error and not crash."""
    app = get_app()
    state = initial_state("nonexistent_file.csv")
    final = app.invoke(state)

    assert final.get("error") is not None
    assert final["dashboard_combined_path"] == ""


def test_combined_html_has_tabs(sample_csv, tmp_path, monkeypatch):
    """Combined HTML must contain all three tab buttons."""
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    from config import settings as settings_module
    settings_module.get_settings.cache_clear()

    app = get_app()
    final = app.invoke(initial_state(sample_csv))

    html = Path(final["dashboard_combined_path"]).read_text(encoding="utf-8")
    assert "data-tab=\"exec\""      in html
    assert "data-tab=\"product\""   in html
    assert "data-tab=\"marketing\"" in html
    assert "Chart.js"               in html
