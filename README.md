# Subscription Science Lab

A portfolio-ready data science project for subscription revenue recovery and e-commerce operations.

This project mirrors the kind of work described in my CV: subscription reporting, ETL validation, campaign performance analysis, churn-risk modeling, revenue forecasting, and operational revenue recovery for multi-brand e-commerce operations.

## Live Dashboard

View the dashboard here: [Subscription Science Lab Dashboard](https://avi09cr7.github.io/subscription-science-lab/reports/dashboard.html)

## Project Story

An e-commerce team manages subscription programs across brands, regions, plans, acquisition channels, payments, fulfillment, support, and inventory. The business wants to know:

- Where are we leaking subscription revenue?
- Which customers, SKUs, campaigns, and payment failures should the team fix first?
- Which owner should act today, this week, or next budget cycle?
- Which data quality checks should run before the analytics layer is trusted?

The repo builds a reproducible synthetic dataset, validates it like an ETL handoff, trains a dependency-light churn model, detects revenue leakage, and generates a decision-ready control tower dashboard. The data is generated locally by `src/generate_data.py`; it is not scraped from real brands and does not contain private customer data.

## Why This Fits My Data Scientist Transition

- **Data science:** churn-risk model, feature coefficients, train/test evaluation, ROC AUC.
- **Analytics:** customer KPIs, channel ROI, subscription revenue trends.
- **ETL and QA:** schema checks, missing-value checks, duplicate checks, business-rule validation.
- **Business communication:** final dashboard translates model output into actions.
- **Revenue operations:** failed payment recovery, fulfillment-driven churn, discount leakage, SKU stockout exposure, and owner-based action queues.
- **Experimentation:** recovery playbooks include hypotheses, treatment/control sizing, primary metrics, and scale decisions.
- **Segmentation:** brand-channel-plan opportunity ranking for focused recovery planning.
- **Monitoring:** weekly alerting and data-quality scorecards to catch operational drift.
- **Scenario planning:** capacity-constrained recovery plans for lean, balanced, and full execution weeks.
- **E-commerce domain:** brands, SKUs, recurring plans, campaign channels, support issues, discounts, and retention.

## Repo Structure

```text
subscription-science-lab/
  src/
    generate_data.py       # Creates reproducible synthetic subscription and campaign data
    model.py               # Logistic regression from scratch with model metrics
    playbooks.py           # Converts recovery actions into ROI-ranked playbooks and experiments
    scenarios.py           # Builds capacity-constrained recovery plans and owner workload scenarios
    segments.py            # Ranks brand-channel-plan pockets by recoverable value and issue mix
    monitoring.py          # Builds KPI movement, alert, and data-quality monitoring outputs
    pipeline.py            # ETL validation, feature engineering, forecasting, report outputs
    build_dashboard.py     # Builds the final HTML dashboard
  data/
    raw/                   # Generated source-like CSVs
    processed/             # Cleaned model-ready outputs
  reports/                 # Metrics, summaries, forecasts, and dashboard
```

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/generate_data.py
python src/pipeline.py
python src/build_dashboard.py
```

Open `reports/dashboard.html` in a browser, or use the GitHub Pages link above after Pages is enabled for the repository.

## Control Tower Features

- Monday Morning Ops Brief summarizing total revenue at risk and the highest-impact recovery actions.
- Revenue leakage stack across campaign quality, fulfillment, stockouts, support, discounts, and failed payments.
- Deduplicated recovery action queue filtered by owner and urgency.
- Recovery playbook ROI planner with expected save value, cost, net impact, and scale/test decisions.
- Experiment backlog with treatment/control sizing, primary metrics, and decision rules.
- Capacity Scenario Planner for lean, balanced, and full recovery weeks by team capacity.
- Segment Opportunity Map ranking brand, acquisition channel, and plan combinations by recoverable value.
- Monitoring & Alert Console for KPI changes, campaign payback gaps, SLA risk, stockouts, and data-quality checks.
- Failed payment recovery breakdown by decline reason.
- SKU stockout exposure report ranked by margin at risk.

## Current Results

After running the pipeline, the project writes:

- `reports/model_metrics.json`
- `reports/customer_risk_scores.csv`
- `reports/brand_summary.csv`
- `reports/channel_summary.csv`
- `reports/revenue_forecast.csv`
- `reports/revenue_leakage_report.csv`
- `reports/action_queue.csv`
- `reports/payment_recovery_summary.csv`
- `reports/sku_risk_report.csv`
- `reports/recovery_playbook_roi.csv`
- `reports/experiment_backlog.csv`
- `reports/owner_workload.csv`
- `reports/scenario_plan.csv`
- `reports/scenario_workload.csv`
- `reports/scenario_action_plan.csv`
- `reports/scenario_summary.json`
- `reports/segment_opportunity_report.csv`
- `reports/segment_issue_matrix.csv`
- `reports/monitoring_alerts.csv`
- `reports/weekly_metric_changes.csv`
- `reports/data_quality_scorecard.csv`
- `reports/monitoring_summary.json`
- `reports/weekly_action_brief.json`
- `reports/dashboard.html`

## Data Source

All input CSVs in `data/raw/` are generated by `src/generate_data.py` with a fixed random seed. The synthetic records mimic realistic subscription analytics fields: brand, region, acquisition channel, plan type, tenure, monthly revenue, discount rate, support tickets, shipping issues, engagement, churn status, payment events, fulfillment events, and SKU inventory.

## Portfolio Talking Points

- Designed a full analytics workflow from raw data generation to validated reporting.
- Implemented churn prediction without relying on a black-box ML framework.
- Added ETL-style quality gates to prevent reporting on broken data.
- Connected model outputs to revenue recovery, owner assignment, capacity planning, segment prioritization, monitoring, inventory planning, budget optimization, experiment design, and subscription growth decisions.
