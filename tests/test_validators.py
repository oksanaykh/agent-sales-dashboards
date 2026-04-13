"""
tests/test_validators.py

Unit tests for web/validators.py
"""
from __future__ import annotations
import pytest
from web.validators import validate_csv

VALID_CSV = b"""Transaction ID,Date,Product Category,Product Name,Units Sold,Unit Price,Total Revenue,Region,Payment Method
10001,2024-01-01,Electronics,iPhone,2,999.99,1999.98,North America,Credit Card
10002,2024-01-15,Books,Dune,1,15.99,15.99,Europe,PayPal
"""

def test_valid_csv():
    r = validate_csv(VALID_CSV, "test.csv")
    assert r.ok
    assert r.row_count == 2
    assert r.col_count == 9
    assert r.date_min == "2024-01-01"
    assert r.date_max == "2024-01-15"

def test_empty_file():
    r = validate_csv(b"", "test.csv")
    assert not r.ok
    assert "empty" in r.error.lower()

def test_wrong_extension():
    r = validate_csv(VALID_CSV, "data.xlsx")
    assert not r.ok
    assert ".csv" in r.error

def test_missing_columns():
    r = validate_csv(b"col1,col2\na,b\n", "test.csv")
    assert not r.ok
    assert "Missing required columns" in r.error

def test_file_too_large():
    r = validate_csv(b"x" * (11 * 1024 * 1024), "test.csv")
    assert not r.ok
    assert "too large" in r.error.lower()

def test_only_header_no_data():
    header = b"Transaction ID,Date,Product Category,Product Name,Units Sold,Unit Price,Total Revenue,Region,Payment Method\n"
    r = validate_csv(header, "test.csv")
    assert not r.ok
    assert "no data rows" in r.error.lower()

def test_to_dict():
    r = validate_csv(VALID_CSV, "test.csv")
    d = r.to_dict()
    assert d["ok"] is True
    assert d["row_count"] == 2
    assert isinstance(d["columns"], list)
