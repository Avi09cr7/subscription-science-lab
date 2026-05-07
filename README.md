# Subscription Science Lab

A small, portfolio-ready data science project for e-commerce subscription analytics.

This project mirrors the kind of work described in my CV: subscription reporting, ETL validation, campaign performance analysis, churn-risk modeling, and revenue forecasting for multi-brand e-commerce operations.

## Project Story

An e-commerce team manages subscription programs across brands, regions, plans, and acquisition channels. The business wants to know:

- Which customers are most likely to churn?
- Which brands and channels carry the highest retention risk?
- What revenue should the team expect over the next six months?
- Which data quality checks should run before the analytics layer is trusted?

The repo builds a reproducible synthetic dataset, validates it like an ETL handoff, trains a dependency-light churn model, and generates a decision-ready HTML dashboard.

## Why This Fits My Data Scientist Transition

- **Data science:** churn-risk model, feature coefficients, train/test evaluation, ROC AUC.
- **Analytics:** customer KPIs, channel ROI, subscription revenue trends.
- **ETL and QA:** schema checks, missing-value checks, duplicate checks, business-rule validation.
- **Business communication:** final dashboard translates model output into actions.
- **E-commerce domain:** brands, SKUs, recurring plans, campaign channels, support issues, discounts, and retention.

## Repo Structure

```text
subscription-science-lab/
  src/
    generate_data.py       # Creates reproducible synthetic subscription and campaign data
    model.py               # Logistic regression from scratch with model metrics
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

Open `reports/dashboard.html` in a browser.

## Current Results

After running the pipeline, the project writes:

- `reports/model_metrics.json`
- `reports/customer_risk_scores.csv`
- `reports/brand_summary.csv`
- `reports/channel_summary.csv`
- `reports/revenue_forecast.csv`
- `reports/dashboard.html`

## Portfolio Talking Points

- Designed a full analytics workflow from raw data generation to validated reporting.
- Implemented churn prediction without relying on a black-box ML framework.
- Added ETL-style quality gates to prevent reporting on broken data.
- Connected model outputs to retention, budget optimization, and subscription growth decisions.

