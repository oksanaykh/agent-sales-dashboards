# 📊 Sales Dashboard Agent

> A LangGraph **sales analytics agent** that reads a CSV, computes product metrics,
> and generates interactive HTML dashboards for three audiences —
> all in one command, no server required.

[![python: 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![framework: LangGraph](https://img.shields.io/badge/framework-LangGraph-purple)](https://langchain-ai.github.io/langgraph/)
[![output: HTML dashboards](https://img.shields.io/badge/output-HTML%20dashboards-green)]()

---

## What this agent does

Reads any CSV with sales data → computes metrics for three audiences → writes HTML dashboards.

| Audience | Dashboard focus |
|---|---|
| **Топ-менеджмент** | Revenue, AOV, category mix, seasonality index |
| **Продуктовая команда** | Top products, SKU analysis, category × region heatmap |
| **Маркетинг / Growth** | Payment methods, regional trends, weekday patterns |

All three dashboards are combined into **one self-contained HTML file** with a tab switcher.
Open it in any browser — no server, no dependencies.

---

## Architecture

```
START → loader → metrics_computer → dashboard_builder → combiner → END
```

Each node is a pure function `AgentState → dict`. The graph uses a conditional edge
after `loader` to short-circuit on file errors without crashing.

```
agent-sales-dashboard/
├── agents/
│   ├── graph.py          # LangGraph StateGraph — nodes + conditional edges
│   └── state.py          # AgentState TypedDict — single source of truth
│
├── tools/
│   ├── loader.py         # CSV parser, type casting, date range
│   ├── metrics.py        # Pure metric functions for all 3 audiences
│   ├── dashboard_builder.py  # Generates 3 individual HTML files
│   └── combiner.py       # Assembles the combined 3-tab HTML
│
├── config/
│   └── settings.py       # Reads REPORTS_DIR, LOG_LEVEL from env
│
├── memory/               # Reserved for future metric caching
│
├── tests/
│   ├── conftest.py       # Shared fixtures (8-row sample CSV)
│   ├── test_loader.py    # Unit tests for CSV loader
│   ├── test_metrics.py   # Unit tests for all metric functions
│   └── test_graph.py     # End-to-end integration tests (no LLM)
│
├── datasets/             # Put your CSV here
├── reports/              # Generated HTML dashboards land here (gitignored)
├── main.py               # CLI entry point
└── pyproject.toml
```

---

## Expected CSV columns

| Column | Type | Description |
|---|---|---|
| `Order ID` | string | Unique transaction identifier |
| `Date` | date (ISO 8601) | Transaction date |
| `Category` | string | Product category |
| `Product Name` | string | Specific product |
| `Quantity` | int | Units sold |
| `Unit Price` | float | Price per unit |
| `Total Price` | float | `Quantity × Unit Price` |
| `Region` | string | Geographic region |
| `Payment Method` | string | e.g. Credit Card, PayPal |

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/your-username/agent-sales-dashboard
cd agent-sales-dashboard

pip install -e ".[anthropic]"
# or just: pip install langgraph langchain-core
```

### 2. Configure (optional)

```bash
cp .env.example .env
# Edit .env — set REPORTS_DIR if you want dashboards somewhere other than reports/
```

### 3. Run

```bash
# Basic run
python main.py --source datasets/sales.csv

# Open the combined dashboard in your browser immediately
python main.py --source datasets/sales.csv --open

# Verbose mode (shows LangGraph node execution)
python main.py --source datasets/sales.csv --verbose

# Save full agent state as JSON (useful for debugging)
python main.py --source datasets/sales.csv --output-json state.json
```

### 4. View the results

```
reports/
├── dashboard_exec_20240315_143201.html       ← Топ-менеджмент
├── dashboard_product_20240315_143201.html    ← Продуктовая команда
├── dashboard_marketing_20240315_143201.html  ← Маркетинг / Growth
└── dashboard_combined_20240315_143201.html   ← ★ All three with tab switcher
```

Open any file in a browser. `dashboard_combined_*.html` is the main deliverable —
it has three tabs with a colored tab switcher (purple / teal / coral).

---

## Example output

```
================================================================
  ✅  Dashboards generated successfully
================================================================

  Agent log (4 steps):
    [loader] Loaded 240,000 rows × 9 cols from 'datasets/sales.csv'
    [metrics] exec: 9 keys | product: 10 keys | marketing: 11 keys
    [builder] Dashboards written → reports/
    [combiner] Combined dashboard → reports/dashboard_combined_20240315_143201.html

  Output files:
      Топ-менеджмент   → reports/dashboard_exec_20240315_143201.html
      Продуктовая      → reports/dashboard_product_20240315_143201.html
      Маркетинг        → reports/dashboard_marketing_20240315_143201.html
      ★ Combined       → reports/dashboard_combined_20240315_143201.html
```

---

## Dashboards in detail

### Топ-менеджмент (Executive)
- KPI cards: Revenue, Orders, AOV, Units sold
- Line chart: Revenue by month
- Bar + Doughnut: Revenue by category
- Bar: Seasonality index by calendar month

### Продуктовая команда (Product)
- KPI cards: Top category, Top product, SKU count, Avg qty/order
- Horizontal bar: Top-15 products by revenue
- Horizontal bar: Revenue by region
- Stacked bar: Category mix by region
- Heatmap table: Category × calendar month

### Маркетинг / Growth
- KPI cards: Top region, Top payment, Region count, Payment count
- Doughnut: Payment method share (% of orders)
- Bar: AOV by payment method
- Multi-line: Revenue by region over time
- Bar: Orders by day of week
- Stacked bar: Payment method × category

---

## Running tests

```bash
pip install -e ".[dev]"

pytest                          # all tests
pytest tests/test_metrics.py   # metrics only
pytest tests/test_graph.py     # end-to-end (no LLM needed)
pytest -v --tb=short            # verbose
pytest --cov                    # with coverage
```

---

## Extending the agent

| Idea | Where |
|---|---|
| LLM-generated text summaries per dashboard | New node in `agents/graph.py` + `tools/summarizer.py` |
| Metric caching (skip recompute if file unchanged) | `memory/metric_cache.py` |
| PDF export of dashboards | New tool using `playwright` or `weasyprint` |
| Slack/email delivery of the combined HTML | New node `tools/notifier.py` |
| Filters by date range / region via CLI | `main.py` args + pass to `loader_node` |
| Multi-file comparison (month vs month) | New conditional branch in `graph.py` |
| Scheduled runs (cron / Airflow) | `main.py` returns exit code 0/1 for scripting |

---

## License

MIT
