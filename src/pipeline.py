from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from leakage import build_leakage_outputs
from model import classification_metrics, predict_proba, train_logistic_regression
from monitoring import build_monitoring_outputs
from playbooks import build_playbook_outputs
from scenarios import build_scenario_outputs
from segments import build_segment_outputs


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"


CUSTOMER_COLUMNS = {
    "customer_id",
    "brand",
    "region",
    "acquisition_channel",
    "plan",
    "tenure_months",
    "active_subscriptions",
    "monthly_revenue",
    "discount_rate",
    "support_tickets_90d",
    "late_shipments_90d",
    "email_engagement",
    "avg_days_between_orders",
    "churned",
}


def validate_customers(customers: pd.DataFrame) -> list[str]:
    checks = []
    missing_columns = CUSTOMER_COLUMNS - set(customers.columns)
    if missing_columns:
        raise ValueError(f"Missing expected columns: {sorted(missing_columns)}")
    if customers[sorted(CUSTOMER_COLUMNS)].isna().sum().sum() != 0:
        raise ValueError("Customer dataset contains missing values.")
    if customers["customer_id"].duplicated().any():
        raise ValueError("Customer IDs must be unique.")
    if (customers["monthly_revenue"] <= 0).any():
        raise ValueError("Monthly revenue must be positive.")
    if not customers["discount_rate"].between(0, 1).all():
        raise ValueError("Discount rate must be between 0 and 1.")
    if not set(customers["churned"].unique()).issubset({0, 1}):
        raise ValueError("Churn label must be binary.")
    checks.extend(
        [
            "schema_check_passed",
            "missing_value_check_passed",
            "unique_customer_check_passed",
            "business_rule_check_passed",
        ]
    )
    return checks


def train_churn_model(customers: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float], pd.DataFrame]:
    feature_frame = pd.get_dummies(
        customers[
            [
                "brand",
                "region",
                "acquisition_channel",
                "plan",
                "tenure_months",
                "active_subscriptions",
                "monthly_revenue",
                "discount_rate",
                "support_tickets_90d",
                "late_shipments_90d",
                "email_engagement",
                "avg_days_between_orders",
            ]
        ],
        drop_first=True,
    )
    labels = customers["churned"].to_numpy()
    rng = np.random.default_rng(42)
    indices = rng.permutation(len(customers))
    split = int(len(customers) * 0.78)
    train_idx, test_idx = indices[:split], indices[split:]

    model = train_logistic_regression(
        feature_frame.iloc[train_idx].to_numpy(dtype=float),
        labels[train_idx],
        list(feature_frame.columns),
    )
    test_probabilities = predict_proba(model, feature_frame.iloc[test_idx].to_numpy(dtype=float))
    metrics = classification_metrics(labels[test_idx], test_probabilities)

    all_probabilities = predict_proba(model, feature_frame.to_numpy(dtype=float))
    scored = customers.copy()
    scored["churn_risk_score"] = np.round(all_probabilities, 4)
    scored["risk_segment"] = pd.cut(
        scored["churn_risk_score"],
        bins=[0, 0.25, 0.45, 0.65, 1.0],
        labels=["low", "watch", "high", "critical"],
        include_lowest=True,
    )

    coefficients = (
        pd.DataFrame({"feature": model.feature_names, "coefficient": model.weights})
        .assign(abs_coefficient=lambda frame: frame["coefficient"].abs())
        .sort_values("abs_coefficient", ascending=False)
        .drop(columns="abs_coefficient")
    )
    return scored, metrics, coefficients


def build_summaries(customers: pd.DataFrame, campaigns: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    brand_summary = (
        customers.groupby("brand")
        .agg(
            customers=("customer_id", "count"),
            monthly_revenue=("monthly_revenue", "sum"),
            churn_rate=("churned", "mean"),
            avg_risk_score=("churn_risk_score", "mean"),
            support_tickets_90d=("support_tickets_90d", "sum"),
        )
        .reset_index()
        .sort_values("avg_risk_score", ascending=False)
    )
    brand_summary["monthly_revenue"] = brand_summary["monthly_revenue"].round(2)
    brand_summary["churn_rate"] = brand_summary["churn_rate"].round(4)
    brand_summary["avg_risk_score"] = brand_summary["avg_risk_score"].round(4)

    channel_summary = campaigns.copy()
    channel_summary["roi"] = (channel_summary["attributed_revenue"] - channel_summary["spend"]) / channel_summary["spend"]
    channel_summary["cost_per_conversion"] = channel_summary["spend"] / channel_summary["conversions"].replace(0, np.nan)
    channel_summary = channel_summary.round({"roi": 3, "cost_per_conversion": 2})
    return brand_summary, channel_summary


def forecast_revenue(monthly: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    monthly = monthly.copy()
    monthly["month"] = pd.to_datetime(monthly["month"])
    forecast_rows = []
    for brand, group in monthly.sort_values("month").groupby("brand"):
        values = group["subscription_revenue"].to_numpy()
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        residual_scale = np.std(values - (slope * x + intercept))
        for step in range(1, periods + 1):
            month = group["month"].max() + pd.DateOffset(months=step)
            point = slope * (len(values) + step - 1) + intercept
            forecast_rows.append(
                {
                    "month": month.date().isoformat(),
                    "brand": brand,
                    "forecast_revenue": round(float(point), 2),
                    "lower_bound": round(float(point - 1.15 * residual_scale), 2),
                    "upper_bound": round(float(point + 1.15 * residual_scale), 2),
                }
            )
    return pd.DataFrame(forecast_rows)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(RAW_DIR / "customers.csv")
    monthly = pd.read_csv(RAW_DIR / "monthly_revenue.csv")
    campaigns = pd.read_csv(RAW_DIR / "campaigns.csv")
    payment_events = pd.read_csv(RAW_DIR / "payment_events.csv")
    fulfillment_events = pd.read_csv(RAW_DIR / "fulfillment_events.csv")
    sku_inventory = pd.read_csv(RAW_DIR / "sku_inventory.csv")

    validation_checks = validate_customers(customers)
    scored_customers, metrics, coefficients = train_churn_model(customers)
    brand_summary, channel_summary = build_summaries(scored_customers, campaigns)
    revenue_forecast = forecast_revenue(monthly)
    leakage_report, action_queue, action_brief = build_leakage_outputs(
        scored_customers,
        campaigns,
        payment_events,
        fulfillment_events,
        sku_inventory,
        REPORTS_DIR,
    )
    playbook_roi, experiment_backlog, owner_workload = build_playbook_outputs(action_queue)
    segment_opportunities, segment_issue_matrix = build_segment_outputs(scored_customers, action_queue)
    monitoring_alerts, metric_changes, data_quality_scorecard, monitoring_summary = build_monitoring_outputs(
        scored_customers,
        monthly,
        campaigns,
        payment_events,
        fulfillment_events,
        sku_inventory,
        REPORTS_DIR,
    )
    scenario_plan, scenario_workload, scenario_actions, scenario_summary = build_scenario_outputs(
        action_queue,
        REPORTS_DIR,
    )

    scored_customers.to_csv(PROCESSED_DIR / "customers_scored.csv", index=False)
    scored_customers.sort_values("churn_risk_score", ascending=False).head(100).to_csv(
        REPORTS_DIR / "customer_risk_scores.csv", index=False
    )
    brand_summary.to_csv(REPORTS_DIR / "brand_summary.csv", index=False)
    channel_summary.to_csv(REPORTS_DIR / "channel_summary.csv", index=False)
    revenue_forecast.to_csv(REPORTS_DIR / "revenue_forecast.csv", index=False)
    coefficients.head(12).to_csv(REPORTS_DIR / "top_model_drivers.csv", index=False)
    playbook_roi.to_csv(REPORTS_DIR / "recovery_playbook_roi.csv", index=False)
    experiment_backlog.to_csv(REPORTS_DIR / "experiment_backlog.csv", index=False)
    owner_workload.to_csv(REPORTS_DIR / "owner_workload.csv", index=False)
    segment_opportunities.to_csv(REPORTS_DIR / "segment_opportunity_report.csv", index=False)
    segment_issue_matrix.to_csv(REPORTS_DIR / "segment_issue_matrix.csv", index=False)
    monitoring_alerts.to_csv(REPORTS_DIR / "monitoring_alerts.csv", index=False)
    metric_changes.to_csv(REPORTS_DIR / "weekly_metric_changes.csv", index=False)
    data_quality_scorecard.to_csv(REPORTS_DIR / "data_quality_scorecard.csv", index=False)
    scenario_plan.to_csv(REPORTS_DIR / "scenario_plan.csv", index=False)
    scenario_workload.to_csv(REPORTS_DIR / "scenario_workload.csv", index=False)
    scenario_actions.to_csv(REPORTS_DIR / "scenario_action_plan.csv", index=False)

    metrics_payload = {
        "validation_checks": validation_checks,
        "model_metrics": metrics,
        "rows_processed": int(len(customers)),
        "overall_churn_rate": round(float(customers["churned"].mean()), 4),
        "total_monthly_revenue": round(float(customers["monthly_revenue"].sum()), 2),
        "total_revenue_at_risk": action_brief["total_revenue_at_risk"],
        "action_queue_items": int(len(action_queue)),
        "leakage_categories": int(len(leakage_report)),
        "playbook_net_impact": round(float(playbook_roi["net_impact"].sum()), 2),
        "playbooks_recommended": int(len(playbook_roi)),
        "experiments_ready": int(len(experiment_backlog)),
        "priority_segments": int(len(segment_opportunities)),
        "top_segment_expected_value": (
            0
            if segment_opportunities.empty
            else round(float(segment_opportunities["expected_value"].max()), 2)
        ),
        "open_monitoring_alerts": monitoring_summary["open_alerts"],
        "critical_monitoring_alerts": monitoring_summary["critical_alerts"],
        "scenario_max_net_impact": scenario_summary["max_net_impact"],
        "scenario_max_actions": scenario_summary["max_actions"],
    }
    (REPORTS_DIR / "model_metrics.json").write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    print("Pipeline complete. Reports written to reports/.")


if __name__ == "__main__":
    main()
