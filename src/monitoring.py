from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def build_monitoring_outputs(
    customers: pd.DataFrame,
    monthly: pd.DataFrame,
    campaigns: pd.DataFrame,
    payment_events: pd.DataFrame,
    fulfillment_events: pd.DataFrame,
    sku_inventory: pd.DataFrame,
    reports_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    metric_changes = build_metric_changes(monthly)
    alerts = pd.concat(
        [
            revenue_alerts(metric_changes),
            churn_alerts(metric_changes),
            campaign_alerts(campaigns),
            payment_alerts(customers, payment_events),
            fulfillment_alerts(fulfillment_events),
            inventory_alerts(sku_inventory),
        ],
        ignore_index=True,
    )
    if alerts.empty:
        alerts = empty_alerts()
        scorecard = build_data_quality_scorecard(
            customers,
            monthly,
            campaigns,
            payment_events,
            fulfillment_events,
            sku_inventory,
        )
        summary = {
            "open_alerts": 0,
            "critical_alerts": 0,
            "warning_alerts": 0,
            "top_alert": {},
            "healthy_checks": int((scorecard["status"] == "Healthy").sum()),
            "checks_run": int(len(scorecard)),
        }
        (reports_dir / "monitoring_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return alerts, metric_changes, scorecard, summary

    alerts = alerts.sort_values(["severity_rank", "impact_value"], ascending=[True, False]).reset_index(drop=True)
    alerts.insert(0, "rank", alerts.index + 1)
    alerts = alerts.drop(columns="severity_rank")

    scorecard = build_data_quality_scorecard(
        customers,
        monthly,
        campaigns,
        payment_events,
        fulfillment_events,
        sku_inventory,
    )
    summary = {
        "open_alerts": int(len(alerts)),
        "critical_alerts": int((alerts["severity"] == "Critical").sum()),
        "warning_alerts": int((alerts["severity"] == "Warning").sum()),
        "top_alert": alerts.iloc[0].to_dict() if not alerts.empty else {},
        "healthy_checks": int((scorecard["status"] == "Healthy").sum()),
        "checks_run": int(len(scorecard)),
    }
    (reports_dir / "monitoring_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return alerts, metric_changes, scorecard, summary


def build_metric_changes(monthly: pd.DataFrame) -> pd.DataFrame:
    frame = monthly.copy()
    frame["month"] = pd.to_datetime(frame["month"])
    latest_month = frame["month"].max()
    previous_window = latest_month - pd.DateOffset(months=3)
    latest = frame[frame["month"] == latest_month].copy()
    baseline = (
        frame[(frame["month"] < latest_month) & (frame["month"] >= previous_window)]
        .groupby("brand", as_index=False)
        .agg(
            baseline_active_customers=("active_customers", "mean"),
            baseline_revenue=("subscription_revenue", "mean"),
            baseline_churn_rate=("monthly_churn_rate", "mean"),
        )
    )
    changes = latest.merge(baseline, on="brand", how="left")
    changes["revenue_change_pct"] = pct_change(changes["subscription_revenue"], changes["baseline_revenue"])
    changes["active_customer_change_pct"] = pct_change(
        changes["active_customers"],
        changes["baseline_active_customers"],
    )
    changes["churn_rate_delta"] = changes["monthly_churn_rate"] - changes["baseline_churn_rate"]
    changes = changes.rename(
        columns={
            "month": "latest_month",
            "subscription_revenue": "current_revenue",
            "active_customers": "current_active_customers",
            "monthly_churn_rate": "current_churn_rate",
        }
    )
    changes["latest_month"] = changes["latest_month"].dt.date.astype(str)
    return changes[
        [
            "brand",
            "latest_month",
            "current_revenue",
            "baseline_revenue",
            "revenue_change_pct",
            "current_active_customers",
            "baseline_active_customers",
            "active_customer_change_pct",
            "current_churn_rate",
            "baseline_churn_rate",
            "churn_rate_delta",
        ]
    ].round(
        {
            "current_revenue": 2,
            "baseline_revenue": 2,
            "revenue_change_pct": 4,
            "baseline_active_customers": 1,
            "active_customer_change_pct": 4,
            "current_churn_rate": 4,
            "baseline_churn_rate": 4,
            "churn_rate_delta": 4,
        }
    )


def revenue_alerts(metric_changes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in metric_changes.itertuples(index=False):
        if row.revenue_change_pct <= -0.05:
            rows.append(
                alert_row(
                    severity="Critical" if row.revenue_change_pct <= -0.10 else "Warning",
                    owner="Revenue Ops",
                    alert_type="Revenue trend",
                    entity=row.brand,
                    metric="Subscription revenue",
                    current_value=row.current_revenue,
                    baseline_value=row.baseline_revenue,
                    change_pct=row.revenue_change_pct,
                    impact_value=max(0, row.baseline_revenue - row.current_revenue),
                    recommendation="Review acquisition mix, churn drivers, and stockout exposure for the brand.",
                )
            )
    return pd.DataFrame(rows)


def churn_alerts(metric_changes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in metric_changes.itertuples(index=False):
        if row.churn_rate_delta >= 0.015:
            rows.append(
                alert_row(
                    severity="Critical" if row.churn_rate_delta >= 0.03 else "Warning",
                    owner="Retention",
                    alert_type="Churn movement",
                    entity=row.brand,
                    metric="Monthly churn rate",
                    current_value=row.current_churn_rate,
                    baseline_value=row.baseline_churn_rate,
                    change_pct=row.churn_rate_delta,
                    impact_value=row.current_churn_rate * row.current_revenue,
                    recommendation="Inspect support, discount, and late-delivery segments before next renewal cycle.",
                )
            )
    return pd.DataFrame(rows)


def campaign_alerts(campaigns: pd.DataFrame) -> pd.DataFrame:
    frame = campaigns.copy()
    frame["roi"] = (frame["attributed_revenue"] - frame["spend"]) / frame["spend"]
    weak = frame[frame["roi"] < 0.75].copy()
    rows = []
    for row in weak.itertuples(index=False):
        rows.append(
            alert_row(
                severity="Critical" if row.roi < 0 else "Warning",
                owner="Marketing",
                alert_type="Campaign payback",
                entity=f"{row.brand} / {row.acquisition_channel}",
                metric="Campaign ROI",
                current_value=row.roi,
                baseline_value=1.0,
                change_pct=row.roi - 1.0,
                impact_value=row.spend * max(0, 0.75 - row.roi),
                recommendation="Cap spend until payback and retention quality recover.",
            )
        )
    return pd.DataFrame(rows)


def payment_alerts(customers: pd.DataFrame, payment_events: pd.DataFrame) -> pd.DataFrame:
    payments = payment_events.merge(customers[["customer_id", "brand"]], on="customer_id", how="left")
    payments["open_failed_amount"] = np.where(
        payments["payment_status"] == "failed",
        payments["invoice_amount"],
        0,
    )
    summary = (
        payments.groupby("brand", as_index=False)
        .agg(
            invoices=("invoice_id", "count"),
            open_failed=("payment_status", lambda values: int((values == "failed").sum())),
            open_amount=("open_failed_amount", "sum"),
        )
    )
    summary["open_failed_rate"] = summary["open_failed"] / summary["invoices"]
    rows = []
    for row in summary.itertuples(index=False):
        if row.open_failed_rate >= 0.025 or row.open_amount >= 1200:
            rows.append(
                alert_row(
                    severity="Critical" if row.open_failed_rate >= 0.04 else "Warning",
                    owner="Billing Ops",
                    alert_type="Failed payment build-up",
                    entity=row.brand,
                    metric="Open failed payment rate",
                    current_value=row.open_failed_rate,
                    baseline_value=0.025,
                    change_pct=row.open_failed_rate - 0.025,
                    impact_value=row.open_amount,
                    recommendation="Prioritize smart dunning and payment-link recovery for high-value invoices.",
                )
            )
    return pd.DataFrame(rows)


def fulfillment_alerts(fulfillment_events: pd.DataFrame) -> pd.DataFrame:
    summary = (
        fulfillment_events.groupby("brand", as_index=False)
        .agg(orders=("order_id", "count"), late_orders=("late_flag", "sum"))
    )
    summary["late_rate"] = summary["late_orders"] / summary["orders"]
    rows = []
    for row in summary.itertuples(index=False):
        if row.late_rate >= 0.28:
            rows.append(
                alert_row(
                    severity="Critical" if row.late_rate >= 0.36 else "Warning",
                    owner="Operations",
                    alert_type="Fulfillment SLA",
                    entity=row.brand,
                    metric="Late fulfillment rate",
                    current_value=row.late_rate,
                    baseline_value=0.18,
                    change_pct=row.late_rate - 0.18,
                    impact_value=row.late_orders,
                    recommendation="Escalate late-shipment rescue workflow for customers near renewal.",
                )
            )
    return pd.DataFrame(rows)


def inventory_alerts(sku_inventory: pd.DataFrame) -> pd.DataFrame:
    inventory = sku_inventory.copy()
    inventory["stockout_units"] = np.maximum(0, inventory["forecast_30d_units"] - inventory["on_hand_units"])
    inventory["stockout_risk"] = inventory["stockout_units"] / inventory["forecast_30d_units"].replace(0, np.nan)
    inventory["margin_at_risk"] = inventory["stockout_units"] * inventory["unit_price"] * inventory["gross_margin_rate"]
    risky = inventory[(inventory["stockout_risk"] >= 0.25) | (inventory["margin_at_risk"] >= 2500)].copy()
    rows = []
    for row in risky.itertuples(index=False):
        rows.append(
            alert_row(
                severity="Critical" if row.stockout_risk >= 0.50 else "Warning",
                owner="Inventory",
                alert_type="Stockout risk",
                entity=f"{row.brand} / {row.sku}",
                metric="SKU stockout risk",
                current_value=row.stockout_risk,
                baseline_value=0.25,
                change_pct=row.stockout_risk - 0.25,
                impact_value=row.margin_at_risk,
                recommendation="Advance purchase order or shift demand to substitute SKUs.",
            )
        )
    return pd.DataFrame(rows)


def build_data_quality_scorecard(
    customers: pd.DataFrame,
    monthly: pd.DataFrame,
    campaigns: pd.DataFrame,
    payment_events: pd.DataFrame,
    fulfillment_events: pd.DataFrame,
    sku_inventory: pd.DataFrame,
) -> pd.DataFrame:
    checks = [
        quality_row("Customer rows", len(customers), len(customers) >= 2500, "Data Engineering", "Expected at least 2,500 customer records."),
        quality_row("Customer duplicates", int(customers["customer_id"].duplicated().sum()), not customers["customer_id"].duplicated().any(), "Data Engineering", "Customer IDs must remain unique."),
        quality_row("Customer missing values", int(customers.isna().sum().sum()), customers.isna().sum().sum() == 0, "Data Engineering", "No null values expected in modeled customer fields."),
        quality_row("Monthly revenue coverage", monthly["month"].nunique(), monthly["month"].nunique() >= 12, "Analytics", "At least 12 months are needed for trend monitoring."),
        quality_row("Campaign ROI inputs", len(campaigns), {"spend", "attributed_revenue", "conversions"}.issubset(campaigns.columns), "Marketing Ops", "Campaign spend, conversions, and revenue are required."),
        quality_row("Payment events coverage", len(payment_events), len(payment_events) == len(customers), "Billing Ops", "Each customer should have one current invoice event."),
        quality_row("Fulfillment sample coverage", len(fulfillment_events), len(fulfillment_events) >= 1500, "Operations", "Recent fulfillment sample should cover at least 1,500 orders."),
        quality_row("Inventory SKU coverage", len(sku_inventory), len(sku_inventory) >= 12, "Inventory", "Each subscription SKU should have inventory coverage."),
    ]
    return pd.DataFrame(checks)


def alert_row(
    severity: str,
    owner: str,
    alert_type: str,
    entity: str,
    metric: str,
    current_value: float,
    baseline_value: float,
    change_pct: float,
    impact_value: float,
    recommendation: str,
) -> dict[str, object]:
    return {
        "severity": severity,
        "severity_rank": {"Critical": 0, "Warning": 1, "Watch": 2}.get(severity, 3),
        "owner": owner,
        "alert_type": alert_type,
        "entity": entity,
        "metric": metric,
        "current_value": round(float(current_value), 4),
        "baseline_value": round(float(baseline_value), 4),
        "change_pct": round(float(change_pct), 4),
        "impact_value": round(float(impact_value), 2),
        "recommendation": recommendation,
    }


def quality_row(check: str, value: float, passed: bool, owner: str, expectation: str) -> dict[str, object]:
    return {
        "check": check,
        "value": value,
        "status": "Healthy" if passed else "Needs review",
        "owner": owner,
        "expectation": expectation,
    }


def pct_change(current: pd.Series, baseline: pd.Series) -> pd.Series:
    return (current - baseline) / baseline.replace(0, np.nan)


def empty_alerts() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "rank",
            "severity",
            "owner",
            "alert_type",
            "entity",
            "metric",
            "current_value",
            "baseline_value",
            "change_pct",
            "impact_value",
            "recommendation",
        ]
    )
