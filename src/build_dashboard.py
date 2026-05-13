from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RAW_DIR = ROOT / "data" / "raw"


ISSUE_META = {
    "failed_payment": {"owner": "Billing Ops", "urgency": "Today", "label": "Failed payment"},
    "late_fulfillment": {"owner": "Operations", "urgency": "This week", "label": "Late fulfillment"},
    "discount_margin_leak": {"owner": "Growth", "urgency": "This week", "label": "Discount leakage"},
    "support_escalation": {"owner": "Customer Success", "urgency": "Today", "label": "Support escalation"},
}


def enrich_actions(actions: pd.DataFrame) -> pd.DataFrame:
    if actions.empty:
        return actions
    enriched = actions.copy()
    enriched["primary_issue"] = enriched["issue_type"].str.split(" + ", regex=False).str[0]
    enriched["owner"] = enriched["primary_issue"].map(lambda item: ISSUE_META.get(item, {}).get("owner", "Ops"))
    enriched["urgency"] = enriched["primary_issue"].map(lambda item: ISSUE_META.get(item, {}).get("urgency", "This week"))
    enriched["issue_label"] = enriched["primary_issue"].map(lambda item: ISSUE_META.get(item, {}).get("label", item))
    return enriched


def main() -> None:
    metrics = json.loads((REPORTS_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    brief = json.loads((REPORTS_DIR / "weekly_action_brief.json").read_text(encoding="utf-8"))
    leakage = pd.read_csv(REPORTS_DIR / "revenue_leakage_report.csv")
    actions = enrich_actions(pd.read_csv(REPORTS_DIR / "action_queue.csv"))
    payments = pd.read_csv(REPORTS_DIR / "payment_recovery_summary.csv")
    sku_risk = pd.read_csv(REPORTS_DIR / "sku_risk_report.csv")
    raw_files = sorted(path.name for path in RAW_DIR.glob("*.csv"))

    payload = {
        "metrics": metrics,
        "brief": brief,
        "leakage": leakage.to_dict(orient="records"),
        "actions": actions.to_dict(orient="records"),
        "payments": payments.to_dict(orient="records"),
        "skuRisk": sku_risk.to_dict(orient="records"),
        "rawFiles": raw_files,
        "issueMeta": ISSUE_META,
    }

    html_doc = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Subscription Revenue Recovery Control Tower</title>
  <style>
    :root {
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
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--canvas);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    button { font: inherit; }
    .shell {
      width: min(1320px, calc(100vw - 48px));
      margin: 0 auto;
    }
    nav {
      position: sticky;
      top: 0;
      z-index: 20;
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--hairline);
      background: rgba(10, 10, 10, .94);
      color: var(--body);
      font-size: 14px;
      backdrop-filter: blur(14px);
    }
    .brand {
      display: flex;
      gap: 10px;
      align-items: center;
      color: var(--ink);
      font-weight: 700;
    }
    .mark {
      width: 24px;
      height: 24px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2px;
    }
    .mark span { background: var(--primary); border-radius: 2px; }
    .nav-links {
      display: flex;
      gap: 20px;
      align-items: center;
      color: var(--muted);
    }
    .nav-links a {
      color: inherit;
      text-decoration: none;
    }
    .button {
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
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
    }
    header {
      display: grid;
      grid-template-columns: minmax(0, .95fr) minmax(420px, 1.05fr);
      gap: 32px;
      align-items: stretch;
      padding: 72px 0 42px;
    }
    .eyebrow {
      display: inline-flex;
      width: fit-content;
      padding: 5px 12px;
      border-radius: 9999px;
      background: var(--surface-card);
      color: var(--primary);
      border: 1px solid var(--hairline);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
    }
    h1 {
      margin: 22px 0;
      max-width: 820px;
      font-size: clamp(40px, 5.8vw, 72px);
      line-height: 1.03;
      font-weight: 700;
      letter-spacing: 0;
    }
    .lead {
      max-width: 760px;
      color: var(--body);
      font-size: 18px;
      line-height: 1.55;
      margin: 0;
    }
    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 28px;
    }
    .button.secondary {
      background: var(--surface-card);
      color: var(--ink);
      border: 1px solid var(--hairline-strong);
    }
    .brief-panel, section {
      background: var(--surface-card);
      border: 1px solid var(--hairline);
      border-radius: 12px;
      padding: 28px;
      overflow-x: auto;
    }
    .brief-panel {
      display: grid;
      align-content: space-between;
      gap: 24px;
    }
    .brief-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
    }
    h2 {
      margin: 0;
      color: inherit;
      font-size: 24px;
      line-height: 1.3;
      font-weight: 700;
      letter-spacing: 0;
    }
    .muted, .brief-head p, .section-head p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      border-radius: 9999px;
      padding: 5px 12px;
      background: var(--surface-elevated);
      color: var(--body-strong);
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
    }
    .hero-metric {
      border-top: 1px solid var(--hairline);
      padding-top: 20px;
    }
    .hero-metric span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 10px;
    }
    .hero-metric strong {
      color: var(--primary);
      font-size: clamp(42px, 6vw, 72px);
      line-height: 1;
      font-weight: 700;
      letter-spacing: 0;
    }
    .brief-list {
      display: grid;
      gap: 12px;
    }
    .brief-item {
      display: grid;
      grid-template-columns: 36px minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 14px;
      background: var(--surface-elevated);
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
    }
    .rank {
      width: 28px;
      height: 28px;
      display: inline-grid;
      place-items: center;
      border-radius: 9999px;
      background: var(--primary);
      color: #0a0a0a;
      font-weight: 800;
      font-size: 13px;
    }
    .brief-item strong {
      display: block;
      color: var(--ink);
      line-height: 1.35;
    }
    .brief-item span {
      color: var(--muted);
      font-size: 13px;
    }
    .brief-item b {
      color: var(--primary);
      white-space: nowrap;
    }
    main { padding-bottom: 80px; }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 24px;
      padding: 20px 0 48px;
    }
    .kpi {
      border-top: 1px solid var(--hairline);
      padding-top: 18px;
    }
    .kpi span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 10px;
    }
    .kpi strong {
      color: var(--primary);
      font-size: clamp(30px, 4.4vw, 52px);
      line-height: 1;
      font-weight: 700;
      letter-spacing: 0;
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 22px;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(360px, .9fr);
      gap: 24px;
      margin-bottom: 24px;
    }
    .grid.equal {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .leak-stack {
      display: grid;
      gap: 12px;
    }
    .leak-row {
      display: grid;
      grid-template-columns: 38px minmax(220px, 1fr) minmax(180px, .8fr) 120px;
      gap: 14px;
      align-items: center;
      padding: 16px 0;
      border-bottom: 1px solid var(--hairline);
    }
    .leak-row:last-child { border-bottom: 0; }
    .leak-row strong { display: block; }
    .leak-row small { color: var(--muted); line-height: 1.45; }
    .bar-track {
      height: 10px;
      background: var(--surface-elevated);
      border-radius: 9999px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      background: var(--primary);
      border-radius: inherit;
    }
    .amount {
      color: var(--primary);
      font-weight: 800;
      text-align: right;
      white-space: nowrap;
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }
    .chip {
      min-height: 36px;
      border: 1px solid var(--hairline-strong);
      border-radius: 9999px;
      background: var(--surface-elevated);
      color: var(--body);
      padding: 8px 13px;
      font-size: 13px;
      cursor: pointer;
    }
    .chip.active {
      background: var(--primary);
      color: #0a0a0a;
      border-color: var(--primary);
      font-weight: 800;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      line-height: 1.45;
    }
    th, td {
      padding: 13px 10px;
      border-bottom: 1px solid var(--hairline);
      text-align: left;
      vertical-align: top;
      color: var(--body);
    }
    th {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0;
    }
    td:first-child, th:first-child { white-space: nowrap; }
    tbody tr:hover td { background: var(--surface-soft); }
    .owner-pill {
      display: inline-flex;
      border-radius: 9999px;
      padding: 4px 10px;
      background: var(--surface-elevated);
      border: 1px solid var(--hairline-strong);
      color: var(--body-strong);
      font-size: 12px;
      white-space: nowrap;
    }
    .recovery-grid {
      display: grid;
      gap: 13px;
    }
    .recovery-row {
      display: grid;
      grid-template-columns: 170px 1fr 90px;
      gap: 12px;
      align-items: center;
      color: var(--body);
      font-size: 14px;
    }
    .source-list {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      padding: 0;
      margin: 0;
      list-style: none;
    }
    .source-list li {
      background: var(--surface-elevated);
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
      padding: 12px;
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      color: var(--body);
    }
    footer {
      border-top: 1px solid var(--hairline);
      padding: 32px 0 48px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }
    @media (max-width: 1060px) {
      .shell { width: min(100vw - 32px, 1280px); }
      header, .grid, .grid.equal { grid-template-columns: 1fr; }
      .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .nav-links { display: none; }
      .leak-row { grid-template-columns: 38px minmax(0, 1fr); }
      .leak-row .amount { text-align: left; }
    }
    @media (max-width: 680px) {
      header { padding: 48px 0 34px; }
      .kpi-grid, .source-list { grid-template-columns: 1fr; }
      section, .brief-panel { padding: 20px; }
      .brief-item, .recovery-row { grid-template-columns: 1fr; }
      .amount { text-align: left; }
      table, thead, tbody, tr, th, td {
        display: block;
      }
      thead {
        display: none;
      }
      tbody {
        display: grid;
        gap: 12px;
      }
      tbody tr {
        border: 1px solid var(--hairline-strong);
        border-radius: 8px;
        background: var(--surface-elevated);
        padding: 14px;
      }
      th, td {
        border-bottom: 0;
        padding: 0;
      }
      td {
        display: grid;
        grid-template-columns: 92px minmax(0, 1fr);
        gap: 12px;
        white-space: normal;
        overflow-wrap: anywhere;
        align-items: start;
      }
      td + td {
        margin-top: 10px;
      }
      td::before {
        content: attr(data-label);
        color: var(--muted);
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
      }
      td:first-child, th:first-child {
        white-space: normal;
      }
      tbody tr:hover td {
        background: transparent;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <nav aria-label="Control tower">
      <div class="brand">
        <div class="mark" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span><span></span></div>
        Revenue Recovery Control Tower
      </div>
      <div class="nav-links">
        <a href="#leakage">Leakage</a>
        <a href="#queue">Action Queue</a>
        <a href="#payments">Payments</a>
        <a href="#inventory">Inventory</a>
      </div>
      <a class="button" href="#queue">Open Queue</a>
    </nav>

    <header>
      <div>
        <span class="eyebrow">Monday morning ops brief</span>
        <h1>Find subscription revenue leaks before they become churn.</h1>
        <p class="lead">A decision cockpit for e-commerce subscription teams: detect where money is leaking, explain why, assign an owner, and rank the next best recovery actions.</p>
        <div class="hero-actions">
          <a class="button" href="#leakage">Review leakage stack</a>
          <a class="button secondary" href="#payments">Payment recovery</a>
        </div>
      </div>
      <aside class="brief-panel" aria-label="Weekly action brief">
        <div class="brief-head">
          <div>
            <h2>This Week's Exposure</h2>
            <p id="briefTopAction"></p>
          </div>
          <span class="badge" id="briefToday"></span>
        </div>
        <div class="hero-metric">
          <span>Total revenue at risk</span>
          <strong id="totalAtRisk"></strong>
        </div>
        <div class="brief-list" id="briefList"></div>
      </aside>
    </header>

    <main>
      <div class="kpi-grid" aria-label="Executive KPIs">
        <div class="kpi"><span>Action queue</span><strong id="kpiActions"></strong></div>
        <div class="kpi"><span>Leak categories</span><strong id="kpiCategories"></strong></div>
        <div class="kpi"><span>Open failed payments</span><strong id="kpiFailedPayments"></strong></div>
        <div class="kpi"><span>SKU margin exposure</span><strong id="kpiSkuExposure"></strong></div>
      </div>

      <section id="leakage">
        <div class="section-head">
          <div>
            <h2>Revenue Leakage Stack</h2>
            <p>Ranked by estimated financial impact across campaign quality, fulfillment, stockouts, support, discounts, and payments.</p>
          </div>
          <span class="badge">Prioritized</span>
        </div>
        <div class="leak-stack" id="leakageRows"></div>
      </section>

      <div class="grid" id="queue">
        <section>
          <div class="section-head">
            <div>
              <h2>Recovery Action Queue</h2>
              <p>One row per customer, deduplicated across overlapping issues and sorted by expected value.</p>
            </div>
            <span class="badge" id="queueCount"></span>
          </div>
          <div class="controls" id="ownerControls"></div>
          <div class="controls" id="urgencyControls"></div>
          <table>
            <thead><tr><th>Customer</th><th>Issue</th><th>Owner</th><th>Value</th><th>Action</th></tr></thead>
            <tbody id="actionRows"></tbody>
          </table>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>What The Queue Is Telling Us</h2>
              <p>Operational patterns behind the highest-value recovery work.</p>
            </div>
            <span class="badge">Signal</span>
          </div>
          <div class="recovery-grid" id="issueMix"></div>
        </section>
      </div>

      <div class="grid equal">
        <section id="payments">
          <div class="section-head">
            <div>
              <h2>Failed Payment Recovery</h2>
              <p>Open failed invoices by decline reason, separated from voluntary churn.</p>
            </div>
            <span class="badge">Billing Ops</span>
          </div>
          <div class="recovery-grid" id="paymentRows"></div>
        </section>

        <section id="inventory">
          <div class="section-head">
            <div>
              <h2>SKU Stockout Exposure</h2>
              <p>Forecasted demand shortfalls ranked by margin at risk.</p>
            </div>
            <span class="badge">Inventory</span>
          </div>
          <table>
            <thead><tr><th>SKU</th><th>Brand</th><th>Shortfall</th><th>Risk</th><th>Margin at Risk</th></tr></thead>
            <tbody id="skuRows"></tbody>
          </table>
        </section>
      </div>

      <section>
        <div class="section-head">
          <div>
            <h2>Data Sources</h2>
            <p>Generated synthetic feeds used by the control tower pipeline.</p>
          </div>
          <span class="badge">Synthetic</span>
        </div>
        <ul class="source-list" id="sourceList"></ul>
      </section>
    </main>

    <footer>
      Built from a reproducible Python pipeline: generated subscription operations data, ETL validation, churn-risk scoring, revenue leakage detection, and a prioritized recovery work queue.
    </footer>
  </div>

  <script id="dashboard-data" type="application/json">__DASHBOARD_DATA__</script>
  <script>
    const data = JSON.parse(document.getElementById("dashboard-data").textContent);
    const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
    const number = new Intl.NumberFormat("en-US");
    const percent = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 0 });
    const state = { owner: "All", urgency: "All" };

    const els = {
      totalAtRisk: document.getElementById("totalAtRisk"),
      briefTopAction: document.getElementById("briefTopAction"),
      briefToday: document.getElementById("briefToday"),
      briefList: document.getElementById("briefList"),
      kpiActions: document.getElementById("kpiActions"),
      kpiCategories: document.getElementById("kpiCategories"),
      kpiFailedPayments: document.getElementById("kpiFailedPayments"),
      kpiSkuExposure: document.getElementById("kpiSkuExposure"),
      leakageRows: document.getElementById("leakageRows"),
      ownerControls: document.getElementById("ownerControls"),
      urgencyControls: document.getElementById("urgencyControls"),
      actionRows: document.getElementById("actionRows"),
      queueCount: document.getElementById("queueCount"),
      issueMix: document.getElementById("issueMix"),
      paymentRows: document.getElementById("paymentRows"),
      skuRows: document.getElementById("skuRows"),
      sourceList: document.getElementById("sourceList")
    };

    function uniq(values) {
      return ["All", ...Array.from(new Set(values)).filter(Boolean)];
    }
    function button(label, active, handler) {
      const node = document.createElement("button");
      node.type = "button";
      node.className = `chip ${active ? "active" : ""}`;
      node.textContent = label;
      node.addEventListener("click", handler);
      return node;
    }
    function filteredActions() {
      return data.actions.filter(row => {
        const ownerOk = state.owner === "All" || row.owner === state.owner;
        const urgencyOk = state.urgency === "All" || row.urgency === state.urgency;
        return ownerOk && urgencyOk;
      });
    }
    function renderBrief() {
      els.totalAtRisk.textContent = money.format(data.brief.total_revenue_at_risk);
      els.briefTopAction.textContent = data.brief.top_recommended_action;
      els.briefToday.textContent = `${data.brief.today_actions} today`;
      els.briefList.innerHTML = data.brief.leakage_items.map(item => `
        <div class="brief-item">
          <span class="rank">${item.rank}</span>
          <div><strong>${item.leak_area}</strong><span>${item.owner} / ${item.urgency}</span></div>
          <b>${money.format(item.revenue_at_risk)}</b>
        </div>
      `).join("");
    }
    function renderKpis() {
      const failedPayments = data.payments.reduce((sum, row) => sum + Number(row.open_failed || 0), 0);
      const skuExposure = data.skuRisk.reduce((sum, row) => sum + Number(row.margin_at_risk || 0), 0);
      els.kpiActions.textContent = number.format(data.actions.length);
      els.kpiCategories.textContent = number.format(data.leakage.length);
      els.kpiFailedPayments.textContent = number.format(failedPayments);
      els.kpiSkuExposure.textContent = money.format(skuExposure);
    }
    function renderLeakage() {
      const max = Math.max(...data.leakage.map(row => row.revenue_at_risk), 1);
      els.leakageRows.innerHTML = data.leakage.map(row => {
        const width = Math.max(4, row.revenue_at_risk / max * 100);
        return `<div class="leak-row">
          <span class="rank">${row.rank}</span>
          <div><strong>${row.leak_area}</strong><small>${row.problem}</small></div>
          <div><div class="bar-track"><div class="bar-fill" style="width:${width.toFixed(1)}%"></div></div><small>${row.affected_count} affected / ${row.owner}</small></div>
          <div class="amount">${money.format(row.revenue_at_risk)}</div>
        </div>`;
      }).join("");
    }
    function renderControls() {
      els.ownerControls.replaceChildren(...uniq(data.actions.map(row => row.owner)).map(owner =>
        button(owner, owner === state.owner, () => {
          state.owner = owner;
          renderControls();
          renderActionQueue();
        })
      ));
      els.urgencyControls.replaceChildren(...uniq(data.actions.map(row => row.urgency)).map(urgency =>
        button(urgency, urgency === state.urgency, () => {
          state.urgency = urgency;
          renderControls();
          renderActionQueue();
        })
      ));
    }
    function renderActionQueue() {
      const rows = filteredActions();
      els.queueCount.textContent = `${rows.length} items`;
      els.actionRows.innerHTML = rows.slice(0, 12).map(row => `
        <tr>
          <td data-label="Customer">${row.customer_id}</td>
          <td data-label="Issue"><strong>${row.issue_label}</strong><br><span class="muted">${row.reason}</span></td>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
          <td data-label="Value">${money.format(row.expected_value)}</td>
          <td data-label="Action">${row.recommended_action}</td>
        </tr>
      `).join("") || `<tr><td data-label="Status" colspan="5">No actions match this filter.</td></tr>`;
      renderIssueMix(rows);
    }
    function renderIssueMix(rows) {
      const mix = {};
      rows.forEach(row => {
        row.issue_type.split(" + ").forEach(issue => {
          const meta = data.issueMeta[issue] || { label: issue };
          mix[meta.label] = (mix[meta.label] || 0) + 1;
        });
      });
      const max = Math.max(...Object.values(mix), 1);
      els.issueMix.innerHTML = Object.entries(mix).sort((a, b) => b[1] - a[1]).map(([label, count]) => {
        const width = Math.max(5, count / max * 100);
        return `<div class="recovery-row">
          <strong>${label}</strong>
          <div class="bar-track"><div class="bar-fill" style="width:${width.toFixed(1)}%"></div></div>
          <span>${count}</span>
        </div>`;
      }).join("");
    }
    function renderPayments() {
      const max = Math.max(...data.payments.map(row => row.open_amount), 1);
      els.paymentRows.innerHTML = data.payments.map(row => {
        const width = Math.max(5, row.open_amount / max * 100);
        return `<div class="recovery-row">
          <strong>${row.decline_reason.replaceAll("_", " ")}</strong>
          <div class="bar-track"><div class="bar-fill" style="width:${width.toFixed(1)}%"></div></div>
          <span>${money.format(row.open_amount)}</span>
        </div>`;
      }).join("");
    }
    function renderSkuRisk() {
      els.skuRows.innerHTML = data.skuRisk.slice(0, 8).map(row => `
        <tr>
          <td data-label="SKU">${row.sku}</td>
          <td data-label="Brand">${row.brand}</td>
          <td data-label="Shortfall">${number.format(row.stockout_units)} units</td>
          <td data-label="Risk">${percent.format(row.stockout_risk)}</td>
          <td data-label="Margin">${money.format(row.margin_at_risk)}</td>
        </tr>
      `).join("");
    }
    function renderSources() {
      els.sourceList.innerHTML = data.rawFiles.map(file => `<li>${file}</li>`).join("");
    }
    renderBrief();
    renderKpis();
    renderLeakage();
    renderControls();
    renderActionQueue();
    renderPayments();
    renderSkuRisk();
    renderSources();
  </script>
</body>
</html>"""
    html_doc = html_doc.replace("__DASHBOARD_DATA__", json.dumps(payload, ensure_ascii=False))
    (REPORTS_DIR / "dashboard.html").write_text(html_doc, encoding="utf-8")
    print("Dashboard written to reports/dashboard.html.")


if __name__ == "__main__":
    main()
