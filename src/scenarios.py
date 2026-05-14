from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from playbooks import PLAYBOOKS


SCENARIOS = {
    "Lean sprint": {
        "description": "Highest-return work for a constrained ops week.",
        "owner_capacity": {
            "Billing Ops": 6,
            "Operations": 8,
            "Customer Success": 5,
            "Growth": 3,
        },
    },
    "Balanced week": {
        "description": "Practical cross-functional plan with enough capacity to cover most high-value work.",
        "owner_capacity": {
            "Billing Ops": 12,
            "Operations": 18,
            "Customer Success": 12,
            "Growth": 8,
        },
    },
    "Full recovery push": {
        "description": "Maximum available queue coverage using all currently ranked opportunities.",
        "owner_capacity": {
            "Billing Ops": 30,
            "Operations": 45,
            "Customer Success": 30,
            "Growth": 20,
        },
    },
}


def build_scenario_outputs(
    action_queue: pd.DataFrame,
    reports_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    scored_actions = score_actions(action_queue)
    scenario_rows = []
    workload_frames = []
    selected_frames = []

    for scenario_name, config in SCENARIOS.items():
        selected = select_actions(scored_actions, config["owner_capacity"]).copy()
        scenario_rows.append(scenario_summary_row(scenario_name, config["description"], selected))
        workload_frames.append(owner_workload(scenario_name, selected))
        selected["scenario"] = scenario_name
        selected_frames.append(selected)

    scenarios = pd.DataFrame(scenario_rows).sort_values("net_impact", ascending=False).reset_index(drop=True)
    workload = pd.concat(workload_frames, ignore_index=True) if workload_frames else empty_scenario_workload()
    selected_actions = pd.concat(selected_frames, ignore_index=True) if selected_frames else empty_selected_actions()
    best = scenarios.sort_values("net_impact", ascending=False).iloc[0].to_dict() if not scenarios.empty else {}
    summary = {
        "scenario_count": int(len(scenarios)),
        "best_scenario": best,
        "max_net_impact": round(float(scenarios["net_impact"].max()), 2) if not scenarios.empty else 0,
        "max_actions": int(scenarios["selected_actions"].max()) if not scenarios.empty else 0,
    }
    (reports_dir / "scenario_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return scenarios, workload, selected_actions, summary


def score_actions(action_queue: pd.DataFrame) -> pd.DataFrame:
    if action_queue.empty:
        return empty_scored_actions()

    scored = action_queue.copy()
    scored["primary_issue"] = scored["issue_type"].str.split(" + ", regex=False).str[0]
    scored["owner"] = scored["primary_issue"].map(lambda issue: PLAYBOOKS.get(issue, {}).get("owner", "Ops"))
    scored["playbook"] = scored["primary_issue"].map(
        lambda issue: PLAYBOOKS.get(issue, {}).get("playbook", "Review recovery queue")
    )
    scored["cost_per_action"] = scored["primary_issue"].map(
        lambda issue: PLAYBOOKS.get(issue, {}).get("cost_per_action", 5.0)
    )
    scored["expected_save_rate"] = scored["primary_issue"].map(
        lambda issue: PLAYBOOKS.get(issue, {}).get("expected_save_rate", 0.15)
    )
    scored["expected_saved_value"] = scored["expected_value"] * scored["expected_save_rate"]
    scored["net_impact"] = scored["expected_saved_value"] - scored["cost_per_action"]
    scored["roi"] = np.where(scored["cost_per_action"] > 0, scored["expected_saved_value"] / scored["cost_per_action"], 0)
    return scored.sort_values(["net_impact", "expected_value"], ascending=False).reset_index(drop=True)


def select_actions(scored_actions: pd.DataFrame, owner_capacity: dict[str, int]) -> pd.DataFrame:
    selected = []
    for owner, capacity in owner_capacity.items():
        owner_actions = scored_actions[(scored_actions["owner"] == owner) & (scored_actions["net_impact"] > 0)]
        selected.append(owner_actions.head(capacity))
    if not selected:
        return empty_scored_actions()
    return pd.concat(selected, ignore_index=True).sort_values("net_impact", ascending=False).reset_index(drop=True)


def scenario_summary_row(name: str, description: str, selected: pd.DataFrame) -> dict[str, object]:
    selected_actions = int(len(selected))
    expected_saved_value = float(selected["expected_saved_value"].sum()) if selected_actions else 0
    execution_cost = float(selected["cost_per_action"].sum()) if selected_actions else 0
    net_impact = expected_saved_value - execution_cost
    gross_value = float(selected["expected_value"].sum()) if selected_actions else 0
    top_owner = (
        selected.groupby("owner")["net_impact"].sum().sort_values(ascending=False).index[0]
        if selected_actions
        else "None"
    )
    return {
        "scenario": name,
        "description": description,
        "selected_actions": selected_actions,
        "covered_expected_value": round(gross_value, 2),
        "expected_saved_value": round(expected_saved_value, 2),
        "execution_cost": round(execution_cost, 2),
        "net_impact": round(net_impact, 2),
        "roi": round(expected_saved_value / execution_cost, 2) if execution_cost else 0,
        "top_owner": top_owner,
        "recommendation": scenario_recommendation(name, selected_actions, net_impact),
    }


def owner_workload(scenario_name: str, selected: pd.DataFrame) -> pd.DataFrame:
    if selected.empty:
        return empty_scenario_workload()
    workload = (
        selected.groupby(["owner", "playbook"], as_index=False)
        .agg(
            selected_actions=("customer_id", "count"),
            expected_saved_value=("expected_saved_value", "sum"),
            execution_cost=("cost_per_action", "sum"),
            net_impact=("net_impact", "sum"),
        )
        .sort_values("net_impact", ascending=False)
    )
    workload.insert(0, "scenario", scenario_name)
    return workload.round({"expected_saved_value": 2, "execution_cost": 2, "net_impact": 2})


def scenario_recommendation(name: str, selected_actions: int, net_impact: float) -> str:
    if selected_actions == 0:
        return "No positive-return recovery actions are available."
    if name == "Balanced week":
        return "Recommended default plan: meaningful coverage without overloading a single team."
    if net_impact >= 2500:
        return "Use when leadership wants maximum recovery coverage this week."
    return "Use when team capacity is constrained and quick wins matter most."


def empty_scored_actions() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "customer_id",
            "brand",
            "issue_type",
            "expected_value",
            "recommended_action",
            "reason",
            "primary_issue",
            "owner",
            "playbook",
            "cost_per_action",
            "expected_save_rate",
            "expected_saved_value",
            "net_impact",
            "roi",
        ]
    )


def empty_scenario_workload() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "scenario",
            "owner",
            "playbook",
            "selected_actions",
            "expected_saved_value",
            "execution_cost",
            "net_impact",
        ]
    )


def empty_selected_actions() -> pd.DataFrame:
    frame = empty_scored_actions()
    frame["scenario"] = []
    return frame
