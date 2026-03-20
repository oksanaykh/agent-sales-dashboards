"""
tools/dashboard_builder.py

Generates individual HTML dashboard files for each audience.
Uses Chart.js via CDN. No external Python dependencies beyond stdlib.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CHARTJS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"

PALETTE_PURPLE = ["#534AB7", "#7F77DD", "#AFA9EC", "#CECBF6", "#3C3489", "#26215C", "#8580D5"]
PALETTE_TEAL   = ["#0F6E56", "#1D9E75", "#5DCAA5", "#9FE1CB", "#085041", "#04342C", "#2DC98A"]
PALETTE_CORAL  = ["#993C1D", "#D85A30", "#F0997B", "#F5C4B3", "#712B13", "#4A1B0C", "#E07050"]
PALETTE_MULTI  = ["#534AB7", "#0F6E56", "#993C1D", "#BA7517", "#3C3489", "#085041", "#712B13"]

MONTHS_EN   = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

BASE_STYLE = """
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #f7f6f3; color: #1a1a18; }
.page { max-width: 1100px; margin: 0 auto; padding: 2rem; }
h1 { font-size: 1.4rem; font-weight: 600; margin-bottom: 1.5rem; }
h1 span { font-weight: 400; color: #6b6a65; font-size: 1rem; margin-left: .5rem; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.5rem; }
.kpi { background: #fff; border: 0.5px solid rgba(0,0,0,.08); border-radius: 10px;
       padding: 1rem 1.25rem; }
.kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: .06em;
             color: #9a9991; margin-bottom: 6px; }
.kpi-value { font-size: 22px; font-weight: 600; letter-spacing: -0.03em; }
.kpi-sub   { font-size: 11px; color: #9a9991; margin-top: 4px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.full  { margin-bottom: 16px; }
.card  { background: #fff; border: 0.5px solid rgba(0,0,0,.08); border-radius: 10px; padding: 1.25rem; }
.card-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em;
              color: #9a9991; margin-bottom: 1rem; }
.chart-wrap { position: relative; width: 100%; }
table.heat { width: 100%; border-collapse: collapse; font-size: 10px; }
table.heat th { font-weight: 500; padding: 3px 2px; color: #6b6a65; text-align: center; }
table.heat td { padding: 4px 2px; border-radius: 3px; }
table.heat td.label { font-size: 10px; color: #6b6a65; white-space: nowrap; padding-right: 6px; }
@media(max-width:700px){.kpi-row{grid-template-columns:1fr 1fr}.grid2,.grid3{grid-template-columns:1fr}}
</style>
"""


def _fmt(v: float) -> str:
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"


def _pct(a: float, b: float) -> str:
    return f"{a/b*100:.1f}%" if b else "0%"


def _colors(palette: list[str], n: int) -> list[str]:
    return [palette[i % len(palette)] for i in range(n)]


def _write(path: Path, html: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    logger.info("Written: %s", path)
    return str(path)


# ── Executive ──────────────────────────────────────────────────────────────────

def build_exec_dashboard(m: dict, reports_dir: str) -> str:
    months   = m["months_sorted"]
    rev_vals = [m["revenue_by_month"][k] for k in months]
    cats     = list(m["revenue_by_category"].keys())
    cat_vals = [m["revenue_by_category"][c] for c in cats]
    season   = m["seasonality_index"]
    season_colors = [PALETTE_PURPLE[0] if v >= 1 else PALETTE_PURPLE[2] for v in season]

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Executive — Sales Dashboard</title>
{BASE_STYLE}
</head><body><div class="page">
<h1>Executive <span>Summary</span></h1>
<div class="kpi-row">
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">Revenue</div>
    <div class="kpi-value">{_fmt(m['total_revenue'])}</div>
    <div class="kpi-sub">{m['total_orders']:,} orders</div>
  </div>
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">Orders</div>
    <div class="kpi-value">{m['total_orders']:,}</div>
    <div class="kpi-sub">total transactions</div>
  </div>
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">AOV</div>
    <div class="kpi-value">{_fmt(m['aov'])}</div>
    <div class="kpi-sub">avg order value</div>
  </div>
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">Units sold</div>
    <div class="kpi-value">{m['total_units']:,}</div>
    <div class="kpi-sub">units sold</div>
  </div>
</div>
<div class="full card">
  <div class="card-title">Revenue by month</div>
  <div class="chart-wrap" style="height:220px"><canvas id="revLine"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Revenue by category</div>
    <div class="chart-wrap" style="height:260px"><canvas id="catBar"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Category share</div>
    <div class="chart-wrap" style="height:260px"><canvas id="catPie"></canvas></div>
  </div>
</div>
<div class="full card">
  <div class="card-title">Seasonality index by month (1.0 = average)</div>
  <div class="chart-wrap" style="height:180px"><canvas id="season"></canvas></div>
</div>
</div>
<script src="{CHARTJS_CDN}"></script>
<script>
const months = {json.dumps(months)};
const revVals = {json.dumps(rev_vals)};
const cats = {json.dumps(cats)};
const catVals = {json.dumps(cat_vals)};
const season = {json.dumps(season)};
const seasonColors = {json.dumps(season_colors)};
const purplePalette = {json.dumps(PALETTE_PURPLE)};
const monthsEn = {json.dumps(MONTHS_EN)};

new Chart(document.getElementById('revLine'), {{
  type: 'line',
  data: {{ labels: months, datasets: [{{
    label: 'Revenue', data: revVals,
    borderColor: '#534AB7', backgroundColor: 'rgba(83,74,183,0.08)',
    fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#534AB7'
  }}] }},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{display:false}} }},
    scales:{{ x:{{ticks:{{font:{{size:11}},maxTicksLimit:12,maxRotation:45}}}},
              y:{{ticks:{{callback:v=>v>=1e6?'$'+(v/1e6).toFixed(1)+'M':v>=1e3?'$'+(v/1e3).toFixed(1)+'K':'$'+v,font:{{size:11}}}}}} }}
  }}
}});

new Chart(document.getElementById('catBar'), {{
  type: 'bar',
  data: {{ labels: cats, datasets: [{{ data: catVals, backgroundColor: purplePalette, borderRadius: 4 }}] }},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{display:false}} }},
    scales:{{ x:{{ticks:{{font:{{size:11}}}}}},
              y:{{ticks:{{callback:v=>v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+(v/1e3).toFixed(1)+'K',font:{{size:11}}}}}} }}
  }}
}});

new Chart(document.getElementById('catPie'), {{
  type: 'doughnut',
  data: {{ labels: cats, datasets: [{{ data: catVals, backgroundColor: purplePalette, borderWidth:1, borderColor:'#fff' }}] }},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{position:'right',labels:{{font:{{size:11}},boxWidth:10}}}} }}
  }}
}});

new Chart(document.getElementById('season'), {{
  type: 'bar',
  data: {{ labels: monthsEn, datasets: [{{ data: season, backgroundColor: seasonColors, borderRadius: 4 }}] }},
  options: {{ responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{display:false}},
              tooltip:{{callbacks:{{label:ctx=>'Index: '+ctx.parsed.y}}}} }},
    scales:{{ x:{{ticks:{{font:{{size:11}}}}}}, y:{{ticks:{{font:{{size:11}}}}}} }}
  }}
}});
</script></body></html>"""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _write(Path(reports_dir) / f"dashboard_exec_{ts}.html", html)


# ── Product ────────────────────────────────────────────────────────────────────

def build_product_dashboard(m: dict, reports_dir: str) -> str:
    top_prods = m["top_products"]
    top_names = [p[0] for p in top_prods]
    top_revs  = [p[1] for p in top_prods]
    h_height  = max(len(top_names) * 32 + 80, 300)

    regs     = list(m["revenue_by_region"].keys())
    reg_vals = list(m["revenue_by_region"].values())

    cats = list(m["cat_by_region"].keys())
    all_regs = regs

    stacked_datasets = []
    for i, cat in enumerate(cats):
        stacked_datasets.append({
            "label": cat,
            "data": [m["cat_by_region"].get(cat, {}).get(r, 0) for r in all_regs],
            "backgroundColor": PALETTE_TEAL[i % len(PALETTE_TEAL)],
            "stack": "s",
        })

    heat_html = _build_heatmap_html(m["cat_by_month"], cats)

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Product Team — Sales Dashboard</title>
{BASE_STYLE}
</head><body><div class="page">
<h1>Product Team</h1>
<div class="kpi-row">
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">Top category</div>
    <div class="kpi-value" style="font-size:16px">{m['top_category']}</div>
    <div class="kpi-sub">{_fmt(m['revenue_by_category'].get(m['top_category'],0))}</div>
  </div>
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">Top product</div>
    <div class="kpi-value" style="font-size:13px">{m['top_product']}</div>
    <div class="kpi-sub">{_fmt(m['top_product_rev'])}</div>
  </div>
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">SKU count</div>
    <div class="kpi-value">{m['sku_count']:,}</div>
    <div class="kpi-sub">unique products</div>
  </div>
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">Avg qty / order</div>
    <div class="kpi-value">{m['avg_qty_per_order']}</div>
    <div class="kpi-sub">units per order</div>
  </div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Top {len(top_names)} products by revenue</div>
    <div class="chart-wrap" style="height:{h_height}px"><canvas id="topBar"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Revenue by region</div>
    <div class="chart-wrap" style="height:{h_height}px"><canvas id="regBar"></canvas></div>
  </div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Categories x region (stacked)</div>
    <div class="chart-wrap" style="height:280px"><canvas id="catReg"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Heatmap: category x month</div>
    {heat_html}
  </div>
</div>
</div>
<script src="{CHARTJS_CDN}"></script>
<script>
const topNames = {json.dumps(top_names)};
const topRevs  = {json.dumps(top_revs)};
const regs     = {json.dumps(regs)};
const regVals  = {json.dumps(reg_vals)};
const tealPal  = {json.dumps(PALETTE_TEAL)};
const stackedDs = {json.dumps(stacked_datasets)};

new Chart(document.getElementById('topBar'), {{
  type:'bar', data:{{labels:topNames, datasets:[{{data:topRevs,backgroundColor:'#1D9E75',borderRadius:4}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{callback:v=>v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+(v/1e3).toFixed(0)+'K',font:{{size:10}}}}}},
             y:{{ticks:{{font:{{size:10}}}}}}}}}}
}});

new Chart(document.getElementById('regBar'), {{
  type:'bar', data:{{labels:regs, datasets:[{{data:regVals,backgroundColor:tealPal,borderRadius:4}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{callback:v=>v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+(v/1e3).toFixed(0)+'K',font:{{size:11}}}}}},
             y:{{ticks:{{font:{{size:11}}}}}}}}}}
}});

new Chart(document.getElementById('catReg'), {{
  type:'bar', data:{{labels:regs, datasets:stackedDs}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}},boxWidth:10}}}}}},
    scales:{{x:{{stacked:true,ticks:{{font:{{size:10}}}}}},
             y:{{stacked:true,ticks:{{callback:v=>v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+(v/1e3).toFixed(0)+'K',font:{{size:10}}}}}}}}}}
}});
</script></body></html>"""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _write(Path(reports_dir) / f"dashboard_product_{ts}.html", html)


def _build_heatmap_html(cat_by_month: dict, cats: list[str]) -> str:
    all_vals = [v for vals in cat_by_month.values() for v in vals if v]
    max_val  = max(all_vals) if all_vals else 1.0

    rows_html = ""
    for cat in cats:
        vals = cat_by_month.get(cat, [0.0] * 12)
        cells = ""
        for v in vals:
            ratio = v / max_val if max_val else 0
            cells += f'<td style="background:rgba(29,158,117,{ratio:.2f});text-align:center" title="${v:,.0f}"></td>'
        rows_html += f"<tr><td class='label'>{cat}</td>{cells}</tr>"

    headers = "".join(f"<th>{m}</th>" for m in MONTHS_EN)
    return f"""<div style="overflow-x:auto;padding-top:.5rem">
<table class="heat">
  <thead><tr><th></th>{headers}</tr></thead>
  <tbody>{rows_html}</tbody>
</table>
<p style="font-size:10px;color:#9a9991;margin-top:.5rem">Color = revenue (darker = higher). Hover for value.</p>
</div>"""


# ── Marketing ──────────────────────────────────────────────────────────────────

def build_marketing_dashboard(m: dict, reports_dir: str) -> str:
    pays        = list(m["orders_by_payment"].keys())
    pay_orders  = [m["orders_by_payment"][p] for p in pays]
    pay_aov     = [m["aov_by_payment"].get(p, 0) for p in pays]

    regs        = list(m["revenue_by_region"].keys())
    all_months  = m["all_months"]

    reg_line_datasets = []
    for i, reg in enumerate(regs):
        reg_line_datasets.append({
            "label": reg,
            "data": [m["rev_reg_by_month"].get(reg, {}).get(mk, 0) for mk in all_months],
            "borderColor": PALETTE_CORAL[i % len(PALETTE_CORAL)],
            "backgroundColor": "transparent",
            "tension": 0.4,
            "pointRadius": 2,
            "borderWidth": 1.5,
        })

    cats     = sorted({c for d in m["pay_by_category"].values() for c in d})
    pay_cat_datasets = []
    for i, cat in enumerate(cats):
        pay_cat_datasets.append({
            "label": cat,
            "data": [m["pay_by_category"].get(p, {}).get(cat, 0) for p in pays],
            "backgroundColor": PALETTE_MULTI[i % len(PALETTE_MULTI)],
            "stack": "s",
        })

    wd = m["orders_by_weekday"]
    wd_colors = [PALETTE_CORAL[0] if i < 5 else PALETTE_CORAL[2] for i in range(7)]

    total_orders = m["total_orders"]

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Marketing / Growth — Sales Dashboard</title>
{BASE_STYLE}
</head><body><div class="page">
<h1>Marketing / Growth</h1>
<div class="kpi-row">
  <div class="kpi" style="border-top:2px solid #993C1D">
    <div class="kpi-label">Top region</div>
    <div class="kpi-value" style="font-size:15px">{m['top_region']}</div>
    <div class="kpi-sub">{_fmt(m['revenue_by_region'].get(m['top_region'],0))}</div>
  </div>
  <div class="kpi" style="border-top:2px solid #993C1D">
    <div class="kpi-label">Top payment</div>
    <div class="kpi-value" style="font-size:15px">{m['top_payment']}</div>
    <div class="kpi-sub">{m['orders_by_payment'].get(m['top_payment'],0):,} orders</div>
  </div>
  <div class="kpi" style="border-top:2px solid #993C1D">
    <div class="kpi-label">Regions</div>
    <div class="kpi-value">{len(regs)}</div>
    <div class="kpi-sub">in dataset</div>
  </div>
  <div class="kpi" style="border-top:2px solid #993C1D">
    <div class="kpi-label">Payment methods</div>
    <div class="kpi-value">{len(pays)}</div>
    <div class="kpi-sub">in dataset</div>
  </div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Payment method share (orders)</div>
    <div class="chart-wrap" style="height:260px"><canvas id="payDonut"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">AOV by payment method</div>
    <div class="chart-wrap" style="height:260px"><canvas id="payAov"></canvas></div>
  </div>
</div>
<div class="full card">
  <div class="card-title">Revenue by region over time</div>
  <div class="chart-wrap" style="height:220px"><canvas id="regLine"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Orders by day of week</div>
    <div class="chart-wrap" style="height:200px"><canvas id="weekday"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Payment method x category</div>
    <div class="chart-wrap" style="height:200px"><canvas id="payCat"></canvas></div>
  </div>
</div>
</div>
<script src="{CHARTJS_CDN}"></script>
<script>
const pays        = {json.dumps(pays)};
const payOrders   = {json.dumps(pay_orders)};
const payAovVals  = {json.dumps(pay_aov)};
const allMonths   = {json.dumps(all_months)};
const regLineDs   = {json.dumps(reg_line_datasets)};
const payCatDs    = {json.dumps(pay_cat_datasets)};
const wd          = {json.dumps(wd)};
const wdColors    = {json.dumps(wd_colors)};
const wdLabels    = {json.dumps(WEEKDAYS_EN)};
const coralPal    = {json.dumps(PALETTE_CORAL)};
const totalOrders = {total_orders};

new Chart(document.getElementById('payDonut'), {{
  type:'doughnut',
  data:{{labels:pays,datasets:[{{data:payOrders,backgroundColor:coralPal,borderWidth:1,borderColor:'#fff'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},boxWidth:10}}}},
              tooltip:{{callbacks:{{label:ctx=>ctx.label+': '+(ctx.parsed/totalOrders*100).toFixed(1)+'%'}}}}}}}}
}});

new Chart(document.getElementById('payAov'), {{
  type:'bar',
  data:{{labels:pays,datasets:[{{data:payAovVals,backgroundColor:coralPal,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{font:{{size:11}}}}}},
             y:{{ticks:{{callback:v=>'$'+v.toFixed(0),font:{{size:11}}}}}}}}}}
}});

new Chart(document.getElementById('regLine'), {{
  type:'line',
  data:{{labels:allMonths,datasets:regLineDs}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}},boxWidth:10}}}}}},
    scales:{{x:{{ticks:{{font:{{size:10}},maxTicksLimit:12,maxRotation:45}}}},
             y:{{ticks:{{callback:v=>v>=1e6?'$'+(v/1e6).toFixed(1)+'M':'$'+(v/1e3).toFixed(0)+'K',font:{{size:10}}}}}}}}}}
}});

new Chart(document.getElementById('weekday'), {{
  type:'bar',
  data:{{labels:wdLabels,datasets:[{{data:wd,backgroundColor:wdColors,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{font:{{size:12}}}}}},y:{{ticks:{{font:{{size:11}}}}}}}}}}
}});

new Chart(document.getElementById('payCat'), {{
  type:'bar',
  data:{{labels:pays,datasets:payCatDs}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}},boxWidth:10}}}}}},
    scales:{{x:{{stacked:true,ticks:{{font:{{size:10}}}}}},y:{{stacked:true,ticks:{{font:{{size:10}}}}}}}}}}
}});
</script></body></html>"""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _write(Path(reports_dir) / f"dashboard_marketing_{ts}.html", html)
