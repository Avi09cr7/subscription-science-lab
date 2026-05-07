from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RAW_DIR = ROOT / "data" / "raw"


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def table_rows(frame: pd.DataFrame, columns: list[str]) -> str:
    rows = []
    for _, row in frame.iterrows():
        cells = "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in columns)
        rows.append(f"<tr>{cells}</tr>")
    return "\n".join(rows)


def risk_rows(frame: pd.DataFrame) -> str:
    max_value = max(frame["avg_risk_score"].max(), 0.001)
    rows = []
    for _, row in frame.iterrows():
        width = max(6, row["avg_risk_score"] / max_value * 100)
        rows.append(
            f"""
            <div class="metric-row">
              <div>
                <strong>{html.escape(str(row["brand"]))}</strong>
                <span>{int(row["customers"]):,} customers / {money(float(row["monthly_revenue"]))} MRR</span>
              </div>
              <div class="track" aria-hidden="true"><div class="fill" style="width:{width:.1f}%"></div></div>
              <b>{pct(float(row["avg_risk_score"]))}</b>
            </div>
            """
        )
    return "\n".join(rows)


def driver_rows(frame: pd.DataFrame) -> str:
    rows = []
    for row in frame.itertuples():
        impact = "Raises churn risk" if row.coefficient > 0 else "Reduces churn risk"
        rows.append(
            f"""
            <div class="driver">
              <code>{html.escape(row.feature)}</code>
              <span>{impact}</span>
              <strong>{row.coefficient:.2f}</strong>
            </div>
            """
        )
    return "\n".join(rows)


def main() -> None:
    metrics = json.loads((REPORTS_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    brand_summary = pd.read_csv(REPORTS_DIR / "brand_summary.csv")
    channel_summary = pd.read_csv(REPORTS_DIR / "channel_summary.csv")
    forecast = pd.read_csv(REPORTS_DIR / "revenue_forecast.csv")
    drivers = pd.read_csv(REPORTS_DIR / "top_model_drivers.csv")
    risk_scores = pd.read_csv(REPORTS_DIR / "customer_risk_scores.csv")

    model_metrics = metrics["model_metrics"]
    best_channels = channel_summary.sort_values("roi", ascending=False).head(6).copy()
    best_channels["roi"] = best_channels["roi"].map(lambda value: f"{value:.2f}x")
    best_channels["cost_per_conversion"] = best_channels["cost_per_conversion"].map(lambda value: f"${value:,.2f}")

    forecast_view = forecast.head(12).copy()
    for column in ["forecast_revenue", "lower_bound", "upper_bound"]:
        forecast_view[column] = forecast_view[column].map(lambda value: f"${value:,.0f}")

    risk_view = risk_scores[
        ["customer_id", "brand", "region", "plan", "monthly_revenue", "churn_risk_score", "risk_segment"]
    ].head(10).copy()
    risk_view["monthly_revenue"] = risk_view["monthly_revenue"].map(lambda value: f"${value:,.2f}")
    risk_view["churn_risk_score"] = risk_view["churn_risk_score"].map(lambda value: f"{value:.2f}")

    raw_files = sorted(path.name for path in RAW_DIR.glob("*.csv"))
    source_rows = "\n".join(f"<li>{html.escape(name)}</li>" for name in raw_files)

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
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--canvas);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    a {{ color: inherit; }}
    .shell {{
      width: min(1280px, calc(100vw - 48px));
      margin: 0 auto;
    }}
    nav {{
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--hairline);
      color: var(--body);
      font-size: 14px;
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
      border-radius: 8px;
      padding: 12px 20px;
      background: var(--primary);
      color: #0a0a0a;
      font-size: 14px;
      font-weight: 600;
      text-decoration: none;
    }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(360px, .85fr);
      gap: 48px;
      align-items: center;
      padding: 88px 0 64px;
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
      margin: 24px 0 24px;
      max-width: 820px;
      font-size: clamp(42px, 7vw, 72px);
      line-height: 1.05;
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
      margin-top: 32px;
    }}
    .button.secondary {{
      background: var(--surface-card);
      color: var(--ink);
      border: 1px solid var(--hairline-strong);
    }}
    .code-window {{
      background: var(--surface-card);
      border: 1px solid var(--hairline);
      border-radius: 12px;
      overflow: hidden;
    }}
    .window-bar {{
      height: 42px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      border-bottom: 1px solid var(--hairline);
      color: var(--muted);
      font-size: 13px;
    }}
    .dots {{ display: flex; gap: 7px; }}
    .dots span {{
      width: 9px;
      height: 9px;
      border-radius: 9999px;
      background: var(--hairline-strong);
    }}
    pre {{
      margin: 0;
      padding: 24px;
      overflow-x: auto;
      color: var(--body);
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 14px;
      line-height: 1.55;
      white-space: pre;
    }}
    .sql-keyword {{ color: var(--primary); }}
    .sql-fn {{ color: var(--blue); }}
    .sql-text {{ color: var(--body-strong); }}
    main {{
      padding: 0 0 80px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 24px;
      padding: 32px 0 72px;
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
      font-size: clamp(36px, 5vw, 56px);
      line-height: 1;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .section-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(320px, .72fr);
      gap: 24px;
      margin-bottom: 24px;
    }}
    section, .panel {{
      background: var(--surface-card);
      border: 1px solid var(--hairline);
      border-radius: 12px;
      padding: 28px;
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
    .metric-row {{
      display: grid;
      grid-template-columns: minmax(160px, .8fr) minmax(160px, 1fr) 72px;
      gap: 18px;
      align-items: center;
      padding: 18px 0;
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
    footer {{
      border-top: 1px solid var(--hairline);
      padding: 32px 0 48px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
    }}
    @media (max-width: 980px) {{
      .shell {{ width: min(100vw - 32px, 1280px); }}
      header, .section-grid {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .nav-links {{ display: none; }}
    }}
    @media (max-width: 640px) {{
      header {{ padding: 56px 0 40px; }}
      .stats, .score-grid, .source-list {{ grid-template-columns: 1fr; }}
      section, .panel {{ padding: 20px; }}
      .metric-row, .driver {{ grid-template-columns: 1fr; }}
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
        <span>ETL</span>
        <span>Churn</span>
        <span>Forecast</span>
        <span>ROI</span>
      </div>
      <a class="button" href="#source">Data Source</a>
    </nav>

    <header>
      <div>
        <span class="eyebrow">Portfolio analytics system</span>
        <h1>Subscription intelligence for e-commerce retention teams.</h1>
        <p class="lead">A reproducible data science project that turns subscription, support, campaign, and revenue signals into churn-risk scores, ROI decisions, and a six-month revenue forecast.</p>
        <div class="hero-actions">
          <a class="button" href="#risk">Review churn risk</a>
          <a class="button secondary" href="#source">Where the data comes from</a>
        </div>
      </div>
      <div class="code-window" aria-label="Data pipeline query preview">
        <div class="window-bar">
          <div class="dots" aria-hidden="true"><span></span><span></span><span></span></div>
          <span>pipeline.sql</span>
        </div>
        <pre><span class="sql-keyword">SELECT</span>
  brand,
  <span class="sql-fn">avg</span>(churn_risk_score) <span class="sql-keyword">AS</span> risk,
  <span class="sql-fn">sum</span>(monthly_revenue) <span class="sql-keyword">AS</span> mrr
<span class="sql-keyword">FROM</span> <span class="sql-text">customers_scored</span>
<span class="sql-keyword">WHERE</span> validation_status = <span class="sql-text">'passed'</span>
<span class="sql-keyword">GROUP BY</span> brand
<span class="sql-keyword">ORDER BY</span> risk <span class="sql-keyword">DESC</span>;</pre>
      </div>
    </header>

    <main>
      <div class="stats" aria-label="Portfolio KPIs">
        <div class="stat"><span>Rows processed</span><strong>{metrics["rows_processed"]:,}</strong></div>
        <div class="stat"><span>Total monthly revenue</span><strong>{money(metrics["total_monthly_revenue"])}</strong></div>
        <div class="stat"><span>Observed churn rate</span><strong>{pct(metrics["overall_churn_rate"])}</strong></div>
        <div class="stat"><span>Model ROC AUC</span><strong>{model_metrics["roc_auc"]:.2f}</strong></div>
      </div>

      <div class="section-grid" id="source">
        <section class="yellow">
          <div class="section-head">
            <div>
              <h2>Data Source</h2>
              <p class="muted">This dashboard uses a synthetic, reproducible portfolio dataset generated by <strong>src/generate_data.py</strong>. It is not scraped from real brands and does not contain private customer data.</p>
            </div>
            <span class="badge">Synthetic dataset</span>
          </div>
          <ul class="source-list">{source_rows}</ul>
        </section>
        <section>
          <div class="section-head">
            <div>
              <h2>Quality Gates</h2>
              <p>ETL checks run before model scoring or reporting outputs are trusted.</p>
            </div>
            <span class="badge">Passed</span>
          </div>
          <table>
            <tbody>
              {"".join(f"<tr><td>{html.escape(check.replace('_', ' ').title())}</td><td>Pass</td></tr>" for check in metrics["validation_checks"])}
            </tbody>
          </table>
        </section>
      </div>

      <div class="section-grid" id="risk">
        <section>
          <div class="section-head">
            <div>
              <h2>Brand Churn Risk</h2>
              <p>Average model risk score by brand, paired with customer count and monthly recurring revenue.</p>
            </div>
            <span class="badge">Ranked</span>
          </div>
          {risk_rows(brand_summary)}
        </section>
        <section>
          <div class="section-head">
            <div>
              <h2>Model Evaluation</h2>
              <p>Threshold tuned for retention recall so teams catch more customers before cancellation.</p>
            </div>
            <span class="badge">Threshold {model_metrics["decision_threshold"]:.2f}</span>
          </div>
          <div class="score-grid">
            <div class="score"><span>Accuracy</span><strong>{model_metrics["accuracy"]:.2f}</strong></div>
            <div class="score"><span>Precision</span><strong>{model_metrics["precision"]:.2f}</strong></div>
            <div class="score"><span>Recall</span><strong>{model_metrics["recall"]:.2f}</strong></div>
            <div class="score"><span>F1</span><strong>{model_metrics["f1"]:.2f}</strong></div>
          </div>
        </section>
      </div>

      <div class="section-grid">
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
            <tbody>{table_rows(best_channels, ["brand", "acquisition_channel", "roi", "cost_per_conversion"])}</tbody>
          </table>
        </section>
        <section>
          <div class="section-head">
            <div>
              <h2>Strongest Churn Drivers</h2>
              <p>Largest logistic-regression coefficients from the trained churn model.</p>
            </div>
            <span class="badge">Model explainability</span>
          </div>
          {driver_rows(drivers)}
        </section>
      </div>

      <section>
        <div class="section-head">
          <div>
            <h2>Highest Risk Customers</h2>
            <p>Top scored accounts for retention intervention, sorted by churn-risk score.</p>
          </div>
          <span class="badge">Action list</span>
        </div>
        <table>
          <thead><tr><th>Customer</th><th>Brand</th><th>Region</th><th>Plan</th><th>Revenue</th><th>Risk</th><th>Segment</th></tr></thead>
          <tbody>{table_rows(risk_view, ["customer_id", "brand", "region", "plan", "monthly_revenue", "churn_risk_score", "risk_segment"])}</tbody>
        </table>
      </section>

      <section>
        <div class="section-head">
          <div>
            <h2>Revenue Forecast Preview</h2>
            <p>Six-month projection built from historical monthly subscription revenue by brand.</p>
          </div>
          <span class="badge">Next 6 months</span>
        </div>
        <table>
          <thead><tr><th>Month</th><th>Brand</th><th>Forecast</th><th>Lower</th><th>Upper</th></tr></thead>
          <tbody>{table_rows(forecast_view, ["month", "brand", "forecast_revenue", "lower_bound", "upper_bound"])}</tbody>
        </table>
      </section>
    </main>

    <footer>
      Generated by a reproducible Python analytics pipeline. Raw inputs are generated locally, processed through ETL validation, scored with a from-scratch logistic regression model, and rendered into this HTML dashboard.
    </footer>
  </div>
</body>
</html>"""

    (REPORTS_DIR / "dashboard.html").write_text(html_doc, encoding="utf-8")
    print("Dashboard written to reports/dashboard.html.")


if __name__ == "__main__":
    main()
