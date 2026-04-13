from __future__ import annotations
import csv, pytest

SAMPLE_ROWS = [
    {"Order ID":"ORD-001","Date":"2023-01-15","Category":"Electronics","Product Name":"iPhone 15","Quantity":2,"Unit Price":999.0,"Total Price":1998.0,"Region":"North America","Payment Method":"Credit Card"},
    {"Order ID":"ORD-002","Date":"2023-01-20","Category":"Books","Product Name":"Atomic Habits","Quantity":1,"Unit Price":15.0,"Total Price":15.0,"Region":"Europe","Payment Method":"PayPal"},
    {"Order ID":"ORD-003","Date":"2023-02-05","Category":"Electronics","Product Name":"MacBook Air","Quantity":1,"Unit Price":1299.0,"Total Price":1299.0,"Region":"Asia","Payment Method":"Debit Card"},
    {"Order ID":"ORD-004","Date":"2023-02-18","Category":"Clothing","Product Name":"Nike Sneakers","Quantity":3,"Unit Price":120.0,"Total Price":360.0,"Region":"North America","Payment Method":"Credit Card"},
    {"Order ID":"ORD-005","Date":"2023-03-10","Category":"Books","Product Name":"Dune","Quantity":2,"Unit Price":12.0,"Total Price":24.0,"Region":"Europe","Payment Method":"PayPal"},
    {"Order ID":"ORD-006","Date":"2023-03-22","Category":"Sports","Product Name":"Yoga Mat","Quantity":1,"Unit Price":45.0,"Total Price":45.0,"Region":"Asia","Payment Method":"Credit Card"},
    {"Order ID":"ORD-007","Date":"2023-04-01","Category":"Electronics","Product Name":"Sony Headphones","Quantity":2,"Unit Price":299.0,"Total Price":598.0,"Region":"Europe","Payment Method":"Debit Card"},
    {"Order ID":"ORD-008","Date":"2023-04-14","Category":"Beauty Products","Product Name":"Face Serum","Quantity":4,"Unit Price":60.0,"Total Price":240.0,"Region":"North America","Payment Method":"PayPal"},
]

@pytest.fixture
def sample_rows(): return SAMPLE_ROWS

@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "test_sales.csv"
    fields = ["Transaction ID","Date","Product Category","Product Name","Units Sold","Unit Price","Total Revenue","Region","Payment Method"]
    canonical = {"Transaction ID":"Order ID","Product Category":"Category","Units Sold":"Quantity","Total Revenue":"Total Price"}
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in SAMPLE_ROWS:
            # reverse-map to CSV column names
            out = {}
            rev = {v:k for k,v in canonical.items()}
            for k,v in row.items():
                out[rev.get(k, k)] = v
            writer.writerow(out)
    return str(path)

@pytest.fixture
def sample_csv_bytes(sample_csv):
    return open(sample_csv, "rb").read()
