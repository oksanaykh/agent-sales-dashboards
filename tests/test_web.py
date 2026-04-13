"""
tests/test_web.py

Integration tests for FastAPI endpoints.
No LLM called — fully deterministic.
"""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

VALID_CSV = b"""Transaction ID,Date,Product Category,Product Name,Units Sold,Unit Price,Total Revenue,Region,Payment Method
10001,2024-01-01,Electronics,iPhone 14 Pro,2,999.99,1999.98,North America,Credit Card
10002,2024-01-15,Books,Dune,1,25.99,25.99,Europe,PayPal
10003,2024-02-01,Clothing,Nike Sneakers,3,89.99,269.97,Asia,Debit Card
10004,2024-02-20,Sports,Yoga Mat,2,45.00,90.00,North America,Credit Card
10005,2024-03-10,Beauty Products,Face Serum,1,60.00,60.00,Europe,PayPal
"""


def test_index_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "drop-zone" in r.text
    assert "Dashboard Agent" in r.text


def test_preview_valid_csv():
    r = client.post("/preview", files={"file": ("sales.csv", VALID_CSV, "text/csv")})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["row_count"] == 5
    assert d["col_count"] == 9
    assert d["date_min"] == "2024-01-01"
    assert d["date_max"] == "2024-03-10"


def test_preview_wrong_extension():
    r = client.post("/preview", files={"file": ("data.xlsx", VALID_CSV, "text/csv")})
    assert r.status_code == 422
    assert "csv" in r.json()["error"].lower()


def test_preview_missing_columns():
    bad = b"col1,col2\na,b\nc,d\n"
    r = client.post("/preview", files={"file": ("bad.csv", bad, "text/csv")})
    assert r.status_code == 422
    assert "Missing required columns" in r.json()["error"]


def test_generate_returns_html_dashboard():
    r = client.post("/generate", files={"file": ("sales.csv", VALID_CSV, "text/csv")})
    assert r.status_code == 200
    html = r.text
    assert len(html) > 5000
    assert "Chart.js" in html
    assert 'data-tab="exec"' in html
    assert 'data-tab="product"' in html
    assert 'data-tab="marketing"' in html


def test_generate_bad_file_returns_422():
    bad = b"col1,col2\na,b\n"
    r = client.post("/generate", files={"file": ("bad.csv", bad, "text/csv")})
    assert r.status_code == 422
