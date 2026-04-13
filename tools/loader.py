"""
tools/loader.py

Loads a CSV into a list of dicts and extracts basic shape metadata.
Supports: file path (str) or raw bytes (web upload).
"""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path
from typing import Union

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


def load_csv(source: Union[str, bytes]) -> dict:
    """
    Parse a CSV file and normalise column names to canonical internal names.

    Args:
        source: file path (str) or raw CSV bytes (web upload)

    Returns a dict with keys:
      rows, row_count, col_count, columns, date_range
    """
    if isinstance(source, bytes):
        return _load_from_bytes(source)
    return _load_from_path(source)


def _load_from_path(source: str) -> dict:
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        return _parse_csv_stream(f, source)


def _load_from_bytes(data: bytes) -> dict:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    stream = io.StringIO(text)
    return _parse_csv_stream(stream, "<upload>")


def _parse_csv_stream(stream, source_label: str) -> dict:
    reader = csv.DictReader(stream)
    columns = list(reader.fieldnames or [])
    rows: list[dict] = []
    for row in reader:
        rows.append(_cast_row(row))

    if not rows:
        raise ValueError(f"CSV is empty: {source_label}")

    # Warn about missing expected columns
    found = set(columns)
    missing = REQUIRED_COLUMNS - found
    if missing:
        logger.warning("Missing expected columns: %s", missing)

    # Date range
    dates = [str(r.get("Date", "")) for r in rows if r.get("Date")]
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
