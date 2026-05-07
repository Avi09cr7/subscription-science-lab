from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def bar_rows(frame: pd.DataFrame, label_col: str, value_col: str, formatter=pct) -> str:
    max_value = max(frame[value_col].max(), 0.001)
    rows = []
    for _, row in frame.iterrows():
        width = max(4, row[value_col] / max_value * 100)
        rows.append(
            f"""
            <div class="bar-row">
              <span>{html.escape(str(row[label_col]))}</span>
              <div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>
              <strong>{formatter(float(row[value_col]))}</strong>
            </div>
            """
        )
    return "\n".join(rows)


def table_rows(frame: pd.DataFrame, columns: list[str]) -> str:
    rows = []
    for _, row in frame.iterrows():
        cells = "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in columns)
        rows.append(f"<tr>{cells}</tr>")
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

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Subscription Science Lab</title>
  <style>
    :root {{
      --ink: #17211c;
      --muted: #617069;
      --line: #d9e1dc;
      --panel: #ffffff;
      --soft: #f5f7f2;
      --accent: #0f766e;
      --accent-2: #b45309;
      --accent-3: #4338ca;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--soft);
    }}
    header {{
      padding: 40px 5vw 26px;
      background: #10231f;
      color: #fff;
    }}
    header p {{ max-width: 860px; color: #d7e2dc; font-size: 1rem; line-height: 1.6; }}
    h1 {{ margin: 0 0 12px; font-size: clamp(2rem, 5vw, 4.5rem); letter-spacing: 0; }}
    h2 {{ margin: 0 0 16px; font-size: 1.15rem; }}
    main {{ padding: 24px 5vw 48px; }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .kpi, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(23, 33, 28, 0.05);
    }}
    .kpi {{ padding: 18px; }}
    .kpi span {{ display: block; color: var(--muted); font-size: .82rem; margin-bottom: 8px; }}
    .kpi strong {{ font-size: 1.55rem; }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr);
      gap: 18px;
      align-items: start;
    }}
    section {{ padding: 20px; margin-bottom: 18px; }}
    .bar-row {{
      display: grid;
      grid-template-columns: 150px minmax(120px, 1fr) 64px;
      gap: 12px;
      align-items: center;
      padding: 9px 0;
      border-bottom: 1px solid #edf1ee;
      font-size: .92rem;
    }}
    .bar-row:last-child {{ border-bottom: 0; }}
    .bar-track {{ height: 10px; background: #e8eee9; border-radius: 99px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); }}
    table {{ width: 100%; border-collapse: collapse; font-size: .86rem; }}
    th, td {{ padding: 10px 9px; border-bottom: 1px solid #edf1ee; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 700; }}
    .driver {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 9px 0;
      border-bottom: 1px solid #edf1ee;
      font-size: .92rem;
    }}
    .driver:last-child {{ border-bottom: 0; }}
    .driver code {{ white-space: normal; color: var(--accent-3); }}
    footer {{ padding: 0 5vw 34px; color: var(--muted); font-size: .86rem; }}
    @media (max-width: 860px) {{
      .kpis, .grid {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 1fr; gap: 6px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Subscription Science Lab</h1>
    <p>Churn-risk modeling, ETL quality gates, campaign ROI, and revenue forecasting for a multi-brand e-commerce subscription portfolio.</p>
  </header>
  <main>
    <div class="kpis">
      <div class="kpi"><span>Rows processed</span><strong>{metrics["rows_processed"]:,}</strong></div>
      <div class="kpi"><span>Monthly revenue</span><strong>{money(metrics["total_monthly_revenue"])}</strong></div>
      <div class="kpi"><span>Overall churn</span><strong>{pct(metrics["overall_churn_rate"])}</strong></div>
      <div class="kpi"><span>Model ROC AUC</span><strong>{model_metrics["roc_auc"]:.2f}</strong></div>
    </div>
    <div class="grid">
      <section>
        <h2>Brand Churn Risk</h2>
        {bar_rows(brand_summary, "brand", "avg_risk_score")}
      </section>
      <section>
        <h2>Model Evaluation</h2>
        <table>
          <tbody>
            <tr><th>Accuracy</th><td>{model_metrics["accuracy"]:.2f}</td></tr>
            <tr><th>Precision</th><td>{model_metrics["precision"]:.2f}</td></tr>
            <tr><th>Recall</th><td>{model_metrics["recall"]:.2f}</td></tr>
            <tr><th>F1</th><td>{model_metrics["f1"]:.2f}</td></tr>
          </tbody>
        </table>
      </section>
    </div>
    <div class="grid">
      <section>
        <h2>Top Campaign ROI</h2>
        <table>
          <thead><tr><th>Brand</th><th>Channel</th><th>ROI</th><th>Cost / Conv.</th></tr></thead>
          <tbody>{table_rows(best_channels, ["brand", "acquisition_channel", "roi", "cost_per_conversion"])}</tbody>
        </table>
      </section>
      <section>
        <h2>Strongest Churn Drivers</h2>
        {"".join(f'<div class="driver"><code>{html.escape(row.feature)}</code><strong>{row.coefficient:.2f}</strong></div>' for row in drivers.itertuples())}
      </section>
    </div>
    <section>
      <h2>Highest Risk Customers</h2>
      <table>
        <thead><tr><th>Customer</th><th>Brand</th><th>Region</th><th>Plan</th><th>Revenue</th><th>Risk</th><th>Segment</th></tr></thead>
        <tbody>{table_rows(risk_view, ["customer_id", "brand", "region", "plan", "monthly_revenue", "churn_risk_score", "risk_segment"])}</tbody>
      </table>
    </section>
    <section>
      <h2>Revenue Forecast Preview</h2>
      <table>
        <thead><tr><th>Month</th><th>Brand</th><th>Forecast</th><th>Lower</th><th>Upper</th></tr></thead>
        <tbody>{table_rows(forecast_view, ["month", "brand", "forecast_revenue", "lower_bound", "upper_bound"])}</tbody>
      </table>
    </section>
  </main>
  <footer>Generated by a reproducible Python analytics pipeline with ETL validation checks and a from-scratch logistic regression model.</footer>
</body>
</html>"""

    (REPORTS_DIR / "dashboard.html").write_text(html_doc, encoding="utf-8")
    print("Dashboard written to reports/dashboard.html.")


if __name__ == "__main__":
    main()

