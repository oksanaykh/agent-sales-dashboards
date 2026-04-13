"""
server/validators.py

Fast CSV validation before running the full agent pipeline.
Returns a structured result with shape info or a clear error message.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 100_000

REQUIRED_COLUMNS = {
    "Transaction ID", "Date", "Product Category", "Product Name",
    "Units Sold", "Unit Price", "Total Revenue", "Region", "Payment Method",
}


@dataclass
class ValidationResult:
    ok: bool
    error: str = ""
    row_count: int = 0
    col_count: int = 0
    columns: list[str] = None  # type: ignore
    date_min: str = ""
    date_max: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "error": self.error,
            "row_count": self.row_count,
            "col_count": self.col_count,
            "columns": self.columns or [],
            "date_min": self.date_min,
            "date_max": self.date_max,
        }


def validate_csv(file_bytes: bytes, filename: str = "") -> ValidationResult:
    # Size check
    if len(file_bytes) > MAX_FILE_SIZE:
        mb = len(file_bytes) / 1024 / 1024
        return ValidationResult(ok=False, error=f"File too large: {mb:.1f} MB (max 10 MB)")

    if len(file_bytes) == 0:
        return ValidationResult(ok=False, error="File is empty")

    # Extension check
    if filename and not filename.lower().endswith(".csv"):
        return ValidationResult(ok=False, error=f"Only .csv files are supported (got: {filename})")

    # Decode
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except Exception:
            return ValidationResult(ok=False, error="Could not decode file. Please save as UTF-8 CSV.")

    # Parse header
    stream = io.StringIO(text)
    reader = csv.DictReader(stream)
    columns = list(reader.fieldnames or [])

    if not columns:
        return ValidationResult(ok=False, error="CSV has no header row")

    missing = REQUIRED_COLUMNS - set(columns)
    if missing:
        missing_str = ", ".join(sorted(missing))
        return ValidationResult(
            ok=False,
            error=f"Missing required columns: {missing_str}"
        )

    # Count rows + collect dates
    rows = []
    dates = []
    try:
        for row in reader:
            rows.append(row)
            d = (row.get("Date") or "").strip()
            if d:
                dates.append(d)
            if len(rows) > MAX_ROWS:
                return ValidationResult(
                    ok=False,
                    error=f"File has more than {MAX_ROWS:,} rows. Please use a smaller dataset."
                )
    except csv.Error as e:
        return ValidationResult(ok=False, error=f"CSV parse error: {e}")

    if not rows:
        return ValidationResult(ok=False, error="CSV has no data rows (only a header)")

    dates.sort()
    return ValidationResult(
        ok=True,
        row_count=len(rows),
        col_count=len(columns),
        columns=columns,
        date_min=dates[0] if dates else "",
        date_max=dates[-1] if dates else "",
    )
