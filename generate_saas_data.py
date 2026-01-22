import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()
np.random.seed(42)
random.seed(42)

# -----------------------------
# CONFIG
# -----------------------------
NUM_CUSTOMERS = 10000
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)

segments = ["SMB", "Mid-Market", "Enterprise"]
segment_weights = [0.6, 0.25, 0.15]

plans = {
    "Basic": 29.99,
    "Pro": 59.99,
    "Enterprise": 129.99
}

churn_probability = {
    "SMB": 0.25,
    "Mid-Market": 0.15,
    "Enterprise": 0.07
}

# -----------------------------
# CUSTOMERS
# -----------------------------
print("Generating customers...")
customers = []

for i in range(NUM_CUSTOMERS):
    signup = fake.date_between(START_DATE.date(), END_DATE.date())
    segment = random.choices(segments, segment_weights)[0]

    customers.append({
        "customer_id": f"C{i:06d}",
        "signup_date": signup,
        "segment": segment,
        "country": fake.country_code(),
        "acquisition_channel": random.choice(["Paid Ads", "Referral", "Organic", "Partner"]),
        "is_active": True
    })

customers_df = pd.DataFrame(customers)

# -----------------------------
# SUBSCRIPTIONS
# -----------------------------
print("Generating subscriptions...")
subscriptions = []

for _, row in customers_df.iterrows():
    plan = random.choice(list(plans.keys()))
    signup = pd.to_datetime(row["signup_date"])
    start_date = signup + timedelta(days=random.randint(0, 14))

    churned = np.random.rand() < churn_probability[row["segment"]]
    end_date = None

    if churned:
        churn_months = random.randint(3, 18)
        end_date = start_date + timedelta(days=30 * churn_months)
        # Ensure end_date doesn't exceed END_DATE
        if end_date > END_DATE:
            end_date = END_DATE

    subscriptions.append({
        "subscription_id": f"S{random.randint(100000, 999999)}",
        "customer_id": row["customer_id"],
        "plan_type": plan,
        "start_date": start_date,
        "end_date": end_date,
        "monthly_price": plans[plan]
    })

subscriptions_df = pd.DataFrame(subscriptions)

# -----------------------------
# PAYMENTS
# -----------------------------
print("Generating payments...")
payments = []

for _, sub in subscriptions_df.iterrows():
    start = pd.to_datetime(sub["start_date"])
    end = pd.to_datetime(sub["end_date"]) if pd.notnull(sub["end_date"]) else pd.to_datetime(END_DATE)
    
    # Ensure end doesn't exceed END_DATE
    end_limit = pd.to_datetime(END_DATE)
    if end > end_limit:
        end = end_limit

    payment_date = start

    while payment_date <= end:
        status = "Success" if random.random() > 0.05 else "Failed"

        payments.append({
            "payment_id": f"P{random.randint(1000000, 9999999)}",
            "customer_id": sub["customer_id"],
            "payment_date": payment_date,
            "amount": sub["monthly_price"] if status == "Success" else 0,
            "payment_status": status
        })

        payment_date += timedelta(days=30)

payments_df = pd.DataFrame(payments)

# -----------------------------
# COSTS (WITH SEASONALITY)
# -----------------------------
print("Generating costs...")
months = pd.period_range("2022-01", "2024-12", freq="M")
costs = []

for m in months:
    base_marketing = random.randint(8000, 14000)

    # marketing spike every Q1
    if m.month in [1, 2, 3]:
        base_marketing = int(base_marketing * 1.3)

    costs.append({
        "month": m.strftime("%Y-%m"),
        "infra_cost": random.randint(12000, 20000),
        "marketing_cost": int(base_marketing),
        "support_cost": random.randint(6000, 10000)
    })

costs_df = pd.DataFrame(costs)

# -----------------------------
# UPDATE CUSTOMER ACTIVE STATUS BASED ON SUBSCRIPTIONS
# -----------------------------
print("Updating customer active status...")
active_customers = subscriptions_df[subscriptions_df["end_date"].isna()]["customer_id"].unique()
customers_df["is_active"] = customers_df["customer_id"].isin(active_customers)

# -----------------------------
# SAVE CSVs
# -----------------------------
print("Saving CSV files...")
customers_df.to_csv("customers.csv", index=False)
subscriptions_df.to_csv("subscriptions.csv", index=False)
payments_df.to_csv("payments.csv", index=False)
costs_df.to_csv("costs.csv", index=False)

print("\n[SUCCESS] SaaS dataset generated successfully!")
print(f"Summary:")
print(f"   - Customers: {len(customers_df):,}")
print(f"   - Subscriptions: {len(subscriptions_df):,}")
print(f"   - Payments: {len(payments_df):,}")
print(f"   - Cost records: {len(costs_df)}")
print(f"\nFiles created:")
print(f"   - customers.csv")
print(f"   - subscriptions.csv")
print(f"   - payments.csv")
print(f"   - costs.csv")
