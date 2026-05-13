from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def build_leakage_outputs(
    customers: pd.DataFrame,
    campaigns: pd.DataFrame,
    payment_events: pd.DataFrame,
    fulfillment_events: pd.DataFrame,
    sku_inventory: pd.DataFrame,
    reports_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    customer_margins = sku_inventory.groupby("brand")["gross_margin_rate"].mean().rename("gross_margin_rate")
    enriched = customers.merge(customer_margins, on="brand", how="left")
    enriched["gross_margin_rate"] = enriched["gross_margin_rate"].fillna(0.48)
    enriched["six_month_margin_at_risk"] = (
        enriched["monthly_revenue"] * 6 * enriched["gross_margin_rate"] * enriched["churn_risk_score"]
    )

    payment_leak = payment_events.merge(
        enriched[["customer_id", "brand", "monthly_revenue", "churn_risk_score", "six_month_margin_at_risk"]],
        on="customer_id",
        how="left",
    )
    open_failed = payment_leak[payment_leak["payment_status"] == "failed"].copy()

    fulfillment_leak = fulfillment_events.merge(
        enriched[["customer_id", "brand", "monthly_revenue", "churn_risk_score", "six_month_margin_at_risk"]],
        on=["customer_id", "brand"],
        how="left",
    )
    late_orders = fulfillment_leak[fulfillment_leak["late_flag"] == 1].copy()

    discount_leak = enriched[(enriched["discount_rate"] >= 0.35) & (enriched["churn_risk_score"] >= 0.30)].copy()
    discount_leak["discount_margin_leak"] = (
        discount_leak["monthly_revenue"] * 3 * discount_leak["discount_rate"] * discount_leak["gross_margin_rate"]
    )

    channel_quality = (
        enriched.groupby(["brand", "acquisition_channel"])
        .agg(
            acquired_customers=("customer_id", "count"),
            avg_churn_risk=("churn_risk_score", "mean"),
            avg_monthly_revenue=("monthly_revenue", "mean"),
        )
        .reset_index()
    )
    campaign_quality = campaigns.merge(channel_quality, on=["brand", "acquisition_channel"], how="left")
    campaign_quality["roi"] = (
        (campaign_quality["attributed_revenue"] - campaign_quality["spend"]) / campaign_quality["spend"]
    )
    campaign_quality["payback_gap"] = np.maximum(0, 1 - campaign_quality["roi"])
    campaign_quality["quality_penalty"] = np.maximum(0, campaign_quality["avg_churn_risk"] - 0.22)
    campaign_quality["budget_at_risk"] = (
        campaign_quality["spend"] * campaign_quality["payback_gap"]
        + campaign_quality["spend"] * campaign_quality["quality_penalty"]
    )
    weak_campaigns = campaign_quality[campaign_quality["budget_at_risk"] > 0].copy()

    inventory = sku_inventory.copy()
    inventory["stockout_units"] = np.maximum(0, inventory["forecast_30d_units"] - inventory["on_hand_units"])
    inventory["stockout_risk"] = inventory["stockout_units"] / inventory["forecast_30d_units"].replace(0, np.nan)
    inventory["margin_at_risk"] = inventory["stockout_units"] * inventory["unit_price"] * inventory["gross_margin_rate"]
    inventory_risk = inventory[inventory["stockout_units"] > 0].copy()

    support_leak = enriched[(enriched["support_tickets_90d"] >= 3) & (enriched["churn_risk_score"] >= 0.35)].copy()

    leakage_rows = [
        {
            "leak_area": "Failed payment recovery",
            "problem": "Open failed subscription invoices are creating preventable involuntary churn risk.",
            "affected_count": int(len(open_failed)),
            "revenue_at_risk": round(float(open_failed["invoice_amount"].sum()), 2),
            "recommended_action": "Prioritize payment update links and retry timing for highest-value failed invoices.",
            "owner": "Billing Ops",
            "urgency": "Today",
        },
        {
            "leak_area": "Fulfillment-driven churn",
            "problem": "Late shipments are hitting customers who already have elevated churn probability.",
            "affected_count": int(len(late_orders)),
            "revenue_at_risk": round(float(late_orders["six_month_margin_at_risk"].sum()), 2),
            "recommended_action": "Escalate late orders for high-margin subscribers before renewal windows.",
            "owner": "Operations",
            "urgency": "This week",
        },
        {
            "leak_area": "Discount margin leakage",
            "problem": "High discounts are concentrated among customers with weak retention signals.",
            "affected_count": int(len(discount_leak)),
            "revenue_at_risk": round(float(discount_leak["discount_margin_leak"].sum()), 2),
            "recommended_action": "Replace blanket discounts with targeted win-back or plan-change offers.",
            "owner": "Growth",
            "urgency": "This week",
        },
        {
            "leak_area": "Campaign quality leakage",
            "problem": "Some acquisition channels are producing weak payback or high-risk subscribers.",
            "affected_count": int(len(weak_campaigns)),
            "revenue_at_risk": round(float(weak_campaigns["budget_at_risk"].sum()), 2),
            "recommended_action": "Pause or cap poor-payback channels and reallocate budget to higher-retention sources.",
            "owner": "Marketing",
            "urgency": "Next budget cycle",
        },
        {
            "leak_area": "SKU stockout exposure",
            "problem": "Forecasted demand exceeds available units for subscription SKUs.",
            "affected_count": int(len(inventory_risk)),
            "revenue_at_risk": round(float(inventory_risk["margin_at_risk"].sum()), 2),
            "recommended_action": "Advance purchase orders for high-margin SKUs with supplier lead-time risk.",
            "owner": "Inventory",
            "urgency": "This week",
        },
        {
            "leak_area": "Support escalation risk",
            "problem": "Subscribers with repeated support issues have high predicted cancellation risk.",
            "affected_count": int(len(support_leak)),
            "revenue_at_risk": round(float(support_leak["six_month_margin_at_risk"].sum()), 2),
            "recommended_action": "Create a callback queue for high-value subscribers with repeated tickets.",
            "owner": "Customer Success",
            "urgency": "Today",
        },
    ]
    leakage_report = (
        pd.DataFrame(leakage_rows)
        .sort_values(["revenue_at_risk", "affected_count"], ascending=False)
        .reset_index(drop=True)
    )
    leakage_report.insert(0, "rank", leakage_report.index + 1)

    action_queue = build_action_queue(open_failed, late_orders, discount_leak, support_leak)
    inventory.sort_values("margin_at_risk", ascending=False).to_csv(reports_dir / "sku_risk_report.csv", index=False)
    payment_recovery_summary(open_failed, payment_events).to_csv(
        reports_dir / "payment_recovery_summary.csv", index=False
    )

    brief = {
        "total_revenue_at_risk": round(float(leakage_report["revenue_at_risk"].sum()), 2),
        "top_leak_area": str(leakage_report.iloc[0]["leak_area"]),
        "top_recommended_action": str(leakage_report.iloc[0]["recommended_action"]),
        "today_actions": int((leakage_report["urgency"] == "Today").sum()),
        "leakage_items": leakage_report.head(3).to_dict(orient="records"),
    }
    (reports_dir / "weekly_action_brief.json").write_text(json.dumps(brief, indent=2), encoding="utf-8")

    leakage_report.to_csv(reports_dir / "revenue_leakage_report.csv", index=False)
    action_queue.to_csv(reports_dir / "action_queue.csv", index=False)
    return leakage_report, action_queue, brief


def build_action_queue(
    open_failed: pd.DataFrame,
    late_orders: pd.DataFrame,
    discount_leak: pd.DataFrame,
    support_leak: pd.DataFrame,
) -> pd.DataFrame:
    actions = []
    for row in open_failed.itertuples():
        actions.append(
            {
                "customer_id": row.customer_id,
                "brand": row.brand,
                "issue_type": "failed_payment",
                "expected_value": round(float(row.invoice_amount), 2),
                "recommended_action": f"Send payment update link; decline reason: {row.decline_reason}.",
                "reason": f"{row.retry_count} retries / {row.days_past_due} days past due",
            }
        )
    for row in late_orders.itertuples():
        actions.append(
            {
                "customer_id": row.customer_id,
                "brand": row.brand,
                "issue_type": "late_fulfillment",
                "expected_value": round(float(row.six_month_margin_at_risk), 2),
                "recommended_action": "Prioritize shipment follow-up before next renewal.",
                "reason": f"Delivered in {row.actual_days} days vs {row.promised_days} promised",
            }
        )
    for row in discount_leak.itertuples():
        actions.append(
            {
                "customer_id": row.customer_id,
                "brand": row.brand,
                "issue_type": "discount_margin_leak",
                "expected_value": round(float(row.discount_margin_leak), 2),
                "recommended_action": "Move from blanket discount to targeted retention offer.",
                "reason": f"{row.discount_rate:.0%} discount with {row.churn_risk_score:.0%} churn risk",
            }
        )
    for row in support_leak.itertuples():
        actions.append(
            {
                "customer_id": row.customer_id,
                "brand": row.brand,
                "issue_type": "support_escalation",
                "expected_value": round(float(row.six_month_margin_at_risk), 2),
                "recommended_action": "Add to customer-success callback queue.",
                "reason": f"{row.support_tickets_90d} support tickets in 90 days",
            }
        )
    if not actions:
        return pd.DataFrame(
            columns=["customer_id", "brand", "issue_type", "expected_value", "recommended_action", "reason"]
        )
    action_frame = pd.DataFrame(actions).sort_values("expected_value", ascending=False)
    primary_actions = action_frame.drop_duplicates("customer_id").set_index("customer_id")
    rolled_up = (
        action_frame.groupby(["customer_id", "brand"], as_index=False)
        .agg(
            issue_type=("issue_type", lambda values: " + ".join(dict.fromkeys(values))),
            expected_value=("expected_value", "sum"),
            reason=("reason", lambda values: " | ".join(list(dict.fromkeys(values))[:2])),
        )
        .sort_values("expected_value", ascending=False)
    )
    rolled_up["expected_value"] = rolled_up["expected_value"].round(2)
    rolled_up["recommended_action"] = rolled_up["customer_id"].map(primary_actions["recommended_action"])
    return rolled_up[
        ["customer_id", "brand", "issue_type", "expected_value", "recommended_action", "reason"]
    ].head(75)


def payment_recovery_summary(open_failed: pd.DataFrame, payment_events: pd.DataFrame) -> pd.DataFrame:
    total_failed = payment_events[payment_events["payment_status"].isin(["failed", "recovered"])].copy()
    if total_failed.empty:
        return pd.DataFrame(columns=["decline_reason", "failed_invoices", "open_failed", "open_amount"])
    return (
        total_failed.groupby("decline_reason")
        .agg(failed_invoices=("invoice_id", "count"), total_failed_amount=("invoice_amount", "sum"))
        .join(
            open_failed.groupby("decline_reason").agg(
                open_failed=("invoice_id", "count"),
                open_amount=("invoice_amount", "sum"),
            ),
            how="left",
        )
        .fillna({"open_failed": 0, "open_amount": 0})
        .reset_index()
        .round({"total_failed_amount": 2, "open_amount": 2})
        .sort_values("open_amount", ascending=False)
    )
