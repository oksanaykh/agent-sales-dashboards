"""
tools/metrics.py

Pure functions that compute metric dicts for each audience.
No I/O — input: list[dict], output: dict[str, Any].
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _month_key(date_str: str) -> str:
    """'2023-04-15' → '2023-04'"""
    try:
        d = datetime.fromisoformat(str(date_str))
        return d.strftime("%Y-%m")
    except Exception:
        return "unknown"


def _weekday(date_str: str) -> int:
    """Return weekday index 0=Mon … 6=Sun, or -1 on error."""
    try:
        return datetime.fromisoformat(str(date_str)).weekday()
    except Exception:
        return -1


# ── Executive metrics ─────────────────────────────────────────────────────────

def compute_exec_metrics(rows: list[dict]) -> dict:
    """
    KPIs for top-management:
      total_revenue, total_orders, aov, total_units,
      revenue_by_month (sorted), revenue_by_category,
      seasonality_index (by calendar month 0-11),
      mom_growth (month-over-month % change list)
    """
    total_revenue = sum(_safe_float(r.get("Total Price")) for r in rows)
    total_orders  = len(rows)
    total_units   = sum(int(r.get("Quantity") or 0) for r in rows)
    aov = total_revenue / total_orders if total_orders else 0.0

    rev_by_month: dict[str, float] = defaultdict(float)
    for r in rows:
        rev_by_month[_month_key(r.get("Date", ""))] += _safe_float(r.get("Total Price"))

    months_sorted = sorted(rev_by_month.keys())
    rev_by_month_sorted = {m: round(rev_by_month[m], 2) for m in months_sorted}

    rev_by_cat: dict[str, float] = defaultdict(float)
    for r in rows:
        cat = r.get("Category") or "Other"
        rev_by_cat[cat] += _safe_float(r.get("Total Price"))
    rev_by_cat = dict(sorted(rev_by_cat.items(), key=lambda x: -x[1]))

    # Seasonality index: average revenue per calendar month / global monthly avg
    month_totals: dict[int, float] = defaultdict(float)
    month_counts: dict[int, int]   = defaultdict(int)
    for m_key, val in rev_by_month.items():
        try:
            m_num = int(m_key.split("-")[1]) - 1  # 0-indexed
            month_totals[m_num] += val
            month_counts[m_num] += 1
        except Exception:
            pass
    month_avgs = [
        month_totals[i] / month_counts[i] if month_counts[i] else 0.0
        for i in range(12)
    ]
    global_avg = sum(month_avgs) / 12 if any(month_avgs) else 1.0
    seasonality_index = [round(v / global_avg, 3) if global_avg else 0.0 for v in month_avgs]

    # MoM growth %
    vals = [rev_by_month_sorted[m] for m in months_sorted]
    mom_growth = [None]
    for i in range(1, len(vals)):
        if vals[i - 1]:
            mom_growth.append(round((vals[i] - vals[i - 1]) / vals[i - 1] * 100, 1))
        else:
            mom_growth.append(None)

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders":  total_orders,
        "total_units":   total_units,
        "aov":           round(aov, 2),
        "revenue_by_month":    rev_by_month_sorted,
        "revenue_by_category": {k: round(v, 2) for k, v in rev_by_cat.items()},
        "seasonality_index":   seasonality_index,
        "mom_growth":          mom_growth,
        "months_sorted":       months_sorted,
    }


# ── Product metrics ───────────────────────────────────────────────────────────

def compute_product_metrics(rows: list[dict]) -> dict:
    """
    Metrics for product team:
      top_products (top-15 by revenue),
      revenue_by_category, revenue_by_region,
      cat_by_region (stacked),
      cat_by_month (heatmap, 12 values per category),
      sku_count, avg_qty_per_order
    """
    rev_by_prod: dict[str, float] = defaultdict(float)
    rev_by_cat:  dict[str, float] = defaultdict(float)
    rev_by_reg:  dict[str, float] = defaultdict(float)

    # category × region
    cat_by_reg: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    # category × month (0-11)
    cat_by_month: dict[str, list[float]] = defaultdict(lambda: [0.0] * 12)

    total_qty = 0
    for r in rows:
        prod = r.get("Product Name") or "Unknown"
        cat  = r.get("Category") or "Other"
        reg  = r.get("Region") or "Unknown"
        val  = _safe_float(r.get("Total Price"))
        qty  = int(r.get("Quantity") or 0)
        total_qty += qty

        rev_by_prod[prod] += val
        rev_by_cat[cat]   += val
        rev_by_reg[reg]   += val
        cat_by_reg[cat][reg] += val

        try:
            m = int(_month_key(r.get("Date", "")).split("-")[1]) - 1
            if 0 <= m < 12:
                cat_by_month[cat][m] += val
        except Exception:
            pass

    top_products = sorted(rev_by_prod.items(), key=lambda x: -x[1])[:15]
    rev_by_cat   = dict(sorted(rev_by_cat.items(), key=lambda x: -x[1]))
    rev_by_reg   = dict(sorted(rev_by_reg.items(), key=lambda x: -x[1]))

    return {
        "top_products":    [(p, round(v, 2)) for p, v in top_products],
        "revenue_by_category": {k: round(v, 2) for k, v in rev_by_cat.items()},
        "revenue_by_region":   {k: round(v, 2) for k, v in rev_by_reg.items()},
        "cat_by_region":   {c: {r: round(v, 2) for r, v in d.items()} for c, d in cat_by_reg.items()},
        "cat_by_month":    {c: [round(v, 2) for v in vals] for c, vals in cat_by_month.items()},
        "sku_count":       len(rev_by_prod),
        "avg_qty_per_order": round(total_qty / len(rows), 2) if rows else 0.0,
        "top_category":    max(rev_by_cat, key=rev_by_cat.get) if rev_by_cat else "",
        "top_product":     top_products[0][0] if top_products else "",
        "top_product_rev": round(top_products[0][1], 2) if top_products else 0.0,
    }


# ── Marketing / Growth metrics ────────────────────────────────────────────────

def compute_marketing_metrics(rows: list[dict]) -> dict:
    """
    Metrics for marketing/growth:
      orders_by_payment, rev_by_payment, aov_by_payment,
      revenue_by_region, rev_reg_by_month (multi-line),
      orders_by_weekday (0=Mon),
      pay_by_category (stacked)
    """
    orders_by_pay: dict[str, int]   = defaultdict(int)
    rev_by_pay:    dict[str, float] = defaultdict(float)
    rev_by_reg:    dict[str, float] = defaultdict(float)

    # region × month
    rev_reg_month: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    # payment × category
    pay_by_cat: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    orders_by_weekday = [0] * 7  # Mon=0 … Sun=6

    for r in rows:
        pay = r.get("Payment Method") or "Unknown"
        reg = r.get("Region") or "Unknown"
        cat = r.get("Category") or "Other"
        val = _safe_float(r.get("Total Price"))
        wd  = _weekday(r.get("Date", ""))
        mk  = _month_key(r.get("Date", ""))

        orders_by_pay[pay] += 1
        rev_by_pay[pay]    += val
        rev_by_reg[reg]    += val
        rev_reg_month[reg][mk] += val
        pay_by_cat[pay][cat]   += 1
        if 0 <= wd <= 6:
            orders_by_weekday[wd] += 1

    aov_by_pay = {
        p: round(rev_by_pay[p] / orders_by_pay[p], 2)
        for p in orders_by_pay
    }
    orders_by_pay = dict(sorted(orders_by_pay.items(), key=lambda x: -x[1]))
    rev_by_reg    = dict(sorted(rev_by_reg.items(), key=lambda x: -x[1]))

    all_months = sorted({
        mk for reg_d in rev_reg_month.values() for mk in reg_d
    })

    return {
        "orders_by_payment":   dict(orders_by_pay),
        "revenue_by_payment":  {k: round(v, 2) for k, v in rev_by_pay.items()},
        "aov_by_payment":      aov_by_pay,
        "revenue_by_region":   {k: round(v, 2) for k, v in rev_by_reg.items()},
        "rev_reg_by_month":    {
            reg: {mk: round(rev_reg_month[reg].get(mk, 0.0), 2) for mk in all_months}
            for reg in rev_reg_month
        },
        "all_months":          all_months,
        "orders_by_weekday":   orders_by_weekday,
        "pay_by_category":     {p: dict(d) for p, d in pay_by_cat.items()},
        "top_region":          max(rev_by_reg, key=rev_by_reg.get) if rev_by_reg else "",
        "top_payment":         max(orders_by_pay, key=orders_by_pay.get) if orders_by_pay else "",
        "total_orders":        sum(orders_by_pay.values()),
    }
