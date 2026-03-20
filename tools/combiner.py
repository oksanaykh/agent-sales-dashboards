"""
tools/combiner.py

Assembles a single self-contained HTML file with three tab-switched dashboards.
All chart data is embedded as JSON — no server required, just open in a browser.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CHARTJS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"
MONTHS_EN   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
WEEKDAYS_EN = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

P_PURPLE = ["#534AB7","#7F77DD","#AFA9EC","#CECBF6","#3C3489","#26215C","#8580D5"]
P_TEAL   = ["#0F6E56","#1D9E75","#5DCAA5","#9FE1CB","#085041","#04342C","#2DC98A"]
P_CORAL  = ["#993C1D","#D85A30","#F0997B","#F5C4B3","#712B13","#4A1B0C","#E07050"]
P_MULTI  = ["#534AB7","#0F6E56","#993C1D","#BA7517","#3C3489","#085041","#712B13"]


def _fmt_py(v: float) -> str:
    if v >= 1_000_000: return f"${v/1_000_000:.1f}M"
    if v >= 1_000:     return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"


def _build_heatmap(cat_by_month: dict, cats: list[str]) -> str:
    all_vals = [v for vals in cat_by_month.values() for v in vals if v]
    max_val  = max(all_vals) if all_vals else 1.0
    rows = ""
    for cat in cats:
        vals = cat_by_month.get(cat, [0.0]*12)
        cells = "".join(
            f'<td style="background:rgba(29,158,117,{v/max_val:.2f});text-align:center" title="${v:,.0f}"></td>'
            for v in vals
        )
        rows += f"<tr><td style='font-size:10px;color:#6b6a65;white-space:nowrap;padding-right:6px'>{cat}</td>{cells}</tr>"
    heads = "".join(f"<th style='font-weight:500;padding:3px 2px;color:#6b6a65;text-align:center;font-size:10px'>{m}</th>" for m in MONTHS_EN)
    return f"""<div style="overflow-x:auto">
<table style="width:100%;border-collapse:collapse">
<thead><tr><th></th>{heads}</tr></thead><tbody>{rows}</tbody></table>
<p style="font-size:10px;color:#9a9991;margin-top:6px">Color = revenue (darker = higher). Hover for value.</p></div>"""


def build_combined_dashboard(
    exec_metrics: dict,
    product_metrics: dict,
    marketing_metrics: dict,
    source: str,
    date_range: tuple[str, str],
    reports_dir: str,
) -> str:

    e  = exec_metrics
    p  = product_metrics
    mk = marketing_metrics

    # exec data
    e_months   = e["months_sorted"]
    e_rev_vals = [e["revenue_by_month"][k] for k in e_months]
    e_cats     = list(e["revenue_by_category"].keys())
    e_cat_vals = [e["revenue_by_category"][c] for c in e_cats]
    e_season   = e["seasonality_index"]
    e_sc       = [P_PURPLE[0] if v >= 1 else P_PURPLE[2] for v in e_season]

    # product data
    top_names  = [x[0] for x in p["top_products"]]
    top_revs   = [x[1] for x in p["top_products"]]
    p_regs     = list(p["revenue_by_region"].keys())
    p_reg_vals = list(p["revenue_by_region"].values())
    p_cats     = list(p["cat_by_region"].keys())
    stacked_ds = [{"label":c,"data":[p["cat_by_region"].get(c,{}).get(r,0) for r in p_regs],
                   "backgroundColor":P_TEAL[i%len(P_TEAL)],"stack":"s"}
                  for i,c in enumerate(p_cats)]
    heat_html  = _build_heatmap(p["cat_by_month"], p_cats)

    # marketing data
    pays        = list(mk["orders_by_payment"].keys())
    pay_orders  = [mk["orders_by_payment"][p_] for p_ in pays]
    pay_aov     = [mk["aov_by_payment"].get(p_, 0) for p_ in pays]
    m_regs      = list(mk["revenue_by_region"].keys())
    all_months  = mk["all_months"]
    reg_line_ds = [{"label":r,"data":[mk["rev_reg_by_month"].get(r,{}).get(m,0) for m in all_months],
                    "borderColor":P_CORAL[i%len(P_CORAL)],"backgroundColor":"transparent",
                    "tension":0.4,"pointRadius":2,"borderWidth":1.5}
                   for i,r in enumerate(m_regs)]
    m_cats      = sorted({c for d in mk["pay_by_category"].values() for c in d})
    pay_cat_ds  = [{"label":c,"data":[mk["pay_by_category"].get(p_,{}).get(c,0) for p_ in pays],
                    "backgroundColor":P_MULTI[i%len(P_MULTI)],"stack":"s"}
                   for i,c in enumerate(m_cats)]
    wd          = mk["orders_by_weekday"]
    wd_colors   = [P_CORAL[0] if i < 5 else P_CORAL[2] for i in range(7)]

    h_h = max(len(top_names)*32+80, 300)
    source_name = Path(source).name
    gen_ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sales Dashboard — {source_name}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f7f6f3;color:#1a1a18}}
.topbar{{background:#fff;border-bottom:.5px solid rgba(0,0,0,.08);padding:0 2rem;display:flex;align-items:center;gap:1rem;height:56px;position:sticky;top:0;z-index:100}}
.topbar-title{{font-size:15px;font-weight:600;letter-spacing:-.02em;flex:1}}
.topbar-meta{{font-size:12px;color:#9a9991}}
.switcher{{background:#fff;border-bottom:.5px solid rgba(0,0,0,.08);padding:0 2rem;display:flex;gap:0}}
.sw-btn{{font-family:inherit;font-size:13px;font-weight:500;background:none;border:none;border-bottom:2px solid transparent;padding:14px 22px 12px;cursor:pointer;color:#6b6a65;transition:color .15s,border-color .15s;display:flex;align-items:center;gap:6px}}
.sw-btn .dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.sw-btn:hover{{color:#1a1a18}}
.sw-btn.active{{color:#1a1a18;border-bottom-color:#1a1a18}}
.sw-btn[data-tab=exec].active{{border-bottom-color:#534AB7;color:#3C3489}}
.sw-btn[data-tab=product].active{{border-bottom-color:#0F6E56;color:#085041}}
.sw-btn[data-tab=marketing].active{{border-bottom-color:#993C1D;color:#712B13}}
.dashboard{{display:none;padding:2rem;max-width:1100px;margin:0 auto}}
.dashboard.active{{display:block}}
.kpi-row{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:1.5rem}}
.kpi{{background:#fff;border:.5px solid rgba(0,0,0,.08);border-radius:10px;padding:1rem 1.25rem}}
.kpi-label{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#9a9991;margin-bottom:6px}}
.kpi-value{{font-size:22px;font-weight:600;letter-spacing:-.03em}}
.kpi-sub{{font-size:11px;color:#9a9991;margin-top:4px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}
.full{{margin-bottom:16px}}
.card{{background:#fff;border:.5px solid rgba(0,0,0,.08);border-radius:10px;padding:1.25rem}}
.card-title{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#9a9991;margin-bottom:1rem}}
.chart-wrap{{position:relative;width:100%}}
footer{{text-align:center;font-size:11px;color:#9a9991;padding:2rem;border-top:.5px solid rgba(0,0,0,.06);margin-top:1rem}}
@media(max-width:700px){{.kpi-row{{grid-template-columns:1fr 1fr}}.grid2{{grid-template-columns:1fr}}.topbar{{padding:0 1rem}}.dashboard{{padding:1rem}}}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-title">Sales Analytics</div>
  <div class="topbar-meta">{source_name} &nbsp;&middot;&nbsp; {e['total_orders']:,} rows &nbsp;&middot;&nbsp; {date_range[0]} &ndash; {date_range[1]}</div>
</div>

<div class="switcher">
  <button class="sw-btn active" data-tab="exec"><span class="dot" style="background:#534AB7"></span> Executive</button>
  <button class="sw-btn" data-tab="product"><span class="dot" style="background:#0F6E56"></span> Product Team</button>
  <button class="sw-btn" data-tab="marketing"><span class="dot" style="background:#993C1D"></span> Marketing / Growth</button>
</div>

<!-- EXECUTIVE -->
<div class="dashboard active" id="tab-exec">
<div class="kpi-row">
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">Revenue</div>
    <div class="kpi-value">{_fmt_py(e['total_revenue'])}</div>
    <div class="kpi-sub">{e['total_orders']:,} orders</div>
  </div>
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">Orders</div>
    <div class="kpi-value">{e['total_orders']:,}</div>
    <div class="kpi-sub">total transactions</div>
  </div>
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">AOV</div>
    <div class="kpi-value">{_fmt_py(e['aov'])}</div>
    <div class="kpi-sub">avg order value</div>
  </div>
  <div class="kpi" style="border-top:2px solid #534AB7">
    <div class="kpi-label">Units sold</div>
    <div class="kpi-value">{e['total_units']:,}</div>
    <div class="kpi-sub">units sold</div>
  </div>
</div>
<div class="full card">
  <div class="card-title">Revenue by month</div>
  <div class="chart-wrap" style="height:220px"><canvas id="e-rev-line"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Revenue by category</div>
    <div class="chart-wrap" style="height:260px"><canvas id="e-cat-bar"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Category share</div>
    <div class="chart-wrap" style="height:260px"><canvas id="e-cat-pie"></canvas></div>
  </div>
</div>
<div class="full card">
  <div class="card-title">Seasonality index by month (1.0 = average)</div>
  <div class="chart-wrap" style="height:180px"><canvas id="e-season"></canvas></div>
</div>
</div>

<!-- PRODUCT -->
<div class="dashboard" id="tab-product">
<div class="kpi-row">
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">Top category</div>
    <div class="kpi-value" style="font-size:16px">{p['top_category']}</div>
    <div class="kpi-sub">{_fmt_py(p['revenue_by_category'].get(p['top_category'],0))}</div>
  </div>
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">Top product</div>
    <div class="kpi-value" style="font-size:13px">{p['top_product']}</div>
    <div class="kpi-sub">{_fmt_py(p['top_product_rev'])}</div>
  </div>
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">SKU count</div>
    <div class="kpi-value">{p['sku_count']:,}</div>
    <div class="kpi-sub">unique products</div>
  </div>
  <div class="kpi" style="border-top:2px solid #0F6E56">
    <div class="kpi-label">Avg qty / order</div>
    <div class="kpi-value">{p['avg_qty_per_order']}</div>
    <div class="kpi-sub">units per order</div>
  </div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Top {len(top_names)} products by revenue</div>
    <div class="chart-wrap" style="height:{h_h}px"><canvas id="p-top-bar"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Revenue by region</div>
    <div class="chart-wrap" style="height:{h_h}px"><canvas id="p-reg-bar"></canvas></div>
  </div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Categories x region (stacked)</div>
    <div class="chart-wrap" style="height:280px"><canvas id="p-cat-reg"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Heatmap: category x month</div>
    {heat_html}
  </div>
</div>
</div>

<!-- MARKETING -->
<div class="dashboard" id="tab-marketing">
<div class="kpi-row">
  <div class="kpi" style="border-top:2px solid #993C1D">
    <div class="kpi-label">Top region</div>
    <div class="kpi-value" style="font-size:15px">{mk['top_region']}</div>
    <div class="kpi-sub">{_fmt_py(mk['revenue_by_region'].get(mk['top_region'],0))}</div>
  </div>
  <div class="kpi" style="border-top:2px solid #993C1D">
    <div class="kpi-label">Top payment</div>
    <div class="kpi-value" style="font-size:15px">{mk['top_payment']}</div>
    <div class="kpi-sub">{mk['orders_by_payment'].get(mk['top_payment'],0):,} orders</div>
  </div>
  <div class="kpi" style="border-top:2px solid #993C1D">
    <div class="kpi-label">Regions</div>
    <div class="kpi-value">{len(m_regs)}</div>
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
    <div class="chart-wrap" style="height:260px"><canvas id="m-pay-donut"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">AOV by payment method</div>
    <div class="chart-wrap" style="height:260px"><canvas id="m-pay-aov"></canvas></div>
  </div>
</div>
<div class="full card">
  <div class="card-title">Revenue by region over time</div>
  <div class="chart-wrap" style="height:220px"><canvas id="m-reg-line"></canvas></div>
</div>
<div class="grid2">
  <div class="card">
    <div class="card-title">Orders by day of week</div>
    <div class="chart-wrap" style="height:200px"><canvas id="m-weekday"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">Payment method x category</div>
    <div class="chart-wrap" style="height:200px"><canvas id="m-pay-cat"></canvas></div>
  </div>
</div>
</div>

<footer>Generated by agent &middot; {gen_ts} &middot; source: {source_name}</footer>

<script src="{CHARTJS_CDN}"></script>
<script>
document.querySelectorAll('.sw-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.sw-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.dashboard').forEach(d => d.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  }});
}});

const eMonths   = {json.dumps(e_months)};
const eRevVals  = {json.dumps(e_rev_vals)};
const eCats     = {json.dumps(e_cats)};
const eCatVals  = {json.dumps(e_cat_vals)};
const eSeason   = {json.dumps(e_season)};
const eSC       = {json.dumps(e_sc)};
const topNames  = {json.dumps(top_names)};
const topRevs   = {json.dumps(top_revs)};
const pRegs     = {json.dumps(p_regs)};
const pRegVals  = {json.dumps(p_reg_vals)};
const stackedDs = {json.dumps(stacked_ds)};
const pays      = {json.dumps(pays)};
const payOrders = {json.dumps(pay_orders)};
const payAovV   = {json.dumps(pay_aov)};
const allMonths = {json.dumps(all_months)};
const regLineDs = {json.dumps(reg_line_ds)};
const payCatDs  = {json.dumps(pay_cat_ds)};
const wd        = {json.dumps(wd)};
const wdColors  = {json.dumps(wd_colors)};
const wdLabels  = {json.dumps(WEEKDAYS_EN)};
const monthsEn  = {json.dumps(MONTHS_EN)};
const totalO    = {e['total_orders']};

function fmtV(v){{ return v>=1e6?'$'+(v/1e6).toFixed(1)+'M':v>=1e3?'$'+(v/1e3).toFixed(0)+'K':'$'+v; }}

new Chart(document.getElementById('e-rev-line'),{{
  type:'line',data:{{labels:eMonths,datasets:[{{label:'Revenue',data:eRevVals,
    borderColor:'#534AB7',backgroundColor:'rgba(83,74,183,0.08)',fill:true,tension:0.4,
    pointRadius:3,pointBackgroundColor:'#534AB7'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{font:{{size:11}},maxTicksLimit:12,maxRotation:45}}}},
             y:{{ticks:{{callback:fmtV,font:{{size:11}}}}}}}}}}
}});
new Chart(document.getElementById('e-cat-bar'),{{
  type:'bar',data:{{labels:eCats,datasets:[{{data:eCatVals,
    backgroundColor:{json.dumps(P_PURPLE)},borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{font:{{size:11}}}}}},y:{{ticks:{{callback:fmtV,font:{{size:11}}}}}}}}}}
}});
new Chart(document.getElementById('e-cat-pie'),{{
  type:'doughnut',data:{{labels:eCats,datasets:[{{data:eCatVals,
    backgroundColor:{json.dumps(P_PURPLE)},borderWidth:1,borderColor:'#fff'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{font:{{size:11}},boxWidth:10}}}}}}}}
}});
new Chart(document.getElementById('e-season'),{{
  type:'bar',data:{{labels:monthsEn,datasets:[{{data:eSeason,backgroundColor:eSC,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>'Index: '+ctx.parsed.y}}}}}},
    scales:{{x:{{ticks:{{font:{{size:11}}}}}},y:{{ticks:{{font:{{size:11}}}}}}}}}}
}});
new Chart(document.getElementById('p-top-bar'),{{
  type:'bar',data:{{labels:topNames,datasets:[{{data:topRevs,backgroundColor:'#1D9E75',borderRadius:4}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{callback:fmtV,font:{{size:10}}}}}},y:{{ticks:{{font:{{size:10}}}}}}}}}}
}});
new Chart(document.getElementById('p-reg-bar'),{{
  type:'bar',data:{{labels:pRegs,datasets:[{{data:pRegVals,backgroundColor:{json.dumps(P_TEAL)},borderRadius:4}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{callback:fmtV,font:{{size:11}}}}}},y:{{ticks:{{font:{{size:11}}}}}}}}}}
}});
new Chart(document.getElementById('p-cat-reg'),{{
  type:'bar',data:{{labels:pRegs,datasets:stackedDs}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}},boxWidth:10}}}}}},
    scales:{{x:{{stacked:true,ticks:{{font:{{size:10}}}}}},
             y:{{stacked:true,ticks:{{callback:fmtV,font:{{size:10}}}}}}}}}}
}});
new Chart(document.getElementById('m-pay-donut'),{{
  type:'doughnut',data:{{labels:pays,datasets:[{{data:payOrders,
    backgroundColor:{json.dumps(P_CORAL)},borderWidth:1,borderColor:'#fff'}}]}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}},boxWidth:10}}}},
              tooltip:{{callbacks:{{label:ctx=>ctx.label+': '+(ctx.parsed/totalO*100).toFixed(1)+'%'}}}}}}}}
}});
new Chart(document.getElementById('m-pay-aov'),{{
  type:'bar',data:{{labels:pays,datasets:[{{data:payAovV,
    backgroundColor:{json.dumps(P_CORAL)},borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{font:{{size:11}}}}}},
             y:{{ticks:{{callback:v=>'$'+v.toFixed(0),font:{{size:11}}}}}}}}}}
}});
new Chart(document.getElementById('m-reg-line'),{{
  type:'line',data:{{labels:allMonths,datasets:regLineDs}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}},boxWidth:10}}}}}},
    scales:{{x:{{ticks:{{font:{{size:10}},maxTicksLimit:12,maxRotation:45}}}},
             y:{{ticks:{{callback:fmtV,font:{{size:10}}}}}}}}}}
}});
new Chart(document.getElementById('m-weekday'),{{
  type:'bar',data:{{labels:wdLabels,datasets:[{{data:wd,backgroundColor:wdColors,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{ticks:{{font:{{size:12}}}}}},y:{{ticks:{{font:{{size:11}}}}}}}}}}
}});
new Chart(document.getElementById('m-pay-cat'),{{
  type:'bar',data:{{labels:pays,datasets:payCatDs}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}},boxWidth:10}}}}}},
    scales:{{x:{{stacked:true,ticks:{{font:{{size:10}}}}}},y:{{stacked:true,ticks:{{font:{{size:10}}}}}}}}}}
}});
</script>
</body></html>"""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(reports_dir) / f"dashboard_combined_{ts}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    logger.info("Combined dashboard written: %s", out)
    return str(out)
