from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def records_json(frame: pd.DataFrame) -> str:
    return json.dumps(frame.to_dict(orient="records"), ensure_ascii=False)


def main() -> None:
    metrics = json.loads((REPORTS_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    brand_summary = pd.read_csv(REPORTS_DIR / "brand_summary.csv")
    channel_summary = pd.read_csv(REPORTS_DIR / "channel_summary.csv")
    forecast = pd.read_csv(REPORTS_DIR / "revenue_forecast.csv")
    drivers = pd.read_csv(REPORTS_DIR / "top_model_drivers.csv")
    customers = pd.read_csv(PROCESSED_DIR / "customers_scored.csv")

    risk_columns = [
        "customer_id",
        "brand",
        "region",
        "plan",
        "monthly_revenue",
        "churn_risk_score",
        "risk_segment",
        "support_tickets_90d",
        "discount_rate",
    ]
    risk_customers = customers.sort_values("churn_risk_score", ascending=False)[risk_columns].copy()
    raw_files = sorted(path.name for path in RAW_DIR.glob("*.csv"))

    dashboard_payload = {
        "metrics": metrics,
        "brands": brand_summary.to_dict(orient="records"),
        "channels": channel_summary.to_dict(orient="records"),
        "forecast": forecast.to_dict(orient="records"),
        "drivers": drivers.to_dict(orient="records"),
        "customers": risk_customers.head(500).to_dict(orient="records"),
        "rawFiles": raw_files,
    }

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Subscription Science Lab</title>
  <style>
    :root {{
      --primary: #faff69;
      --primary-active: #e6eb52;
      --ink: #ffffff;
      --body: #cccccc;
      --body-strong: #e6e6e6;
      --muted: #888888;
      --muted-soft: #5a5a5a;
      --hairline: #2a2a2a;
      --hairline-strong: #3a3a3a;
      --canvas: #0a0a0a;
      --surface-soft: #121212;
      --surface-card: #1a1a1a;
      --surface-elevated: #242424;
      --success: #22c55e;
      --warning: #f59e0b;
      --error: #ef4444;
      --blue: #3b82f6;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--canvas);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    button, input {{ font: inherit; }}
    a {{ color: inherit; }}
    .shell {{
      width: min(1320px, calc(100vw - 48px));
      margin: 0 auto;
    }}
    nav {{
      position: sticky;
      top: 0;
      z-index: 20;
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--hairline);
      background: rgba(10, 10, 10, .92);
      color: var(--body);
      font-size: 14px;
      backdrop-filter: blur(14px);
    }}
    .brand {{
      display: flex;
      gap: 10px;
      align-items: center;
      color: var(--ink);
      font-weight: 700;
    }}
    .mark {{
      width: 24px;
      height: 24px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2px;
    }}
    .mark span {{ background: var(--primary); border-radius: 2px; }}
    .nav-links {{
      display: flex;
      gap: 20px;
      align-items: center;
      color: var(--muted);
    }}
    .button {{
      min-height: 40px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 0;
      border-radius: 8px;
      padding: 12px 20px;
      background: var(--primary);
      color: #0a0a0a;
      font-size: 14px;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
    }}
    .button.secondary {{
      background: var(--surface-card);
      color: var(--ink);
      border: 1px solid var(--hairline-strong);
    }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, .92fr) minmax(420px, 1.08fr);
      gap: 48px;
      align-items: center;
      padding: 78px 0 56px;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      padding: 5px 12px;
      border-radius: 9999px;
      background: var(--surface-card);
      color: var(--primary);
      border: 1px solid var(--hairline);
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 22px 0 22px;
      max-width: 800px;
      font-size: clamp(42px, 6.3vw, 76px);
      line-height: 1.03;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .lead {{
      max-width: 760px;
      color: var(--body);
      font-size: 18px;
      line-height: 1.55;
      margin: 0;
    }}
    .hero-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 30px;
    }}
    .scene-panel {{
      min-height: 520px;
      position: relative;
      overflow: hidden;
      background: var(--surface-card);
      border: 1px solid var(--hairline);
      border-radius: 12px;
    }}
    #riskScene {{
      display: block;
      width: 100%;
      height: 520px;
    }}
    .scene-overlay {{
      position: absolute;
      left: 20px;
      right: 20px;
      bottom: 20px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      pointer-events: none;
    }}
    .scene-chip {{
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
      background: rgba(10, 10, 10, .76);
      padding: 14px;
    }}
    .scene-chip span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .scene-chip strong {{
      color: var(--primary);
      font-size: 22px;
      line-height: 1;
    }}
    main {{ padding: 0 0 80px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 24px;
      padding: 24px 0 72px;
    }}
    .stat {{
      border-top: 1px solid var(--hairline);
      padding-top: 20px;
    }}
    .stat span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
      margin-bottom: 12px;
    }}
    .stat strong {{
      color: var(--primary);
      font-size: clamp(34px, 5vw, 56px);
      line-height: 1;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .section-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(340px, .74fr);
      gap: 24px;
      margin-bottom: 24px;
    }}
    .section-grid.equal {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    section, .panel {{
      background: var(--surface-card);
      border: 1px solid var(--hairline);
      border-radius: 12px;
      padding: 28px;
      overflow-x: auto;
    }}
    section.yellow {{
      background: var(--primary);
      color: #0a0a0a;
      border-color: var(--primary);
    }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 24px;
    }}
    h2 {{
      margin: 0;
      color: inherit;
      font-size: 24px;
      line-height: 1.3;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .section-head p, .muted {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }}
    .yellow .muted {{ color: #242424; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      border-radius: 9999px;
      padding: 5px 12px;
      background: var(--surface-elevated);
      color: var(--body-strong);
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
    }}
    .yellow .badge {{
      background: #0a0a0a;
      color: var(--primary);
    }}
    .control-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 22px;
    }}
    .chip-button {{
      min-height: 36px;
      border: 1px solid var(--hairline-strong);
      border-radius: 9999px;
      background: var(--surface-elevated);
      color: var(--body);
      padding: 8px 13px;
      font-size: 13px;
      cursor: pointer;
    }}
    .chip-button.active {{
      background: var(--primary);
      color: #0a0a0a;
      border-color: var(--primary);
      font-weight: 700;
    }}
    .metric-row {{
      display: grid;
      grid-template-columns: minmax(170px, .85fr) minmax(160px, 1fr) 72px;
      gap: 18px;
      align-items: center;
      padding: 16px 0;
      border-bottom: 1px solid var(--hairline);
    }}
    .metric-row:last-child {{ border-bottom: 0; }}
    .metric-row strong {{
      display: block;
      font-size: 16px;
      line-height: 1.4;
    }}
    .metric-row span {{
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 13px;
    }}
    .metric-row b {{
      color: var(--primary);
      font-size: 18px;
      text-align: right;
    }}
    .track {{
      height: 10px;
      border-radius: 9999px;
      background: var(--surface-elevated);
      overflow: hidden;
    }}
    .fill {{
      height: 100%;
      border-radius: inherit;
      background: var(--primary);
    }}
    .score-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .score {{
      background: var(--surface-elevated);
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
      padding: 16px;
    }}
    .score span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}
    .score strong {{
      color: var(--ink);
      font-size: 28px;
      line-height: 1;
    }}
    .sim-grid {{
      display: grid;
      grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr);
      gap: 20px;
    }}
    .slider-group {{
      display: grid;
      gap: 18px;
    }}
    label {{
      display: grid;
      gap: 10px;
      color: var(--body);
      font-size: 14px;
    }}
    .label-line {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }}
    input[type="range"] {{
      width: 100%;
      accent-color: var(--primary);
    }}
    .impact-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .impact {{
      min-height: 118px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background: var(--surface-elevated);
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
      padding: 16px;
    }}
    .impact span {{ color: var(--muted); font-size: 13px; }}
    .impact strong {{
      color: var(--primary);
      font-size: clamp(26px, 4vw, 42px);
      line-height: 1;
      letter-spacing: 0;
    }}
    .viz-bars {{
      display: grid;
      gap: 13px;
    }}
    .viz-bar {{
      display: grid;
      grid-template-columns: 88px 1fr 52px;
      gap: 12px;
      align-items: center;
      color: var(--body);
      font-size: 14px;
    }}
    .forecast-modes {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      line-height: 1.45;
    }}
    th, td {{
      padding: 13px 10px;
      border-bottom: 1px solid var(--hairline);
      text-align: left;
      vertical-align: top;
      color: var(--body);
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    th:first-child, td:first-child {{ white-space: nowrap; }}
    tbody tr:hover td {{ background: var(--surface-soft); }}
    .driver {{
      display: grid;
      grid-template-columns: minmax(170px, 1fr) 132px 64px;
      gap: 14px;
      align-items: center;
      padding: 13px 0;
      border-bottom: 1px solid var(--hairline);
      font-size: 14px;
    }}
    .driver:last-child {{ border-bottom: 0; }}
    .driver code {{
      color: var(--primary);
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 14px;
      white-space: normal;
    }}
    .driver span {{ color: var(--muted); }}
    .driver strong {{ text-align: right; color: var(--ink); }}
    .source-list {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      padding: 0;
      margin: 22px 0 0;
      list-style: none;
    }}
    .source-list li {{
      background: rgba(10, 10, 10, .12);
      border: 1px solid rgba(10, 10, 10, .22);
      border-radius: 8px;
      padding: 12px;
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
    }}
    .mini-note {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    footer {{
      border-top: 1px solid var(--hairline);
      padding: 32px 0 48px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }}
    @media (max-width: 1060px) {{
      .shell {{ width: min(100vw - 32px, 1280px); }}
      header, .section-grid, .section-grid.equal, .sim-grid {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .nav-links {{ display: none; }}
    }}
    @media (max-width: 680px) {{
      header {{ padding: 52px 0 40px; }}
      #riskScene {{ height: 420px; }}
      .scene-panel {{ min-height: 420px; }}
      .scene-overlay, .stats, .score-grid, .source-list, .impact-grid {{ grid-template-columns: 1fr; }}
      section, .panel {{ padding: 20px; }}
      .metric-row, .driver, .viz-bar {{ grid-template-columns: 1fr; }}
      .metric-row b, .driver strong {{ text-align: left; }}
      th, td {{ padding: 11px 8px; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <nav aria-label="Dashboard">
      <div class="brand">
        <div class="mark" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span><span></span></div>
        Subscription Science Lab
      </div>
      <div class="nav-links" aria-hidden="true">
        <span>3D Risk Map</span>
        <span>Simulator</span>
        <span>Forecast</span>
        <span>ROI</span>
      </div>
      <a class="button" href="#simulator">Run Scenario</a>
    </nav>

    <header>
      <div>
        <span class="eyebrow">Interactive portfolio analytics</span>
        <h1>Subscription intelligence with a live retention cockpit.</h1>
        <p class="lead">Explore synthetic subscription data through a 3D churn-risk map, brand filters, risk-segment drilldowns, a retention action simulator, and scenario-based revenue forecasts.</p>
        <div class="hero-actions">
          <a class="button" href="#simulator">Try the simulator</a>
          <a class="button secondary" href="#risk">Filter customer risk</a>
        </div>
      </div>
      <div class="scene-panel" aria-label="3D churn risk constellation">
        <canvas id="riskScene"></canvas>
        <div class="scene-overlay">
          <div class="scene-chip"><span>Selected customers</span><strong id="sceneCustomers">0</strong></div>
          <div class="scene-chip"><span>Critical risk</span><strong id="sceneCritical">0</strong></div>
          <div class="scene-chip"><span>Avg risk</span><strong id="sceneAvgRisk">0%</strong></div>
        </div>
      </div>
    </header>

    <main>
      <div class="stats" aria-label="Portfolio KPIs">
        <div class="stat"><span>Rows processed</span><strong>{metrics["rows_processed"]:,}</strong></div>
        <div class="stat"><span>Total monthly revenue</span><strong>{money(metrics["total_monthly_revenue"])}</strong></div>
        <div class="stat"><span>Observed churn rate</span><strong>{pct(metrics["overall_churn_rate"])}</strong></div>
        <div class="stat"><span>Model ROC AUC</span><strong>{metrics["model_metrics"]["roc_auc"]:.2f}</strong></div>
      </div>

      <section id="risk">
        <div class="section-head">
          <div>
            <h2>Risk Explorer</h2>
            <p>Filter the portfolio by fictional brand and churn-risk segment. The 3D scene, distribution, and customer action list update together.</p>
          </div>
          <span class="badge">Live filters</span>
        </div>
        <div class="control-row" id="brandControls"></div>
        <div class="control-row" id="segmentControls"></div>
        <div class="section-grid equal">
          <div>
            <div id="brandRiskRows"></div>
          </div>
          <div>
            <div class="section-head">
              <div>
                <h2>Risk Distribution</h2>
                <p>Customer count by current risk filter.</p>
              </div>
            </div>
            <div class="viz-bars" id="riskDistribution"></div>
          </div>
        </div>
      </section>

      <div class="section-grid" id="simulator">
        <section>
          <div class="section-head">
            <div>
              <h2>Retention Action Simulator</h2>
              <p>Estimate the business impact of targeting the highest-risk customers with an incentive or proactive support play.</p>
            </div>
            <span class="badge">Interactive</span>
          </div>
          <div class="sim-grid">
            <div class="slider-group">
              <label>
                <span class="label-line"><span>Customers targeted</span><strong id="targetCountLabel"></strong></span>
                <input id="targetCount" type="range" min="25" max="300" step="25" value="100">
              </label>
              <label>
                <span class="label-line"><span>Incentive cost per customer</span><strong id="incentiveLabel"></strong></span>
                <input id="incentiveCost" type="range" min="5" max="80" step="5" value="25">
              </label>
              <label>
                <span class="label-line"><span>Expected save rate</span><strong id="saveRateLabel"></strong></span>
                <input id="saveRate" type="range" min="5" max="45" step="5" value="20">
              </label>
              <p class="mini-note">Revenue saved is estimated from six months of monthly revenue, churn probability, and expected retention save rate.</p>
            </div>
            <div class="impact-grid">
              <div class="impact"><span>Revenue protected</span><strong id="savedRevenue"></strong></div>
              <div class="impact"><span>Campaign cost</span><strong id="campaignCost"></strong></div>
              <div class="impact"><span>Net impact</span><strong id="netImpact"></strong></div>
              <div class="impact"><span>Break-even save rate</span><strong id="breakEven"></strong></div>
            </div>
          </div>
        </section>
        <section>
          <div class="section-head">
            <div>
              <h2>Highest Risk Customers</h2>
              <p>Action list filtered by the current brand and segment selection.</p>
            </div>
            <span class="badge">Top 10</span>
          </div>
          <table>
            <thead><tr><th>Customer</th><th>Brand</th><th>Plan</th><th>Revenue</th><th>Risk</th><th>Segment</th></tr></thead>
            <tbody id="customerRows"></tbody>
          </table>
        </section>
      </div>

      <div class="section-grid equal">
        <section>
          <div class="section-head">
            <div>
              <h2>Revenue Forecast</h2>
              <p>Toggle conservative, expected, and optimistic revenue paths from the existing forecast bounds.</p>
            </div>
            <span class="badge">Scenario toggle</span>
          </div>
          <div class="forecast-modes" id="forecastModes"></div>
          <div class="viz-bars" id="forecastBars"></div>
        </section>
        <section>
          <div class="section-head">
            <div>
              <h2>Top Campaign ROI</h2>
              <p>Channel performance ranked by attributed revenue after acquisition spend.</p>
            </div>
            <span class="badge">Budget view</span>
          </div>
          <table>
            <thead><tr><th>Brand</th><th>Channel</th><th>ROI</th><th>Cost / Conv.</th></tr></thead>
            <tbody id="channelRows"></tbody>
          </table>
        </section>
      </div>

      <div class="section-grid">
        <section class="yellow" id="source">
          <div class="section-head">
            <div>
              <h2>Data Source</h2>
              <p class="muted">This dashboard uses a synthetic, reproducible portfolio dataset generated by <strong>src/generate_data.py</strong>. It is not scraped from real brands and does not contain private customer data.</p>
            </div>
            <span class="badge">Synthetic dataset</span>
          </div>
          <ul class="source-list" id="sourceList"></ul>
        </section>
        <section>
          <div class="section-head">
            <div>
              <h2>Model Drivers</h2>
              <p>Largest logistic-regression coefficients from the trained churn model.</p>
            </div>
            <span class="badge">Explainability</span>
          </div>
          <div id="driverRows"></div>
        </section>
      </div>
    </main>

    <footer>
      Generated by a reproducible Python analytics pipeline. Raw inputs are generated locally, processed through ETL validation, scored with a from-scratch logistic regression model, and rendered into this interactive static dashboard.
    </footer>
  </div>

  <script id="dashboard-data" type="application/json">{json.dumps(dashboard_payload, ensure_ascii=False)}</script>
  <script type="module">
    let THREE = null;
    try {{
      THREE = await import("https://unpkg.com/three@0.160.0/build/three.module.js");
    }} catch (error) {{
      console.warn("Three.js unavailable; using canvas fallback.", error);
    }}

    const data = JSON.parse(document.getElementById("dashboard-data").textContent);
    const state = {{ brand: "All", segment: "All", forecastMode: "forecast_revenue" }};
    const segments = ["All", "low", "watch", "high", "critical"];
    const modeLabels = {{
      lower_bound: "Conservative",
      forecast_revenue: "Expected",
      upper_bound: "Optimistic"
    }};
    const moneyFmt = new Intl.NumberFormat("en-US", {{ style: "currency", currency: "USD", maximumFractionDigits: 0 }});
    const shortMoneyFmt = new Intl.NumberFormat("en-US", {{ style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 }});
    const numberFmt = new Intl.NumberFormat("en-US");
    const pctFmt = new Intl.NumberFormat("en-US", {{ style: "percent", maximumFractionDigits: 1 }});

    const brandNames = ["All", ...data.brands.map(item => item.brand)];
    const els = {{
      brandControls: document.getElementById("brandControls"),
      segmentControls: document.getElementById("segmentControls"),
      brandRiskRows: document.getElementById("brandRiskRows"),
      riskDistribution: document.getElementById("riskDistribution"),
      customerRows: document.getElementById("customerRows"),
      channelRows: document.getElementById("channelRows"),
      forecastModes: document.getElementById("forecastModes"),
      forecastBars: document.getElementById("forecastBars"),
      driverRows: document.getElementById("driverRows"),
      sourceList: document.getElementById("sourceList"),
      targetCount: document.getElementById("targetCount"),
      incentiveCost: document.getElementById("incentiveCost"),
      saveRate: document.getElementById("saveRate"),
      targetCountLabel: document.getElementById("targetCountLabel"),
      incentiveLabel: document.getElementById("incentiveLabel"),
      saveRateLabel: document.getElementById("saveRateLabel"),
      savedRevenue: document.getElementById("savedRevenue"),
      campaignCost: document.getElementById("campaignCost"),
      netImpact: document.getElementById("netImpact"),
      breakEven: document.getElementById("breakEven"),
      sceneCustomers: document.getElementById("sceneCustomers"),
      sceneCritical: document.getElementById("sceneCritical"),
      sceneAvgRisk: document.getElementById("sceneAvgRisk")
    }};

    function filteredCustomers() {{
      return data.customers.filter(customer => {{
        const brandOk = state.brand === "All" || customer.brand === state.brand;
        const segmentOk = state.segment === "All" || customer.risk_segment === state.segment;
        return brandOk && segmentOk;
      }});
    }}

    function filteredChannels() {{
      return data.channels
        .filter(row => state.brand === "All" || row.brand === state.brand)
        .sort((a, b) => b.roi - a.roi)
        .slice(0, 6);
    }}

    function createButton(label, active, onClick) {{
      const button = document.createElement("button");
      button.type = "button";
      button.className = `chip-button ${{active ? "active" : ""}}`;
      button.textContent = label;
      button.addEventListener("click", onClick);
      return button;
    }}

    function renderControls() {{
      els.brandControls.replaceChildren(...brandNames.map(brand =>
        createButton(brand, state.brand === brand, () => {{
          state.brand = brand;
          renderAll();
        }})
      ));
      els.segmentControls.replaceChildren(...segments.map(segment =>
        createButton(segment[0].toUpperCase() + segment.slice(1), state.segment === segment, () => {{
          state.segment = segment;
          renderAll();
        }})
      ));
      els.forecastModes.replaceChildren(...Object.entries(modeLabels).map(([mode, label]) =>
        createButton(label, state.forecastMode === mode, () => {{
          state.forecastMode = mode;
          renderForecast();
        }})
      ));
    }}

    function renderBrandRisk() {{
      const maxRisk = Math.max(...data.brands.map(item => item.avg_risk_score));
      const rows = data.brands
        .filter(row => state.brand === "All" || row.brand === state.brand)
        .map(row => {{
          const width = Math.max(6, row.avg_risk_score / maxRisk * 100);
          return `<div class="metric-row">
            <div><strong>${{row.brand}}</strong><span>${{numberFmt.format(row.customers)}} customers / ${{moneyFmt.format(row.monthly_revenue)}} MRR</span></div>
            <div class="track" aria-hidden="true"><div class="fill" style="width:${{width.toFixed(1)}}%"></div></div>
            <b>${{pctFmt.format(row.avg_risk_score)}}</b>
          </div>`;
        }}).join("");
      els.brandRiskRows.innerHTML = rows;
    }}

    function renderDistribution() {{
      const customers = filteredCustomers();
      const counts = Object.fromEntries(segments.filter(item => item !== "All").map(item => [item, 0]));
      customers.forEach(customer => counts[customer.risk_segment] += 1);
      const maxCount = Math.max(...Object.values(counts), 1);
      els.riskDistribution.innerHTML = Object.entries(counts).map(([segment, count]) => {{
        const width = Math.max(4, count / maxCount * 100);
        return `<div class="viz-bar">
          <strong>${{segment}}</strong>
          <div class="track"><div class="fill" style="width:${{width.toFixed(1)}}%"></div></div>
          <span>${{count}}</span>
        </div>`;
      }}).join("");
    }}

    function renderCustomers() {{
      const rows = filteredCustomers().slice(0, 10).map(customer => `<tr>
        <td>${{customer.customer_id}}</td>
        <td>${{customer.brand}}</td>
        <td>${{customer.plan}}</td>
        <td>${{moneyFmt.format(customer.monthly_revenue)}}</td>
        <td>${{customer.churn_risk_score.toFixed(2)}}</td>
        <td>${{customer.risk_segment}}</td>
      </tr>`).join("");
      els.customerRows.innerHTML = rows || `<tr><td colspan="6">No customers match this filter.</td></tr>`;
    }}

    function renderChannels() {{
      els.channelRows.innerHTML = filteredChannels().map(row => `<tr>
        <td>${{row.brand}}</td>
        <td>${{row.acquisition_channel}}</td>
        <td>${{row.roi.toFixed(2)}}x</td>
        <td>${{moneyFmt.format(row.cost_per_conversion)}}</td>
      </tr>`).join("");
    }}

    function renderForecast() {{
      const rows = data.forecast
        .filter(row => state.brand === "All" || row.brand === state.brand)
        .slice(0, 12);
      const maxValue = Math.max(...rows.map(row => row[state.forecastMode]), 1);
      els.forecastBars.innerHTML = rows.map(row => {{
        const width = Math.max(5, row[state.forecastMode] / maxValue * 100);
        return `<div class="viz-bar">
          <strong>${{row.month.slice(0, 7)}}</strong>
          <div class="track"><div class="fill" style="width:${{width.toFixed(1)}}%"></div></div>
          <span>${{shortMoneyFmt.format(row[state.forecastMode])}}</span>
        </div>`;
      }}).join("");
      renderControls();
    }}

    function renderSimulator() {{
      const targetCount = Number(els.targetCount.value);
      const incentive = Number(els.incentiveCost.value);
      const saveRate = Number(els.saveRate.value) / 100;
      const targets = filteredCustomers().slice(0, targetCount);
      const exposure = targets.reduce((sum, customer) => sum + customer.monthly_revenue * 6 * customer.churn_risk_score, 0);
      const saved = exposure * saveRate;
      const cost = targets.length * incentive;
      const net = saved - cost;
      const breakEven = exposure > 0 ? cost / exposure : 0;

      els.targetCountLabel.textContent = numberFmt.format(targetCount);
      els.incentiveLabel.textContent = moneyFmt.format(incentive);
      els.saveRateLabel.textContent = pctFmt.format(saveRate);
      els.savedRevenue.textContent = moneyFmt.format(saved);
      els.campaignCost.textContent = moneyFmt.format(cost);
      els.netImpact.textContent = moneyFmt.format(net);
      els.breakEven.textContent = pctFmt.format(breakEven);
    }}

    function renderDrivers() {{
      els.driverRows.innerHTML = data.drivers.map(row => {{
        const impact = row.coefficient > 0 ? "Raises churn risk" : "Reduces churn risk";
        return `<div class="driver">
          <code>${{row.feature}}</code>
          <span>${{impact}}</span>
          <strong>${{row.coefficient.toFixed(2)}}</strong>
        </div>`;
      }}).join("");
    }}

    function renderSource() {{
      els.sourceList.innerHTML = data.rawFiles.map(file => `<li>${{file}}</li>`).join("");
    }}

    const sceneState = initScene();
    function initFallbackScene() {{
      const canvas = document.getElementById("riskScene");
      const context = canvas.getContext("2d");
      let activeCustomers = data.customers;

      function resize() {{
        const rect = canvas.getBoundingClientRect();
        const scale = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(rect.width * scale);
        canvas.height = Math.floor(rect.height * scale);
        context.setTransform(scale, 0, 0, scale, 0, 0);
        draw();
      }}

      function draw() {{
        const rect = canvas.getBoundingClientRect();
        context.clearRect(0, 0, rect.width, rect.height);
        context.fillStyle = "#1a1a1a";
        context.fillRect(0, 0, rect.width, rect.height);
        context.strokeStyle = "#3a3a3a";
        context.lineWidth = 1;
        for (let i = 0; i < 4; i += 1) {{
          context.beginPath();
          context.ellipse(rect.width / 2, rect.height * .52, rect.width * (.28 + i * .07), rect.height * (.055 + i * .018), 0, 0, Math.PI * 2);
          context.stroke();
        }}
        const selectedIds = new Set(activeCustomers.map(customer => customer.customer_id));
        data.customers.slice(0, 240).forEach((customer, index) => {{
          const angle = index * 2.399963 + customer.churn_risk_score * 1.7;
          const radius = rect.width * (.16 + customer.churn_risk_score * .18);
          const x = rect.width / 2 + Math.cos(angle) * radius;
          const y = rect.height * .52 + Math.sin(angle) * radius * .18 - customer.churn_risk_score * rect.height * .24;
          const active = selectedIds.has(customer.customer_id);
          context.beginPath();
          context.fillStyle = active ? (customer.risk_segment === "critical" ? "#ef4444" : "#faff69") : "#5a5a5a";
          context.globalAlpha = active ? .75 : .38;
          context.arc(x, y, active ? 5 : 3, 0, Math.PI * 2);
          context.fill();
        }});
        context.globalAlpha = 1;
      }}

      window.addEventListener("resize", resize);
      resize();
      return {{
        fallback: true,
        update(customers) {{
          activeCustomers = customers;
          draw();
        }}
      }};
    }}

    function initScene() {{
      if (!THREE) {{
        return initFallbackScene();
      }}
      const canvas = document.getElementById("riskScene");
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
      camera.position.set(0, 1.45, 7.2);
      camera.lookAt(0, 0, 0);
      const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
      renderer.setClearColor(0x1a1a1a, 1);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      const group = new THREE.Group();
      group.position.y = .35;
      scene.add(group);
      const ambient = new THREE.AmbientLight(0xffffff, 0.72);
      const point = new THREE.PointLight(0xfaff69, 2.2, 18);
      point.position.set(3, 5, 6);
      scene.add(ambient, point);

      const ringMaterial = new THREE.MeshBasicMaterial({{ color: 0x3a3a3a, wireframe: true, transparent: true, opacity: .38 }});
      for (let i = 0; i < 4; i += 1) {{
        const ring = new THREE.Mesh(new THREE.TorusGeometry(1.3 + i * .55, .008, 8, 96), ringMaterial);
        ring.rotation.x = Math.PI / 2;
        group.add(ring);
      }}
      const pointGeometry = new THREE.SphereGeometry(.055, 12, 12);
      const activeMaterial = new THREE.MeshStandardMaterial({{ color: 0xfaff69, emissive: 0x777700, roughness: .35, metalness: .2 }});
      const mutedMaterial = new THREE.MeshStandardMaterial({{ color: 0x5a5a5a, emissive: 0x111111, roughness: .65, metalness: .1 }});
      const highMaterial = new THREE.MeshStandardMaterial({{ color: 0xef4444, emissive: 0x551111, roughness: .42, metalness: .15 }});
      const meshes = data.customers.slice(0, 240).map((customer, index) => {{
        const angle = index * 2.399963 + customer.churn_risk_score * 1.7;
        const radius = 1.05 + customer.churn_risk_score * 2.2;
        const mesh = new THREE.Mesh(pointGeometry, activeMaterial);
        mesh.position.set(Math.cos(angle) * radius, (customer.churn_risk_score - .35) * 3.2, Math.sin(angle) * radius);
        mesh.userData.customer = customer;
        group.add(mesh);
        return mesh;
      }});

      function resize() {{
        const rect = canvas.getBoundingClientRect();
        renderer.setSize(rect.width, rect.height, false);
        camera.aspect = rect.width / rect.height;
        camera.updateProjectionMatrix();
      }}
      window.addEventListener("resize", resize);
      resize();

      function animate() {{
        group.rotation.y += 0.0025;
        group.rotation.x = Math.sin(Date.now() * 0.00035) * 0.08;
        renderer.render(scene, camera);
        requestAnimationFrame(animate);
      }}
      animate();

      return {{ meshes, activeMaterial, mutedMaterial, highMaterial }};
    }}

    function updateScene() {{
      const customers = filteredCustomers();
      if (sceneState.fallback) {{
        sceneState.update(customers);
        els.sceneCustomers.textContent = numberFmt.format(customers.length);
        els.sceneCritical.textContent = numberFmt.format(customers.filter(customer => customer.risk_segment === "critical").length);
        els.sceneAvgRisk.textContent = customers.length ? pctFmt.format(customers.reduce((sum, customer) => sum + customer.churn_risk_score, 0) / customers.length) : "0%";
        return;
      }}
      const selectedIds = new Set(customers.map(customer => customer.customer_id));
      let visible = 0;
      let critical = 0;
      let riskSum = 0;
      sceneState.meshes.forEach(mesh => {{
        const customer = mesh.userData.customer;
        const active = selectedIds.has(customer.customer_id);
        mesh.material = active ? (customer.risk_segment === "critical" ? sceneState.highMaterial : sceneState.activeMaterial) : sceneState.mutedMaterial;
        mesh.scale.setScalar(active ? 1.45 : .72);
        if (active) {{
          visible += 1;
          riskSum += customer.churn_risk_score;
          if (customer.risk_segment === "critical") critical += 1;
        }}
      }});
      els.sceneCustomers.textContent = numberFmt.format(customers.length);
      els.sceneCritical.textContent = numberFmt.format(customers.filter(customer => customer.risk_segment === "critical").length);
      els.sceneAvgRisk.textContent = customers.length ? pctFmt.format(customers.reduce((sum, customer) => sum + customer.churn_risk_score, 0) / customers.length) : "0%";
    }}

    function renderAll() {{
      renderControls();
      renderBrandRisk();
      renderDistribution();
      renderCustomers();
      renderChannels();
      renderForecast();
      renderSimulator();
      updateScene();
    }}

    [els.targetCount, els.incentiveCost, els.saveRate].forEach(input => input.addEventListener("input", renderSimulator));
    renderDrivers();
    renderSource();
    renderAll();
  </script>
</body>
</html>"""

    (REPORTS_DIR / "dashboard.html").write_text(html_doc, encoding="utf-8")
    print("Dashboard written to reports/dashboard.html.")


if __name__ == "__main__":
    main()
