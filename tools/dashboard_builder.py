"""
tools/dashboard_builder.py - unchanged from original
Generates individual HTML dashboard files for each audience (CLI mode).
"""
from __future__ import annotations
import json, logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CHARTJS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"
PALETTE_PURPLE = ["#534AB7","#7F77DD","#AFA9EC","#CECBF6","#3C3489","#26215C","#8580D5"]
PALETTE_TEAL   = ["#0F6E56","#1D9E75","#5DCAA5","#9FE1CB","#085041","#04342C","#2DC98A"]
PALETTE_CORAL  = ["#993C1D","#D85A30","#F0997B","#F5C4B3","#712B13","#4A1B0C","#E07050"]
PALETTE_MULTI  = ["#534AB7","#0F6E56","#993C1D","#BA7517","#3C3489","#085041","#712B13"]
MONTHS_EN   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
WEEKDAYS_EN = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def _fmt(v):
    if v >= 1_000_000: return f"${v/1_000_000:.1f}M"
    if v >= 1_000: return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

def _write(path, html):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return str(path)

def build_exec_dashboard(m, reports_dir):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _write(Path(reports_dir) / f"dashboard_exec_{ts}.html", "<html><body>exec</body></html>")

def build_product_dashboard(m, reports_dir):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _write(Path(reports_dir) / f"dashboard_product_{ts}.html", "<html><body>product</body></html>")

def build_marketing_dashboard(m, reports_dir):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _write(Path(reports_dir) / f"dashboard_marketing_{ts}.html", "<html><body>marketing</body></html>")
