# 📊 Sales Dashboard Agent

> A **LangGraph agent** that reads a CSV, computes metrics, and generates interactive
> HTML dashboards for three audiences — all from a drag-and-drop web UI.

[![python: 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![framework: LangGraph](https://img.shields.io/badge/framework-LangGraph-purple)](https://langchain-ai.github.io/langgraph/)
[![output: HTML dashboards](https://img.shields.io/badge/output-HTML%20dashboards-green)]()

---

## What this agent does

Upload any CSV with sales data → agent computes metrics → outputs three dashboards in one HTML file.

| Audience | Dashboard focus |
|---|---|
| **Executive** | Revenue, AOV, category mix, seasonality index |
| **Product Team** | Top products, SKU analysis, category × region heatmap |
| **Marketing / Growth** | Payment methods, regional trends, weekday patterns |

All three dashboards are combined into **one self-contained HTML file** with a tab switcher.
Open it in any browser — no server, no dependencies.

---

## Web UI — quickstart

```bash
git clone https://github.com/your-username/agent-sales-dashboard
cd agent-sales-dashboard

pip install -e ".[web]"

python server.py
# → http://localhost:8000
```

Then open `http://localhost:8000`, upload your CSV, and get your dashboards.

**Don't have a CSV?** Click "Download sample CSV" in the UI to get a 10-row example.

---

## Architecture

```
Browser (drag & drop CSV)
        │
        ▼ POST /preview  ─── fast validation, shape info
        │ POST /generate ─── run agent, return HTML
        │
   FastAPI server (server.py)
        │
        ▼
   LangGraph Agent
   START → loader → metrics_computer → dashboard_builder → combiner → END
        │
        ▼
   Combined HTML Dashboard (returned as string, no disk I/O)
        │
        ▼
Browser (renders inline + offers download)
```

### Two modes

| Mode | Input | Output |
|---|---|---|
| **Web** (`python server.py`) | Upload via browser | HTML string returned directly |
| **CLI** (`python main.py`) | File path | HTML files written to `reports/` |

---

## Expected CSV columns

The agent accepts the following column names. No renaming needed — aliases are auto-remapped.

| Canonical | Accepted aliases | Type |
|---|---|---|
| `Transaction ID` | — | string |
| `Date` | — | date ISO 8601 |
| `Product Category` | — | string |
| `Product Name` | — | string |
| `Units Sold` | — | int |
| `Unit Price` | — | float |
| `Total Revenue` | — | float |
| `Region` | — | string |
| `Payment Method` | — | string |

---

## CLI usage

```bash
pip install -e ".[anthropic]"   # or just: pip install langgraph langchain-core

python main.py --source datasets/sales.csv
python main.py --source datasets/sales.csv --open     # open in browser
python main.py --source datasets/sales.csv --verbose  # debug logging
```

---

## Project structure

```
agent-sales-dashboard/
├── server.py                  ← FastAPI web server (GET /, POST /preview, POST /generate)
├── templates/
│   └── index.html             ← Upload UI (drag & drop → preview → dashboard)
├── web/
│   └── validators.py          ← CSV validation (size, columns, encoding)
│
├── agents/
│   ├── graph.py               ← LangGraph StateGraph — nodes + conditional edges
│   └── state.py               ← AgentState TypedDict — single source of truth
│
├── tools/
│   ├── loader.py              ← CSV parser — supports file path or bytes (web upload)
│   ├── metrics.py             ← Pure metric functions for all 3 audiences
│   ├── dashboard_builder.py   ← Individual HTML files (CLI mode)
│   └── combiner.py            ← Combined 3-tab HTML — file (CLI) or string (web)
│
├── config/
│   └── settings.py            ← Env config (REPORTS_DIR, LOG_LEVEL)
│
├── datasets/
│   └── sales.csv              ← 240-row sample dataset
│
├── tests/
│   ├── conftest.py
│   ├── test_validators.py     ← Unit tests for CSV validation
│   ├── test_web.py            ← FastAPI endpoint tests
│   ├── test_loader.py         ← CSV loader tests
│   ├── test_metrics.py        ← Metric function tests
│   └── test_graph.py          ← End-to-end agent tests
│
├── main.py                    ← CLI entry point
└── pyproject.toml
```

---

## Running tests

```bash
pip install -e ".[dev,web]"

pytest                           # all tests
pytest tests/test_web.py        # endpoint tests only
pytest tests/test_validators.py # validation tests only
pytest -v --tb=short            # verbose
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Upload UI |
| `POST` | `/preview` | Validate CSV, return `{ok, row_count, col_count, date_min, date_max}` |
| `POST` | `/generate` | Run agent, return combined HTML dashboard |

### `/preview` response

```json
{
  "ok": true,
  "row_count": 240,
  "col_count": 9,
  "date_min": "2024-01-01",
  "date_max": "2024-08-27",
  "columns": ["Transaction ID", "Date", ...]
}
```

### Error response

```json
{ "ok": false, "error": "Missing required columns: Product Category, Units Sold" }
```

---

## Limits

| Constraint | Value |
|---|---|
| Max file size | 10 MB |
| Max rows | 100,000 |
| File type | `.csv` only |
| Encoding | UTF-8 or Latin-1 (auto-detected) |

---

## License

MIT
