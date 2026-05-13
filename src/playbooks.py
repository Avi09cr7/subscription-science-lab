from __future__ import annotations

import math

import numpy as np
import pandas as pd


PLAYBOOKS = {
    "failed_payment": {
        "playbook": "Smart dunning and payment-link recovery",
        "owner": "Billing Ops",
        "cost_per_action": 1.25,
        "expected_save_rate": 0.42,
        "speed_to_value": "0-7 days",
        "primary_metric": "Recovered invoice rate",
        "hypothesis": "A timed retry and payment-link sequence will recover more failed invoices before involuntary churn.",
        "decision_rule": "Scale if recovery rate improves by 8 percentage points without refund complaints increasing.",
    },
    "late_fulfillment": {
        "playbook": "Late-shipment rescue workflow",
        "owner": "Operations",
        "cost_per_action": 9.00,
        "expected_save_rate": 0.24,
        "speed_to_value": "7-21 days",
        "primary_metric": "Next renewal retained",
        "hypothesis": "Proactive shipment follow-up and make-good credits will protect renewals after late delivery.",
        "decision_rule": "Scale if next-renewal retention improves by 5 percentage points at positive margin.",
    },
    "discount_margin_leak": {
        "playbook": "Offer ladder instead of blanket discounts",
        "owner": "Growth",
        "cost_per_action": 3.50,
        "expected_save_rate": 0.16,
        "speed_to_value": "14-30 days",
        "primary_metric": "Gross margin retained",
        "hypothesis": "Replacing blanket discounts with tiered offers will retain customers while reducing margin leakage.",
        "decision_rule": "Scale if retained gross margin improves by 4 percentage points with stable churn.",
    },
    "support_escalation": {
        "playbook": "Priority callback for high-value subscribers",
        "owner": "Customer Success",
        "cost_per_action": 14.00,
        "expected_save_rate": 0.20,
        "speed_to_value": "7-14 days",
        "primary_metric": "Escalation retention rate",
        "hypothesis": "Human callbacks for repeated support issues will reduce avoidable cancellations.",
        "decision_rule": "Scale if escalation retention improves by 6 percentage points and callbacks stay within SLA.",
    },
}


def build_playbook_outputs(action_queue: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if action_queue.empty:
        return empty_playbooks(), empty_experiments(), empty_owner_workload()

    exploded = explode_issues(action_queue)
    grouped = (
        exploded.groupby("issue_type", as_index=False)
        .agg(
            eligible_customers=("customer_id", "nunique"),
            gross_value=("allocated_value", "sum"),
            avg_customer_value=("allocated_value", "mean"),
            brands=("brand", lambda values: ", ".join(sorted(set(values)))),
        )
        .sort_values("gross_value", ascending=False)
    )

    rows = []
    for row in grouped.itertuples(index=False):
        config = PLAYBOOKS.get(row.issue_type)
        if not config:
            continue
        total_cost = row.eligible_customers * config["cost_per_action"]
        expected_saved_value = row.gross_value * config["expected_save_rate"]
        net_impact = expected_saved_value - total_cost
        roi = expected_saved_value / total_cost if total_cost else np.nan
        rows.append(
            {
                "issue_type": row.issue_type,
                "playbook": config["playbook"],
                "owner": config["owner"],
                "eligible_customers": int(row.eligible_customers),
                "gross_value": round(float(row.gross_value), 2),
                "avg_customer_value": round(float(row.avg_customer_value), 2),
                "cost_per_action": round(float(config["cost_per_action"]), 2),
                "total_cost": round(float(total_cost), 2),
                "expected_save_rate": round(float(config["expected_save_rate"]), 4),
                "expected_saved_value": round(float(expected_saved_value), 2),
                "net_impact": round(float(net_impact), 2),
                "roi": round(float(roi), 2) if not math.isnan(roi) else np.nan,
                "speed_to_value": config["speed_to_value"],
                "primary_metric": config["primary_metric"],
                "brands": row.brands,
                "decision": decision_label(net_impact, roi),
            }
        )

    playbooks = pd.DataFrame(rows).sort_values(["net_impact", "roi"], ascending=False).reset_index(drop=True)
    playbooks.insert(0, "rank", playbooks.index + 1)
    experiments = build_experiment_backlog(playbooks)
    owner_workload = build_owner_workload(playbooks)
    return playbooks, experiments, owner_workload


def explode_issues(action_queue: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in action_queue.itertuples(index=False):
        issues = str(row.issue_type).split(" + ")
        allocated_value = float(row.expected_value) / len(issues)
        for issue in issues:
            rows.append(
                {
                    "customer_id": row.customer_id,
                    "brand": row.brand,
                    "issue_type": issue,
                    "allocated_value": allocated_value,
                }
            )
    return pd.DataFrame(rows)


def decision_label(net_impact: float, roi: float) -> str:
    if net_impact >= 1000 and roi >= 3:
        return "Scale this week"
    if net_impact > 0 and roi >= 1.5:
        return "Run controlled test"
    if net_impact > 0:
        return "Monitor economics"
    return "Do not scale yet"


def build_experiment_backlog(playbooks: pd.DataFrame) -> pd.DataFrame:
    if playbooks.empty:
        return empty_experiments()

    rows = []
    for row in playbooks.itertuples(index=False):
        config = PLAYBOOKS[row.issue_type]
        control_count = max(5, int(round(row.eligible_customers * 0.25)))
        treatment_count = max(5, row.eligible_customers - control_count)
        rows.append(
            {
                "experiment_id": f"EXP-{int(row.rank):03d}",
                "playbook": row.playbook,
                "owner": row.owner,
                "hypothesis": config["hypothesis"],
                "treatment_count": int(treatment_count),
                "control_count": int(control_count),
                "primary_metric": row.primary_metric,
                "minimum_detectable_lift": round(max(0.03, row.expected_save_rate * 0.35), 4),
                "duration_days": duration_days(row.speed_to_value),
                "decision_rule": config["decision_rule"],
            }
        )
    return pd.DataFrame(rows)


def build_owner_workload(playbooks: pd.DataFrame) -> pd.DataFrame:
    if playbooks.empty:
        return empty_owner_workload()

    best = playbooks.sort_values("net_impact", ascending=False).drop_duplicates("owner").set_index("owner")
    workload = (
        playbooks.groupby("owner", as_index=False)
        .agg(
            playbooks=("playbook", "count"),
            eligible_customers=("eligible_customers", "sum"),
            gross_value=("gross_value", "sum"),
            total_cost=("total_cost", "sum"),
            expected_net_impact=("net_impact", "sum"),
        )
        .sort_values("expected_net_impact", ascending=False)
    )
    workload["best_next_playbook"] = workload["owner"].map(best["playbook"])
    return workload.round({"gross_value": 2, "total_cost": 2, "expected_net_impact": 2})


def duration_days(speed_to_value: str) -> int:
    if speed_to_value == "0-7 days":
        return 14
    if speed_to_value == "7-14 days":
        return 21
    if speed_to_value == "7-21 days":
        return 28
    return 35


def empty_playbooks() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "rank",
            "issue_type",
            "playbook",
            "owner",
            "eligible_customers",
            "gross_value",
            "avg_customer_value",
            "cost_per_action",
            "total_cost",
            "expected_save_rate",
            "expected_saved_value",
            "net_impact",
            "roi",
            "speed_to_value",
            "primary_metric",
            "brands",
            "decision",
        ]
    )


def empty_experiments() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "experiment_id",
            "playbook",
            "owner",
            "hypothesis",
            "treatment_count",
            "control_count",
            "primary_metric",
            "minimum_detectable_lift",
            "duration_days",
            "decision_rule",
        ]
    )


def empty_owner_workload() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "owner",
            "playbooks",
            "eligible_customers",
            "gross_value",
            "total_cost",
            "expected_net_impact",
            "best_next_playbook",
        ]
    )
