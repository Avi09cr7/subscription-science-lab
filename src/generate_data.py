from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


def main() -> None:
    rng = np.random.default_rng(8077674279)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    n_customers = 2600
    brands = np.array(["Northstar Apparel", "Voltix Home", "DermaCo Labs", "VitalEdge Wellness"])
    regions = np.array(["Malaysia", "Singapore", "Thailand", "Indonesia", "Philippines"])
    channels = np.array(["paid_search", "affiliate", "display", "email", "organic"])
    plans = np.array(["monthly", "quarterly", "annual"])
    brand_skus = {
        "Northstar Apparel": ["NA-TEE-01", "NA-DENIM-02", "NA-JACKET-03"],
        "Voltix Home": ["VH-FILTER-01", "VH-BATTERY-02", "VH-CLEAN-03"],
        "DermaCo Labs": ["DL-SERUM-01", "DL-CREAM-02", "DL-CLEANSER-03"],
        "VitalEdge Wellness": ["VW-CAPSULE-01", "VW-PROTEIN-02", "VW-BUNDLE-03"],
    }

    brand = rng.choice(brands, n_customers, p=[0.28, 0.22, 0.24, 0.26])
    region = rng.choice(regions, n_customers, p=[0.26, 0.18, 0.19, 0.22, 0.15])
    channel = rng.choice(channels, n_customers, p=[0.26, 0.18, 0.2, 0.16, 0.2])
    plan = rng.choice(plans, n_customers, p=[0.58, 0.27, 0.15])

    tenure = rng.integers(1, 37, n_customers)
    active_subscriptions = rng.integers(1, 4, n_customers)
    base_revenue = {
        "Northstar Apparel": 52,
        "Voltix Home": 118,
        "DermaCo Labs": 37,
        "VitalEdge Wellness": 64,
    }
    monthly_revenue = np.array([base_revenue[item] for item in brand]) * rng.normal(1.0, 0.22, n_customers)
    monthly_revenue *= np.where(plan == "annual", 1.35, np.where(plan == "quarterly", 1.12, 1.0))
    monthly_revenue = np.clip(monthly_revenue, 12, None).round(2)

    discount_rate = np.clip(rng.beta(2, 8, n_customers) + (channel == "affiliate") * 0.06, 0, 0.55).round(3)
    support_tickets_90d = rng.poisson(0.7 + (brand == "Voltix Home") * 0.35, n_customers)
    late_shipments_90d = rng.poisson(0.45 + (region == "Indonesia") * 0.2, n_customers)
    email_engagement = np.clip(rng.normal(0.52, 0.18, n_customers), 0.02, 0.98).round(3)
    avg_days_between_orders = np.clip(rng.normal(31, 9, n_customers) + (plan == "quarterly") * 20 + (plan == "annual") * 45, 12, 120).round(1)

    churn_logit = (
        -1.45
        - 0.045 * tenure
        + 1.9 * discount_rate
        + 0.33 * support_tickets_90d
        + 0.23 * late_shipments_90d
        - 1.35 * email_engagement
        + 0.012 * avg_days_between_orders
        + (channel == "display") * 0.28
        + (plan == "monthly") * 0.32
        - (plan == "annual") * 0.42
        + (region == "Indonesia") * 0.16
    )
    churn_probability = 1 / (1 + np.exp(-churn_logit))
    churned = rng.binomial(1, churn_probability)

    customers = pd.DataFrame(
        {
            "customer_id": [f"CUST-{idx:05d}" for idx in range(1, n_customers + 1)],
            "brand": brand,
            "region": region,
            "acquisition_channel": channel,
            "plan": plan,
            "tenure_months": tenure,
            "active_subscriptions": active_subscriptions,
            "monthly_revenue": monthly_revenue,
            "discount_rate": discount_rate,
            "support_tickets_90d": support_tickets_90d,
            "late_shipments_90d": late_shipments_90d,
            "email_engagement": email_engagement,
            "avg_days_between_orders": avg_days_between_orders,
            "churned": churned,
        }
    )

    months = pd.date_range("2025-01-01", periods=15, freq="MS")
    rows = []
    for month_index, month in enumerate(months):
        for item in brands:
            trend = 1 + 0.018 * month_index
            seasonality = 1 + 0.08 * np.sin(month_index / 12 * 2 * np.pi)
            customers_count = int(rng.normal(560, 70) * trend)
            arpu = base_revenue[item] * rng.normal(1.0, 0.06) * seasonality
            churn_rate = np.clip(rng.normal(0.13, 0.025) - 0.006 * month_index, 0.04, 0.24)
            rows.append(
                {
                    "month": month.date().isoformat(),
                    "brand": item,
                    "active_customers": customers_count,
                    "subscription_revenue": round(customers_count * arpu, 2),
                    "monthly_churn_rate": round(churn_rate, 4),
                }
            )

    monthly_revenue = pd.DataFrame(rows)

    campaign_rows = []
    for item in brands:
        for channel_name in channels:
            spend = rng.integers(7000, 38000)
            conversions = int(spend / rng.uniform(48, 145))
            revenue = conversions * base_revenue[item] * rng.uniform(1.7, 4.4)
            campaign_rows.append(
                {
                    "brand": item,
                    "acquisition_channel": channel_name,
                    "spend": spend,
                    "conversions": conversions,
                    "attributed_revenue": round(revenue, 2),
                }
            )

    campaigns = pd.DataFrame(campaign_rows)

    decline_reasons = np.array(["expired_card", "insufficient_funds", "soft_decline", "authentication_required", "gateway_issue"])
    payment_rows = []
    for idx, row in customers.iterrows():
        failure_probability = np.clip(
            0.035
            + row["discount_rate"] * 0.08
            + (row["tenure_months"] < 4) * 0.025
            + (row["email_engagement"] < 0.25) * 0.03
            + (row["region"] == "Indonesia") * 0.012,
            0.02,
            0.18,
        )
        failed = rng.random() < failure_probability
        recovered = bool(failed and rng.random() < 0.42)
        retry_count = int(rng.integers(1, 4)) if failed else 0
        days_past_due = int(rng.integers(1, 18)) if failed and not recovered else 0
        payment_rows.append(
            {
                "invoice_id": f"INV-{idx + 1:05d}",
                "customer_id": row["customer_id"],
                "invoice_amount": round(float(row["monthly_revenue"]), 2),
                "payment_status": "recovered" if recovered else ("failed" if failed else "paid"),
                "decline_reason": rng.choice(decline_reasons) if failed else "none",
                "retry_count": retry_count,
                "days_past_due": days_past_due,
            }
        )

    payment_events = pd.DataFrame(payment_rows)

    fulfillment_rows = []
    recent_customers = customers.sample(n=1800, random_state=42)
    for idx, row in recent_customers.reset_index(drop=True).iterrows():
        sku = rng.choice(brand_skus[row["brand"]])
        promised_days = int(rng.choice([2, 3, 4, 5], p=[0.2, 0.35, 0.3, 0.15]))
        delay_pressure = (row["region"] == "Indonesia") * 0.9 + (row["late_shipments_90d"] > 0) * 0.7
        actual_days = max(1, int(round(promised_days + rng.normal(0.4 + delay_pressure, 1.4))))
        late = actual_days > promised_days + 1
        fulfillment_rows.append(
            {
                "order_id": f"ORD-{idx + 1:05d}",
                "customer_id": row["customer_id"],
                "brand": row["brand"],
                "sku": sku,
                "promised_days": promised_days,
                "actual_days": actual_days,
                "late_flag": int(late),
                "fulfillment_status": "late" if late else "on_time",
            }
        )

    fulfillment_events = pd.DataFrame(fulfillment_rows)

    inventory_rows = []
    sku_categories = {
        "NA": "apparel",
        "VH": "home_care",
        "DL": "beauty",
        "VW": "wellness",
    }
    for item in brands:
        for sku in brand_skus[item]:
            forecast_units = int(rng.integers(120, 520))
            on_hand_units = int(max(0, forecast_units * rng.uniform(0.32, 1.55)))
            unit_price = round(float(base_revenue[item] * rng.uniform(0.55, 1.35)), 2)
            margin_rate = round(float(rng.uniform(0.34, 0.68)), 3)
            inventory_rows.append(
                {
                    "sku": sku,
                    "brand": item,
                    "category": sku_categories[sku[:2]],
                    "on_hand_units": on_hand_units,
                    "forecast_30d_units": forecast_units,
                    "unit_price": unit_price,
                    "gross_margin_rate": margin_rate,
                    "supplier_lead_time_days": int(rng.integers(8, 31)),
                }
            )

    sku_inventory = pd.DataFrame(inventory_rows)

    customers.to_csv(RAW_DIR / "customers.csv", index=False)
    monthly_revenue.to_csv(RAW_DIR / "monthly_revenue.csv", index=False)
    campaigns.to_csv(RAW_DIR / "campaigns.csv", index=False)
    payment_events.to_csv(RAW_DIR / "payment_events.csv", index=False)
    fulfillment_events.to_csv(RAW_DIR / "fulfillment_events.csv", index=False)
    sku_inventory.to_csv(RAW_DIR / "sku_inventory.csv", index=False)
    print("Generated raw subscription, revenue, and campaign data.")


if __name__ == "__main__":
    main()
