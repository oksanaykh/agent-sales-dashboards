"""
server.py

FastAPI web server for the Sales Dashboard Agent.

Endpoints:
  GET  /           → upload UI (index.html)
  POST /preview    → validate CSV, return shape info (fast, no agent)
  POST /generate   → run agent, return combined HTML dashboard

Run:
  python server.py
  # → http://localhost:8000
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Make sure project root is importable
sys.path.insert(0, str(Path(__file__).parent))

from agents.graph import get_app
from agents.state import AgentState
from web.validators import validate_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sales Dashboard Agent", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Load UI template once at startup ──────────────────────────────────────────

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"


def _load_template() -> str:
    if _TEMPLATE_PATH.exists():
        return _TEMPLATE_PATH.read_text(encoding="utf-8")
    return "<h1>Template not found</h1>"


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the upload UI."""
    return HTMLResponse(_load_template())


@app.post("/preview")
async def preview(file: UploadFile = File(...)):
    """
    Validate CSV and return shape info without running the full agent.
    Fast — used to show the confirmation step before generation.
    """
    file_bytes = await file.read()
    result = validate_csv(file_bytes, filename=file.filename or "")

    if not result.ok:
        return JSONResponse(status_code=422, content={"ok": False, "error": result.error})

    return JSONResponse(content=result.to_dict())


@app.post("/generate")
async def generate(file: UploadFile = File(...)):
    """
    Run the full LangGraph agent and return the combined HTML dashboard.
    Returns the HTML string directly so the browser can render it inline
    or the user can download it.
    """
    file_bytes = await file.read()

    # Fast validation first
    validation = validate_csv(file_bytes, filename=file.filename or "")
    if not validation.ok:
        raise HTTPException(status_code=422, detail=validation.error)

    logger.info("Generating dashboard for %s (%d rows)", file.filename, validation.row_count)

    # Build initial state with bytes
    state: AgentState = {
        "source": file.filename or "<upload>",
        "_file_bytes": file_bytes,  # type: ignore[typeddict-unknown-key]
        "rows": [],
        "row_count": 0,
        "col_count": 0,
        "columns": [],
        "date_range": ("", ""),
        "metrics_exec": {},
        "metrics_product": {},
        "metrics_marketing": {},
        "dashboard_exec_path": "",
        "dashboard_product_path": "",
        "dashboard_marketing_path": "",
        "dashboard_combined_path": "",
        "dashboard_combined_html": "",
        "messages": [],
        "error": None,
    }

    try:
        agent = get_app()
        final = agent.invoke(state)
    except Exception as exc:
        logger.exception("Agent crashed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

    if final.get("error"):
        raise HTTPException(status_code=422, detail=final["error"])

    html = final.get("dashboard_combined_html", "")
    if not html:
        raise HTTPException(status_code=500, detail="Agent produced no output")

    logger.info("Dashboard ready — %d chars", len(html))
    return HTMLResponse(content=html)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
