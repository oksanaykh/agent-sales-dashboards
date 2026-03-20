"""
tools/loader.py

Loads a CSV into a list of dicts and extracts basic shape metadata.
Supports: plain CSV path.
Future: sqlite:///path.db::table, postgresql://...
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "Transaction ID", "Date", "Product Category", "Product Name",
    "Units Sold", "Unit Price", "Total Revenue", "Region", "Payment Method",
}

# Mapping from CSV column names → internal canonical names used in metrics.py
COLUMN_ALIASES = {
    "Transaction ID":   "Order ID",
    "Product Category": "Category",
    "Units Sold":       "Quantity",
    "Total Revenue":    "Total Price",
}


def load_csv(source: str) -> dict:
    """
    Parse a CSV file and normalise column names to canonical internal names.

    Returns a dict with keys:
      rows, row_count, col_count, columns, date_range
    """
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        for row in reader:
            rows.append(_cast_row(row))

    if not rows:
        raise ValueError(f"CSV is empty: {source}")

    # Warn about missing expected columns
    found = set(columns)
    missing = REQUIRED_COLUMNS - found
    if missing:
        logger.warning("Missing expected columns: %s", missing)

    # Date range
    dates = []
    for r in rows:
        d = r.get("Date", "")
        if d:
            dates.append(str(d))
    dates.sort()
    date_range = (dates[0], dates[-1]) if dates else ("", "")

    return {
        "rows": rows,
        "row_count": len(rows),
        "col_count": len(columns),
        "columns": columns,
        "date_range": date_range,
    }


def _cast_row(row: dict) -> dict:
    """Normalise column names and cast numeric columns from str to float/int."""
    out = {}
    for k, v in row.items():
        canonical = COLUMN_ALIASES.get(k, k)
        v = v.strip() if isinstance(v, str) else v

        if canonical == "Quantity":
            try:
                out[canonical] = int(float(v))
            except (ValueError, TypeError):
                out[canonical] = None
        elif canonical in ("Unit Price", "Total Price"):
            try:
                out[canonical] = float(v)
            except (ValueError, TypeError):
                out[canonical] = None
        else:
            out[canonical] = v if v != "" else None
    return out
