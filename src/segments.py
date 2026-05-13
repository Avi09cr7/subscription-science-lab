from __future__ import annotations

import numpy as np
import pandas as pd

from playbooks import PLAYBOOKS


SEGMENT_KEYS = ["brand", "acquisition_channel", "plan"]


def build_segment_outputs(
    customers: pd.DataFrame,
    action_queue: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if action_queue.empty:
        return empty_segment_opportunities(), empty_segment_issue_matrix()

    base_segments = build_base_segments(customers)
    action_segments = enrich_actions_with_customer_context(customers, action_queue)
    opportunity = build_opportunity_report(base_segments, action_segments)
    issue_matrix = build_issue_matrix(action_segments)
    return opportunity, issue_matrix


def build_base_segments(customers: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        customers.groupby(SEGMENT_KEYS, as_index=False)
        .agg(
            customers=("customer_id", "nunique"),
            monthly_revenue=("monthly_revenue", "sum"),
            avg_risk_score=("churn_risk_score", "mean"),
            churn_rate=("churned", "mean"),
            avg_discount_rate=("discount_rate", "mean"),
            support_tickets_90d=("support_tickets_90d", "sum"),
            late_shipments_90d=("late_shipments_90d", "sum"),
        )
        .round(
            {
                "monthly_revenue": 2,
                "avg_risk_score": 4,
                "churn_rate": 4,
                "avg_discount_rate": 4,
            }
        )
    )
    grouped["segment_name"] = grouped.apply(segment_name, axis=1)
    return grouped


def enrich_actions_with_customer_context(customers: pd.DataFrame, action_queue: pd.DataFrame) -> pd.DataFrame:
    context_columns = [
        "customer_id",
        "brand",
        "acquisition_channel",
        "plan",
        "monthly_revenue",
        "churn_risk_score",
        "risk_segment",
    ]
    return action_queue.drop(columns=["brand"], errors="ignore").merge(
        customers[context_columns],
        on="customer_id",
        how="left",
    )


def build_opportunity_report(base_segments: pd.DataFrame, action_segments: pd.DataFrame) -> pd.DataFrame:
    queue_rollup = (
        action_segments.groupby(SEGMENT_KEYS, as_index=False)
        .agg(
            action_customers=("customer_id", "nunique"),
            expected_value=("expected_value", "sum"),
            avg_action_value=("expected_value", "mean"),
            avg_queue_risk=("churn_risk_score", "mean"),
            critical_or_high=("risk_segment", lambda values: int(values.isin(["high", "critical"]).sum())),
        )
        .round({"expected_value": 2, "avg_action_value": 2, "avg_queue_risk": 4})
    )

    opportunity = base_segments.merge(queue_rollup, on=SEGMENT_KEYS, how="inner")
    opportunity["action_rate"] = opportunity["action_customers"] / opportunity["customers"]
    opportunity["value_per_customer"] = opportunity["expected_value"] / opportunity["customers"]

    dominant = dominant_issue_by_segment(action_segments)
    opportunity = opportunity.merge(dominant, on=SEGMENT_KEYS, how="left")
    opportunity["owner"] = opportunity["dominant_issue"].map(lambda issue: PLAYBOOKS.get(issue, {}).get("owner", "Ops"))
    opportunity["recommended_playbook"] = opportunity["dominant_issue"].map(
        lambda issue: PLAYBOOKS.get(issue, {}).get("playbook", "Review recovery queue")
    )
    opportunity["suggested_action"] = opportunity.apply(suggested_action, axis=1)

    opportunity["priority_score"] = calculate_priority_score(opportunity)
    opportunity = (
        opportunity.sort_values(["priority_score", "expected_value"], ascending=False)
        .reset_index(drop=True)
        .head(12)
    )
    opportunity.insert(0, "rank", opportunity.index + 1)
    return opportunity[
        [
            "rank",
            "segment_name",
            "brand",
            "acquisition_channel",
            "plan",
            "customers",
            "action_customers",
            "action_rate",
            "monthly_revenue",
            "avg_risk_score",
            "expected_value",
            "value_per_customer",
            "dominant_issue",
            "dominant_issue_value",
            "owner",
            "recommended_playbook",
            "priority_score",
            "suggested_action",
        ]
    ].round({"action_rate": 4, "value_per_customer": 2, "dominant_issue_value": 2, "priority_score": 1})


def dominant_issue_by_segment(action_segments: pd.DataFrame) -> pd.DataFrame:
    exploded = explode_segment_issues(action_segments)
    issue_value = (
        exploded.groupby(SEGMENT_KEYS + ["issue_type"], as_index=False)
        .agg(issue_customers=("customer_id", "nunique"), issue_value=("allocated_value", "sum"))
        .sort_values(SEGMENT_KEYS + ["issue_value"], ascending=[True, True, True, False])
    )
    dominant = issue_value.drop_duplicates(SEGMENT_KEYS).rename(
        columns={"issue_type": "dominant_issue", "issue_value": "dominant_issue_value"}
    )
    return dominant[SEGMENT_KEYS + ["dominant_issue", "dominant_issue_value"]]


def build_issue_matrix(action_segments: pd.DataFrame) -> pd.DataFrame:
    exploded = explode_segment_issues(action_segments)
    matrix = (
        exploded.pivot_table(
            index=SEGMENT_KEYS,
            columns="issue_type",
            values="customer_id",
            aggfunc=pd.Series.nunique,
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for issue in PLAYBOOKS:
        if issue not in matrix.columns:
            matrix[issue] = 0

    matrix["segment_name"] = matrix.apply(segment_name, axis=1)
    issue_columns = list(PLAYBOOKS)
    matrix["total_issue_mentions"] = matrix[issue_columns].sum(axis=1)
    matrix = matrix.sort_values("total_issue_mentions", ascending=False).head(12)
    return matrix[["segment_name", *SEGMENT_KEYS, *issue_columns, "total_issue_mentions"]]


def explode_segment_issues(action_segments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in action_segments.itertuples(index=False):
        issues = str(row.issue_type).split(" + ")
        allocated_value = float(row.expected_value) / len(issues)
        for issue in issues:
            rows.append(
                {
                    "customer_id": row.customer_id,
                    "brand": row.brand,
                    "acquisition_channel": row.acquisition_channel,
                    "plan": row.plan,
                    "issue_type": issue,
                    "allocated_value": allocated_value,
                }
            )
    return pd.DataFrame(rows)


def calculate_priority_score(opportunity: pd.DataFrame) -> pd.Series:
    value_score = safe_scale(opportunity["expected_value"])
    risk_score = safe_scale(opportunity["avg_risk_score"])
    density_score = safe_scale(opportunity["action_rate"])
    return 100 * (0.55 * value_score + 0.25 * risk_score + 0.20 * density_score)


def safe_scale(series: pd.Series) -> pd.Series:
    max_value = series.max()
    if max_value == 0 or pd.isna(max_value):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return series / max_value


def suggested_action(row: pd.Series) -> str:
    playbook = PLAYBOOKS.get(row["dominant_issue"], {})
    metric = playbook.get("primary_metric", "segment recovery")
    return f"Run {row['recommended_playbook']} for {row['segment_name']} and track {metric.lower()}."


def segment_name(row: pd.Series) -> str:
    return f"{row['brand']} / {row['acquisition_channel']} / {row['plan']}"


def empty_segment_opportunities() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "rank",
            "segment_name",
            "brand",
            "acquisition_channel",
            "plan",
            "customers",
            "action_customers",
            "action_rate",
            "monthly_revenue",
            "avg_risk_score",
            "expected_value",
            "value_per_customer",
            "dominant_issue",
            "dominant_issue_value",
            "owner",
            "recommended_playbook",
            "priority_score",
            "suggested_action",
        ]
    )


def empty_segment_issue_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "segment_name",
            *SEGMENT_KEYS,
            *PLAYBOOKS.keys(),
            "total_issue_mentions",
        ]
    )
