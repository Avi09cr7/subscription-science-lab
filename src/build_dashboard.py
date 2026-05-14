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
    playbooks = pd.read_csv(REPORTS_DIR / "recovery_playbook_roi.csv")
    experiments = pd.read_csv(REPORTS_DIR / "experiment_backlog.csv")
    owner_workload = pd.read_csv(REPORTS_DIR / "owner_workload.csv")
    scenario_plan = pd.read_csv(REPORTS_DIR / "scenario_plan.csv")
    scenario_workload = pd.read_csv(REPORTS_DIR / "scenario_workload.csv")
    scenario_actions = pd.read_csv(REPORTS_DIR / "scenario_action_plan.csv")
    scenario_summary = json.loads((REPORTS_DIR / "scenario_summary.json").read_text(encoding="utf-8"))
    segments = pd.read_csv(REPORTS_DIR / "segment_opportunity_report.csv")
    segment_issues = pd.read_csv(REPORTS_DIR / "segment_issue_matrix.csv")
    monitoring_alerts = pd.read_csv(REPORTS_DIR / "monitoring_alerts.csv")
    metric_changes = pd.read_csv(REPORTS_DIR / "weekly_metric_changes.csv")
    data_quality = pd.read_csv(REPORTS_DIR / "data_quality_scorecard.csv")
    monitoring_summary = json.loads((REPORTS_DIR / "monitoring_summary.json").read_text(encoding="utf-8"))
    raw_files = sorted(path.name for path in RAW_DIR.glob("*.csv"))

    payload = {
        "metrics": metrics,
        "brief": brief,
        "leakage": leakage.to_dict(orient="records"),
        "actions": actions.to_dict(orient="records"),
        "payments": payments.to_dict(orient="records"),
        "skuRisk": sku_risk.to_dict(orient="records"),
        "playbooks": playbooks.to_dict(orient="records"),
        "experiments": experiments.to_dict(orient="records"),
        "ownerWorkload": owner_workload.to_dict(orient="records"),
        "scenarios": scenario_plan.to_dict(orient="records"),
        "scenarioWorkload": scenario_workload.to_dict(orient="records"),
        "scenarioActions": scenario_actions.to_dict(orient="records"),
        "scenarioSummary": scenario_summary,
        "segments": segments.to_dict(orient="records"),
        "segmentIssues": segment_issues.to_dict(orient="records"),
        "monitoringAlerts": monitoring_alerts.to_dict(orient="records"),
        "metricChanges": metric_changes.to_dict(orient="records"),
        "dataQuality": data_quality.to_dict(orient="records"),
        "monitoringSummary": monitoring_summary,
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
    [id] { scroll-margin-top: 84px; }
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
      gap: 16px;
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
    tbody tr.is-selected td { background: rgba(250, 255, 105, .08); }
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
    .metric-strip {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }
    .metric-tile {
      min-height: 92px;
      display: grid;
      align-content: space-between;
      gap: 10px;
      padding: 16px;
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
      background: var(--surface-elevated);
    }
    .metric-tile span {
      color: var(--muted);
      font-size: 12px;
    }
    .metric-tile strong {
      color: var(--primary);
      font-size: 24px;
      line-height: 1;
    }
    .decision-pill {
      display: inline-flex;
      width: fit-content;
      border-radius: 9999px;
      padding: 4px 10px;
      border: 1px solid var(--hairline-strong);
      background: var(--surface-elevated);
      color: var(--body-strong);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .decision-pill.scale {
      border-color: var(--primary);
      color: var(--primary);
    }
    .decision-pill.test {
      border-color: var(--blue);
      color: #93c5fd;
    }
    .severity {
      display: inline-flex;
      width: fit-content;
      border-radius: 9999px;
      padding: 4px 10px;
      border: 1px solid var(--hairline-strong);
      background: var(--surface-elevated);
      color: var(--body-strong);
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    .severity.critical {
      border-color: var(--error);
      color: #fca5a5;
    }
    .severity.warning {
      border-color: var(--warning);
      color: #fcd34d;
    }
    .quality-pill {
      display: inline-flex;
      width: fit-content;
      border-radius: 9999px;
      padding: 4px 10px;
      border: 1px solid rgba(34, 197, 94, .55);
      color: #86efac;
      background: rgba(34, 197, 94, .08);
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    .quality-pill.review {
      border-color: var(--warning);
      color: #fcd34d;
      background: rgba(245, 158, 11, .08);
    }
    .experiment-list {
      display: grid;
      gap: 14px;
    }
    .experiment-card {
      display: grid;
      gap: 12px;
      padding: 16px;
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
      background: var(--surface-elevated);
    }
    .experiment-card strong {
      color: var(--ink);
      line-height: 1.35;
    }
    .experiment-card p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .experiment-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .experiment-meta span {
      border: 1px solid var(--hairline-strong);
      border-radius: 9999px;
      padding: 4px 9px;
      color: var(--body);
      font-size: 12px;
    }
    .segment-brief {
      display: grid;
      gap: 16px;
    }
    .segment-brief h3 {
      margin: 0;
      color: var(--ink);
      font-size: 28px;
      line-height: 1.2;
    }
    .segment-brief p {
      margin: 0;
      color: var(--body);
      line-height: 1.55;
    }
    .segment-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .segment-stat {
      border: 1px solid var(--hairline-strong);
      border-radius: 8px;
      background: var(--surface-elevated);
      padding: 12px;
    }
    .segment-stat span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 7px;
    }
    .segment-stat strong {
      color: var(--primary);
      font-size: 20px;
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
      .metric-strip { grid-template-columns: 1fr; }
      .segment-stats { grid-template-columns: 1fr; }
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
        <a href="#playbooks">Playbooks</a>
        <a href="#scenarios">Scenarios</a>
        <a href="#segments">Segments</a>
        <a href="#monitoring">Monitor</a>
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
          <a class="button secondary" href="#playbooks">Compare playbooks</a>
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
        <div class="kpi"><span>Net recovery upside</span><strong id="kpiNetImpact"></strong></div>
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

      <section id="playbooks">
        <div class="section-head">
          <div>
            <h2>Recovery Playbook ROI</h2>
            <p>Turns the action queue into an operating plan: expected save rate, cost to execute, net impact, and the decision to scale or test.</p>
          </div>
          <span class="badge">Step 3</span>
        </div>
        <div class="metric-strip" id="playbookSummary"></div>
        <table>
          <thead><tr><th>Playbook</th><th>Owner</th><th>Eligible</th><th>Net Impact</th><th>ROI</th><th>Decision</th></tr></thead>
          <tbody id="playbookRows"></tbody>
        </table>
      </section>

      <div class="grid">
        <section>
          <div class="section-head">
            <div>
              <h2>Experiment Backlog</h2>
              <p>Each playbook has a testable hypothesis, sample split, primary metric, and decision rule.</p>
            </div>
            <span class="badge">Test Plan</span>
          </div>
          <div class="experiment-list" id="experimentRows"></div>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>Owner Workload</h2>
              <p>Shows where the recovery work lands and the best next playbook for each team.</p>
            </div>
            <span class="badge">Ownership</span>
          </div>
          <table>
            <thead><tr><th>Owner</th><th>Customers</th><th>Net Impact</th><th>Best Next Playbook</th></tr></thead>
          <tbody id="ownerRows"></tbody>
        </table>
      </section>
    </div>

      <section id="scenarios">
        <div class="section-head">
          <div>
            <h2>Capacity Scenario Planner</h2>
            <p>Compares lean, balanced, and full recovery weeks using owner capacity, expected saved value, execution cost, ROI, and net impact.</p>
          </div>
          <span class="badge">Step 6</span>
        </div>
        <div class="controls" id="scenarioControls"></div>
        <div class="metric-strip" id="scenarioSummary"></div>
        <table>
          <thead><tr><th>Scenario</th><th>Actions</th><th>Covered Value</th><th>Saved Value</th><th>Cost</th><th>Net Impact</th><th>When To Use</th></tr></thead>
          <tbody id="scenarioRows"></tbody>
        </table>
      </section>

      <div class="grid">
        <section>
          <div class="section-head">
            <div>
              <h2>Scenario Owner Load</h2>
              <p>Shows how the selected plan distributes work across teams and playbooks.</p>
            </div>
            <span class="badge">Capacity</span>
          </div>
          <table>
            <thead><tr><th>Owner</th><th>Playbook</th><th>Actions</th><th>Saved Value</th><th>Net Impact</th></tr></thead>
            <tbody id="scenarioWorkloadRows"></tbody>
          </table>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>Selected Action Sample</h2>
              <p>A concrete view of the customers the selected scenario would route first.</p>
            </div>
            <span class="badge">Next Moves</span>
          </div>
          <table>
            <thead><tr><th>Customer</th><th>Owner</th><th>Playbook</th><th>Net</th><th>Action</th></tr></thead>
            <tbody id="scenarioActionRows"></tbody>
          </table>
        </section>
      </div>

      <section id="segments">
        <div class="section-head">
          <div>
            <h2>Segment Opportunity Map</h2>
            <p>Ranks brand, channel, and plan combinations by recovery value, churn risk, action density, dominant issue, and owner.</p>
          </div>
          <span class="badge">Step 4</span>
        </div>
        <div class="metric-strip" id="segmentSummary"></div>
        <table>
          <thead><tr><th>Segment</th><th>Customers</th><th>Action Rate</th><th>Value</th><th>Dominant Issue</th><th>Owner</th><th>Score</th></tr></thead>
          <tbody id="segmentRows"></tbody>
        </table>
      </section>

      <div class="grid">
        <section>
          <div class="section-head">
            <div>
              <h2>Segment Issue Mix</h2>
              <p>Shows the operational pattern inside each priority segment instead of treating every customer issue as isolated.</p>
            </div>
            <span class="badge">Root Cause</span>
          </div>
          <div class="experiment-list" id="segmentIssueRows"></div>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>Where To Start</h2>
              <p>The highest-scoring segment translated into a client-ready recommendation.</p>
            </div>
            <span class="badge">Focus</span>
          </div>
          <div class="segment-brief" id="segmentBrief"></div>
        </section>
      </div>

      <section id="monitoring">
        <div class="section-head">
          <div>
            <h2>Monitoring & Alert Console</h2>
            <p>Flags KPI movement, campaign payback gaps, payment build-up, fulfillment SLA risk, stockouts, and data-quality health.</p>
          </div>
          <span class="badge">Step 5</span>
        </div>
        <div class="metric-strip" id="monitoringSummary"></div>
        <table>
          <thead><tr><th>Severity</th><th>Owner</th><th>Alert</th><th>Metric</th><th>Impact</th><th>Action</th></tr></thead>
          <tbody id="alertRows"></tbody>
        </table>
      </section>

      <div class="grid">
        <section>
          <div class="section-head">
            <div>
              <h2>Weekly Metric Movement</h2>
              <p>Latest month compared with the trailing three-month baseline by brand.</p>
            </div>
            <span class="badge">Trend</span>
          </div>
          <table>
            <thead><tr><th>Brand</th><th>Revenue</th><th>Revenue Change</th><th>Customers</th><th>Churn Delta</th></tr></thead>
            <tbody id="metricChangeRows"></tbody>
          </table>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>Data Quality Scorecard</h2>
              <p>Pipeline checks that decide whether the dashboard is safe to trust this week.</p>
            </div>
            <span class="badge">Trust Layer</span>
          </div>
          <table>
            <thead><tr><th>Check</th><th>Status</th><th>Value</th><th>Owner</th></tr></thead>
            <tbody id="qualityRows"></tbody>
          </table>
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
    const state = { owner: "All", urgency: "All", scenario: "Balanced week" };

    const els = {
      totalAtRisk: document.getElementById("totalAtRisk"),
      briefTopAction: document.getElementById("briefTopAction"),
      briefToday: document.getElementById("briefToday"),
      briefList: document.getElementById("briefList"),
      kpiActions: document.getElementById("kpiActions"),
      kpiNetImpact: document.getElementById("kpiNetImpact"),
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
      playbookSummary: document.getElementById("playbookSummary"),
      playbookRows: document.getElementById("playbookRows"),
      experimentRows: document.getElementById("experimentRows"),
      ownerRows: document.getElementById("ownerRows"),
      scenarioControls: document.getElementById("scenarioControls"),
      scenarioSummary: document.getElementById("scenarioSummary"),
      scenarioRows: document.getElementById("scenarioRows"),
      scenarioWorkloadRows: document.getElementById("scenarioWorkloadRows"),
      scenarioActionRows: document.getElementById("scenarioActionRows"),
      segmentSummary: document.getElementById("segmentSummary"),
      segmentRows: document.getElementById("segmentRows"),
      segmentIssueRows: document.getElementById("segmentIssueRows"),
      segmentBrief: document.getElementById("segmentBrief"),
      monitoringSummary: document.getElementById("monitoringSummary"),
      alertRows: document.getElementById("alertRows"),
      metricChangeRows: document.getElementById("metricChangeRows"),
      qualityRows: document.getElementById("qualityRows"),
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
      const netImpact = data.playbooks.reduce((sum, row) => sum + Number(row.net_impact || 0), 0);
      els.kpiActions.textContent = number.format(data.actions.length);
      els.kpiNetImpact.textContent = money.format(netImpact);
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
    function decisionClass(decision) {
      if (decision.includes("Scale")) return "scale";
      if (decision.includes("test")) return "test";
      return "";
    }
    function renderPlaybooks() {
      const netImpact = data.playbooks.reduce((sum, row) => sum + Number(row.net_impact || 0), 0);
      const savedValue = data.playbooks.reduce((sum, row) => sum + Number(row.expected_saved_value || 0), 0);
      const totalCost = data.playbooks.reduce((sum, row) => sum + Number(row.total_cost || 0), 0);
      const avgRoi = totalCost ? savedValue / totalCost : 0;
      els.playbookSummary.innerHTML = [
        ["Recommended playbooks", number.format(data.playbooks.length)],
        ["Expected saved value", money.format(savedValue)],
        ["Net impact", money.format(netImpact)],
        ["Blended ROI", `${avgRoi.toFixed(1)}x`]
      ].map(([label, value]) => `
        <div class="metric-tile"><span>${label}</span><strong>${value}</strong></div>
      `).join("");

      els.playbookRows.innerHTML = data.playbooks.map(row => `
        <tr>
          <td data-label="Playbook"><strong>${row.playbook}</strong><br><span class="muted">${row.primary_metric} / ${row.speed_to_value}</span></td>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
          <td data-label="Eligible">${number.format(row.eligible_customers)}</td>
          <td data-label="Net Impact">${money.format(row.net_impact)}</td>
          <td data-label="ROI">${Number(row.roi).toFixed(1)}x</td>
          <td data-label="Decision"><span class="decision-pill ${decisionClass(row.decision)}">${row.decision}</span></td>
        </tr>
      `).join("");
    }
    function renderExperiments() {
      els.experimentRows.innerHTML = data.experiments.map(row => `
        <article class="experiment-card">
          <strong>${row.experiment_id}: ${row.playbook}</strong>
          <p>${row.hypothesis}</p>
          <div class="experiment-meta">
            <span>${row.owner}</span>
            <span>${number.format(row.treatment_count)} treatment</span>
            <span>${number.format(row.control_count)} control</span>
            <span>${row.duration_days} days</span>
            <span>${percent.format(row.minimum_detectable_lift)} lift</span>
          </div>
          <p>${row.decision_rule}</p>
        </article>
      `).join("");
    }
    function renderOwnerWorkload() {
      els.ownerRows.innerHTML = data.ownerWorkload.map(row => `
        <tr>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
          <td data-label="Customers">${number.format(row.eligible_customers)}</td>
          <td data-label="Net Impact">${money.format(row.expected_net_impact)}</td>
          <td data-label="Best Next">${row.best_next_playbook}</td>
        </tr>
      `).join("");
    }
    function selectedScenario() {
      return data.scenarios.find(row => row.scenario === state.scenario) || data.scenarios[0] || {};
    }
    function orderedScenarios() {
      const order = { "Lean sprint": 1, "Balanced week": 2, "Full recovery push": 3 };
      return [...data.scenarios].sort((a, b) => (order[a.scenario] || 99) - (order[b.scenario] || 99));
    }
    function renderScenarioControls() {
      els.scenarioControls.replaceChildren(...orderedScenarios().map(row =>
        button(row.scenario, row.scenario === state.scenario, () => {
          state.scenario = row.scenario;
          renderScenarioControls();
          renderScenarios();
        })
      ));
    }
    function renderScenarios() {
      const plan = selectedScenario();
      els.scenarioSummary.innerHTML = [
        ["Selected plan", plan.scenario || "None"],
        ["Actions staffed", number.format(plan.selected_actions || 0)],
        ["Net impact", money.format(plan.net_impact || 0)],
        ["ROI after cost", `${Number(plan.roi || 0).toFixed(1)}x`]
      ].map(([label, value]) => `
        <div class="metric-tile"><span>${label}</span><strong>${value}</strong></div>
      `).join("");

      els.scenarioRows.innerHTML = orderedScenarios().map(row => `
        <tr class="${row.scenario === state.scenario ? "is-selected" : ""}">
          <td data-label="Scenario"><strong>${row.scenario}</strong><br><span class="muted">${row.description}</span></td>
          <td data-label="Actions">${number.format(row.selected_actions)}</td>
          <td data-label="Covered">${money.format(row.covered_expected_value)}</td>
          <td data-label="Saved">${money.format(row.expected_saved_value)}</td>
          <td data-label="Cost">${money.format(row.execution_cost)}</td>
          <td data-label="Net">${money.format(row.net_impact)}<br><span class="muted">${Number(row.roi).toFixed(1)}x ROI</span></td>
          <td data-label="Use">${row.recommendation}</td>
        </tr>
      `).join("");

      const workloadRows = data.scenarioWorkload.filter(row => row.scenario === plan.scenario);
      els.scenarioWorkloadRows.innerHTML = workloadRows.map(row => `
        <tr>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
          <td data-label="Playbook">${row.playbook}</td>
          <td data-label="Actions">${number.format(row.selected_actions)}</td>
          <td data-label="Saved">${money.format(row.expected_saved_value)}</td>
          <td data-label="Net">${money.format(row.net_impact)}</td>
        </tr>
      `).join("") || `<tr><td data-label="Status" colspan="5">No positive-return actions selected.</td></tr>`;

      const actionRows = data.scenarioActions
        .filter(row => row.scenario === plan.scenario)
        .slice(0, 8);
      els.scenarioActionRows.innerHTML = actionRows.map(row => `
        <tr>
          <td data-label="Customer">${row.customer_id}<br><span class="muted">${issueLabel(row.primary_issue)}</span></td>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
          <td data-label="Playbook">${row.playbook}</td>
          <td data-label="Net">${money.format(row.net_impact)}</td>
          <td data-label="Action">${row.recommended_action}</td>
        </tr>
      `).join("") || `<tr><td data-label="Status" colspan="5">No selected actions for this scenario.</td></tr>`;
    }
    function issueLabel(issue) {
      return data.issueMeta[issue]?.label || issue.replaceAll("_", " ");
    }
    function renderSegments() {
      const topSegment = data.segments[0];
      const topValue = Math.max(...data.segments.map(row => Number(row.expected_value || 0)), 0);
      const topActionRate = Math.max(...data.segments.map(row => Number(row.action_rate || 0)), 0);
      const avgScore = data.segments.length
        ? data.segments.reduce((sum, row) => sum + Number(row.priority_score || 0), 0) / data.segments.length
        : 0;
      els.segmentSummary.innerHTML = [
        ["Priority segments", number.format(data.segments.length)],
        ["Top segment value", money.format(topValue)],
        ["Highest action rate", percent.format(topActionRate)],
        ["Avg priority score", avgScore.toFixed(1)]
      ].map(([label, value]) => `
        <div class="metric-tile"><span>${label}</span><strong>${value}</strong></div>
      `).join("");

      els.segmentRows.innerHTML = data.segments.map(row => `
        <tr>
          <td data-label="Segment"><strong>${row.segment_name}</strong><br><span class="muted">${row.recommended_playbook}</span></td>
          <td data-label="Customers">${number.format(row.customers)}</td>
          <td data-label="Action Rate">${percent.format(row.action_rate)}</td>
          <td data-label="Value">${money.format(row.expected_value)}</td>
          <td data-label="Dominant">${issueLabel(row.dominant_issue)}</td>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
          <td data-label="Score">${Number(row.priority_score).toFixed(1)}</td>
        </tr>
      `).join("");

      els.segmentIssueRows.innerHTML = data.segmentIssues.slice(0, 6).map(row => {
        const chips = Object.keys(data.issueMeta)
          .filter(issue => Number(row[issue] || 0) > 0)
          .map(issue => `<span>${issueLabel(issue)}: ${number.format(row[issue])}</span>`)
          .join("");
        return `<article class="experiment-card">
          <strong>${row.segment_name}</strong>
          <p>${number.format(row.total_issue_mentions)} issue signals across this segment.</p>
          <div class="experiment-meta">${chips}</div>
        </article>`;
      }).join("");

      els.segmentBrief.innerHTML = topSegment ? `
        <h3>${topSegment.segment_name}</h3>
        <p>${topSegment.suggested_action}</p>
        <div class="segment-stats">
          <div class="segment-stat"><span>Priority score</span><strong>${Number(topSegment.priority_score).toFixed(1)}</strong></div>
          <div class="segment-stat"><span>Expected value</span><strong>${money.format(topSegment.expected_value)}</strong></div>
          <div class="segment-stat"><span>Action density</span><strong>${percent.format(topSegment.action_rate)}</strong></div>
          <div class="segment-stat"><span>Dominant issue</span><strong>${issueLabel(topSegment.dominant_issue)}</strong></div>
        </div>
        <p>Owner: ${topSegment.owner}. Start with ${number.format(topSegment.action_customers)} queued customers inside a base of ${number.format(topSegment.customers)} subscribers.</p>
      ` : `<p>No priority segments found.</p>`;
    }
    function severityClass(severity) {
      return String(severity).toLowerCase();
    }
    function renderMonitoring() {
      const qualityRate = data.monitoringSummary.checks_run
        ? data.monitoringSummary.healthy_checks / data.monitoringSummary.checks_run
        : 0;
      const topAlert = data.monitoringSummary.top_alert || {};
      els.monitoringSummary.innerHTML = [
        ["Open alerts", number.format(data.monitoringSummary.open_alerts || 0)],
        ["Critical alerts", number.format(data.monitoringSummary.critical_alerts || 0)],
        ["Healthy checks", percent.format(qualityRate)],
        ["Top owner", topAlert.owner || "None"]
      ].map(([label, value]) => `
        <div class="metric-tile"><span>${label}</span><strong>${value}</strong></div>
      `).join("");

      els.alertRows.innerHTML = data.monitoringAlerts.slice(0, 10).map(row => `
        <tr>
          <td data-label="Severity"><span class="severity ${severityClass(row.severity)}">${row.severity}</span></td>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
          <td data-label="Alert"><strong>${row.alert_type}</strong><br><span class="muted">${row.entity}</span></td>
          <td data-label="Metric">${row.metric}<br><span class="muted">${Number(row.current_value).toFixed(2)} vs ${Number(row.baseline_value).toFixed(2)}</span></td>
          <td data-label="Impact">${money.format(row.impact_value)}</td>
          <td data-label="Action">${row.recommendation}</td>
        </tr>
      `).join("") || `<tr><td data-label="Status" colspan="6">No monitoring alerts found.</td></tr>`;
    }
    function renderMetricChanges() {
      els.metricChangeRows.innerHTML = data.metricChanges.map(row => `
        <tr>
          <td data-label="Brand"><strong>${row.brand}</strong><br><span class="muted">${row.latest_month}</span></td>
          <td data-label="Revenue">${money.format(row.current_revenue)}</td>
          <td data-label="Rev Change">${percent.format(row.revenue_change_pct)}</td>
          <td data-label="Customers">${number.format(row.current_active_customers)}<br><span class="muted">${percent.format(row.active_customer_change_pct)}</span></td>
          <td data-label="Churn Delta">${percent.format(row.churn_rate_delta)}</td>
        </tr>
      `).join("");
    }
    function renderDataQuality() {
      els.qualityRows.innerHTML = data.dataQuality.map(row => `
        <tr>
          <td data-label="Check"><strong>${row.check}</strong><br><span class="muted">${row.expectation}</span></td>
          <td data-label="Status"><span class="quality-pill ${row.status === "Healthy" ? "" : "review"}">${row.status}</span></td>
          <td data-label="Value">${number.format(row.value)}</td>
          <td data-label="Owner"><span class="owner-pill">${row.owner}</span></td>
        </tr>
      `).join("");
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
    renderPlaybooks();
    renderExperiments();
    renderOwnerWorkload();
    renderScenarioControls();
    renderScenarios();
    renderSegments();
    renderMonitoring();
    renderMetricChanges();
    renderDataQuality();
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
