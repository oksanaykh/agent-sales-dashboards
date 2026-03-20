"""
tests/test_loader.py

Unit tests for tools/loader.py
"""

from __future__ import annotations

import pytest
from tools.loader import load_csv


def test_load_basic(sample_csv):
    result = load_csv(sample_csv)
    assert result["row_count"] == 8
    assert result["col_count"] == 9
    assert "Order ID" in result["columns"]


def test_numeric_casting(sample_csv):
    result = load_csv(sample_csv)
    row = result["rows"][0]
    assert isinstance(row["Total Price"], float)
    assert isinstance(row["Quantity"], int)
    assert isinstance(row["Unit Price"], float)


def test_date_range(sample_csv):
    result = load_csv(sample_csv)
    min_d, max_d = result["date_range"]
    assert min_d == "2023-01-15"
    assert max_d == "2023-04-14"


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_csv("nonexistent_file.csv")


def test_empty_csv(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("Order ID,Date,Category\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        load_csv(str(path))
