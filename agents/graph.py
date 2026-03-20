"""
agents/graph.py

LangGraph StateGraph for the Sales Dashboard Agent.

Flow:
  START → loader → metrics_computer → dashboard_builder → combiner → END

Each node is a pure function: AgentState → dict (partial state update).
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from agents.state import AgentState
from tools.loader import load_csv
from tools.metrics import compute_exec_metrics, compute_marketing_metrics, compute_product_metrics
from tools.dashboard_builder import build_exec_dashboard, build_product_dashboard, build_marketing_dashboard
from tools.combiner import build_combined_dashboard

logger = logging.getLogger(__name__)


# ── Nodes ─────────────────────────────────────────────────────────────────────

def loader_node(state: AgentState) -> dict:
    """Load CSV → rows, basic shape info."""
    logger.info("Node: loader — source=%s", state["source"])
    try:
        result = load_csv(state["source"])
        msg = f"[loader] Loaded {result['row_count']:,} rows × {result['col_count']} cols from '{state['source']}'"
        logger.info(msg)
        return {**result, "messages": state["messages"] + [msg]}
    except Exception as exc:
        msg = f"[loader] ERROR: {exc}"
        logger.error(msg)
        return {"error": str(exc), "messages": state["messages"] + [msg]}


def metrics_node(state: AgentState) -> dict:
    """Compute all three sets of metrics from loaded rows."""
    logger.info("Node: metrics_computer — %d rows", state["row_count"])
    if state.get("error"):
        return {}

    rows = state["rows"]
    exec_m    = compute_exec_metrics(rows)
    product_m = compute_product_metrics(rows)
    marketing_m = compute_marketing_metrics(rows)

    msg = (
        f"[metrics] exec: {len(exec_m)} keys | "
        f"product: {len(product_m)} keys | "
        f"marketing: {len(marketing_m)} keys"
    )
    logger.info(msg)
    return {
        "metrics_exec": exec_m,
        "metrics_product": product_m,
        "metrics_marketing": marketing_m,
        "messages": state["messages"] + [msg],
    }


def dashboard_builder_node(state: AgentState) -> dict:
    """Build three individual HTML dashboards."""
    logger.info("Node: dashboard_builder")
    if state.get("error"):
        return {}

    from config.settings import get_settings
    settings = get_settings()

    exec_path    = build_exec_dashboard(state["metrics_exec"], settings.reports_dir)
    product_path = build_product_dashboard(state["metrics_product"], settings.reports_dir)
    marketing_path = build_marketing_dashboard(state["metrics_marketing"], settings.reports_dir)

    msg = f"[builder] Dashboards written → {settings.reports_dir}/"
    logger.info(msg)
    return {
        "dashboard_exec_path": exec_path,
        "dashboard_product_path": product_path,
        "dashboard_marketing_path": marketing_path,
        "messages": state["messages"] + [msg],
    }


def combiner_node(state: AgentState) -> dict:
    """Combine three dashboards into one HTML file with tab switcher."""
    logger.info("Node: combiner")
    if state.get("error"):
        return {}

    from config.settings import get_settings
    settings = get_settings()

    combined_path = build_combined_dashboard(
        exec_metrics=state["metrics_exec"],
        product_metrics=state["metrics_product"],
        marketing_metrics=state["metrics_marketing"],
        source=state["source"],
        date_range=state["date_range"],
        reports_dir=settings.reports_dir,
    )

    msg = f"[combiner] Combined dashboard → {combined_path}"
    logger.info(msg)
    return {
        "dashboard_combined_path": combined_path,
        "messages": state["messages"] + [msg],
    }


# ── Conditional routing ────────────────────────────────────────────────────────

def route_after_loader(state: AgentState) -> str:
    """Skip rest of graph if loader failed."""
    if state.get("error"):
        return END
    return "metrics_computer"


# ── Graph assembly ─────────────────────────────────────────────────────────────

def get_app():
    g = StateGraph(AgentState)

    g.add_node("loader",            loader_node)
    g.add_node("metrics_computer",  metrics_node)
    g.add_node("dashboard_builder", dashboard_builder_node)
    g.add_node("combiner",          combiner_node)

    g.add_edge(START, "loader")
    g.add_conditional_edges("loader", route_after_loader, {
        "metrics_computer": "metrics_computer",
        END: END,
    })
    g.add_edge("metrics_computer",  "dashboard_builder")
    g.add_edge("dashboard_builder", "combiner")
    g.add_edge("combiner",          END)

    return g.compile()
