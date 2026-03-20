"""
tests/test_metrics.py

Unit tests for tools/metrics.py — all three metric functions.
"""

from __future__ import annotations

import pytest


# ── Executive metrics ─────────────────────────────────────────────────────────

class TestExecMetrics:
    def test_total_revenue(self, exec_metrics, sample_rows):
        expected = sum(r["Total Price"] for r in sample_rows)
        assert abs(exec_metrics["total_revenue"] - expected) < 0.01

    def test_total_orders(self, exec_metrics, sample_rows):
        assert exec_metrics["total_orders"] == len(sample_rows)

    def test_aov(self, exec_metrics):
        rev = exec_metrics["total_revenue"]
        orders = exec_metrics["total_orders"]
        assert abs(exec_metrics["aov"] - rev / orders) < 0.01

    def test_total_units(self, exec_metrics, sample_rows):
        expected = sum(r["Quantity"] for r in sample_rows)
        assert exec_metrics["total_units"] == expected

    def test_revenue_by_month_sorted(self, exec_metrics):
        months = exec_metrics["months_sorted"]
        assert months == sorted(months)

    def test_revenue_by_month_values(self, exec_metrics):
        # Jan: 1998 + 15 = 2013
        assert abs(exec_metrics["revenue_by_month"]["2023-01"] - 2013.0) < 0.01

    def test_revenue_by_category_keys(self, exec_metrics):
        cats = set(exec_metrics["revenue_by_category"].keys())
        assert "Electronics" in cats
        assert "Books" in cats

    def test_seasonality_index_length(self, exec_metrics):
        assert len(exec_metrics["seasonality_index"]) == 12

    def test_seasonality_index_mean_approx_one(self, exec_metrics):
        idx = [v for v in exec_metrics["seasonality_index"] if v > 0]
        if idx:
            mean = sum(idx) / len(idx)
            assert 0.5 <= mean <= 2.0  # sanity range

    def test_mom_growth_length(self, exec_metrics):
        assert len(exec_metrics["mom_growth"]) == len(exec_metrics["months_sorted"])

    def test_mom_growth_first_is_none(self, exec_metrics):
        assert exec_metrics["mom_growth"][0] is None


# ── Product metrics ───────────────────────────────────────────────────────────

class TestProductMetrics:
    def test_top_products_is_list_of_tuples(self, product_metrics):
        tp = product_metrics["top_products"]
        assert isinstance(tp, list)
        assert all(isinstance(x, (list, tuple)) and len(x) == 2 for x in tp)

    def test_top_products_sorted_desc(self, product_metrics):
        revs = [x[1] for x in product_metrics["top_products"]]
        assert revs == sorted(revs, reverse=True)

    def test_top_products_max_15(self, product_metrics):
        assert len(product_metrics["top_products"]) <= 15

    def test_sku_count(self, product_metrics, sample_rows):
        unique_prods = {r["Product Name"] for r in sample_rows}
        assert product_metrics["sku_count"] == len(unique_prods)

    def test_revenue_by_region_keys(self, product_metrics):
        assert "North America" in product_metrics["revenue_by_region"]
        assert "Europe" in product_metrics["revenue_by_region"]

    def test_cat_by_month_length(self, product_metrics):
        for cat, vals in product_metrics["cat_by_month"].items():
            assert len(vals) == 12, f"{cat} should have 12 monthly values"

    def test_cat_by_region_structure(self, product_metrics):
        cbr = product_metrics["cat_by_region"]
        assert isinstance(cbr, dict)
        for cat, regions in cbr.items():
            assert isinstance(regions, dict)

    def test_top_category_is_electronics(self, product_metrics):
        # Electronics has highest revenue in sample data
        assert product_metrics["top_category"] == "Electronics"

    def test_avg_qty_positive(self, product_metrics):
        assert product_metrics["avg_qty_per_order"] > 0


# ── Marketing metrics ─────────────────────────────────────────────────────────

class TestMarketingMetrics:
    def test_orders_by_payment_keys(self, marketing_metrics):
        pays = marketing_metrics["orders_by_payment"]
        assert "Credit Card" in pays
        assert "PayPal" in pays

    def test_orders_by_payment_total(self, marketing_metrics, sample_rows):
        total = sum(marketing_metrics["orders_by_payment"].values())
        assert total == len(sample_rows)

    def test_aov_by_payment_positive(self, marketing_metrics):
        for pay, aov in marketing_metrics["aov_by_payment"].items():
            assert aov > 0, f"AOV for {pay} should be positive"

    def test_revenue_by_region_sorted(self, marketing_metrics):
        vals = list(marketing_metrics["revenue_by_region"].values())
        assert vals == sorted(vals, reverse=True)

    def test_orders_by_weekday_length(self, marketing_metrics):
        assert len(marketing_metrics["orders_by_weekday"]) == 7

    def test_orders_by_weekday_total(self, marketing_metrics, sample_rows):
        total = sum(marketing_metrics["orders_by_weekday"])
        assert total == len(sample_rows)

    def test_pay_by_category_structure(self, marketing_metrics):
        for pay, cats in marketing_metrics["pay_by_category"].items():
            assert isinstance(cats, dict)

    def test_top_region_in_regions(self, marketing_metrics):
        assert marketing_metrics["top_region"] in marketing_metrics["revenue_by_region"]

    def test_top_payment_in_payments(self, marketing_metrics):
        assert marketing_metrics["top_payment"] in marketing_metrics["orders_by_payment"]

    def test_all_months_sorted(self, marketing_metrics):
        months = marketing_metrics["all_months"]
        assert months == sorted(months)
