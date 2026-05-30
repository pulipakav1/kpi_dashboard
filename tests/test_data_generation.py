"""Tests for the synthetic data generator."""

import pandas as pd
import pytest


def test_customers_shape(customers_df: pd.DataFrame):
    assert len(customers_df) == 10_000
    assert {"customer_id", "signup_date", "segment", "is_active"}.issubset(customers_df.columns)


def test_customers_segments(customers_df: pd.DataFrame):
    assert set(customers_df["segment"].unique()) == {"SMB", "Mid-Market", "Enterprise"}


def test_payments_positive_amounts(payments_df: pd.DataFrame):
    assert (payments_df["amount"] > 0).all()


def test_payments_status_values(payments_df: pd.DataFrame):
    assert set(payments_df["payment_status"].unique()).issubset({"Success", "Failed"})


def test_subscriptions_dates(subscriptions_df: pd.DataFrame):
    active = subscriptions_df[subscriptions_df["end_date"].isna()]
    churned = subscriptions_df[subscriptions_df["end_date"].notna()]
    assert len(active) > 0
    assert len(churned) > 0


def test_costs_monthly_records(costs_df: pd.DataFrame):
    assert len(costs_df) == 36
    assert {"infra_cost", "marketing_cost", "support_cost"}.issubset(costs_df.columns)
    assert (costs_df[["infra_cost", "marketing_cost", "support_cost"]] >= 0).all().all()
